#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章采集 → Obsidian (v3.0)
=====================================
全程 Selenium 模式，模拟真人浏览器操作，不触发限频
扫码登录后自动切换无头模式，不影响你操作电脑

使用方式：
  1. pip install selenium requests beautifulsoup4 lxml
  2. python wechat_to_obsidian.py
"""

import json
import os
import re
import sys
import time
import random
import logging
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ─────────────────────────── 配置 ───────────────────────────

CONFIG_FILE = "wechat_obsidian_config.json"
DEFAULT_VAULT_PATH = r"C:\Users\1\Documents\Obsidian Vault"
SAVE_SUBDIR = "微信采集"

# ─────────────────────────── 日志 ───────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("wechat_scraper.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("wechat")


# ─────────────────────────── 工具函数 ───────────────────────────


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|\n\r\t]', "_", name)
    name = re.sub(r"_+", "_", name).strip("_. ")
    return name[:200] if name else "untitled"


def random_sleep(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))


def load_config() -> dict:
    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_vault_path(config: dict) -> str:
    vault_path = config.get("obsidian_vault_path", "")
    if vault_path and Path(vault_path).exists():
        return vault_path
    if Path(DEFAULT_VAULT_PATH).exists():
        config["obsidian_vault_path"] = DEFAULT_VAULT_PATH
        save_config(config)
        return DEFAULT_VAULT_PATH
    print("\n请设置 Obsidian vault 路径")
    print("打开 Obsidian → 设置(齿轮) → 关于 → 库路径")
    while True:
        vault_path = input("请输入路径: ").strip().strip('"')
        if Path(vault_path).exists():
            config["obsidian_vault_path"] = vault_path
            save_config(config)
            return vault_path
        print(f"路径不存在: {vault_path}")


# ─────────────────────────── 浏览器 ───────────────────────────


def create_driver(headless=False):
    options = ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    # 修改点：合并 excludeSwitches，避免覆盖
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--log-level=3")

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
    else:
        options.add_argument("--start-maximized")

    try:
        # 修改点：使用 Service 和 Webdriver Manager 自动管理驱动
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        logger.error(f"启动 Chrome 失败: {e}")
        print("请确保已安装 Chrome 浏览器")
        sys.exit(1)

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"},
    )
    return driver


# ─────────────────────────── 登录 & 无头切换 ───────────────────────────


class WeChatSession:
    def __init__(self):
        self.cookies = {}
        self.token = ""
        self.user_agent = ""
        self.driver = None

    def login(self) -> bool:
        """启动浏览器 → 扫码登录 → 最小化窗口继续使用"""
        logger.info("启动浏览器，请扫码登录...")
        self.driver = create_driver(headless=False)
        self.driver.get("https://mp.weixin.qq.com/")

        print("\n" + "=" * 50)
        print("  请在弹出的浏览器中 扫码登录 微信公众平台")
        print("  登录成功后浏览器会自动最小化到后台")
        print("=" * 50 + "\n")

        try:
            WebDriverWait(self.driver, 180).until(
                lambda d: "token=" in d.current_url or "/cgi-bin/home" in d.current_url
            )
        except TimeoutException:
            logger.error("登录超时（3分钟）")
            self.driver.quit()
            self.driver = None
            return False

        logger.info("✓ 登录成功！")
        time.sleep(3)

        # 提取凭证
        current_url = self.driver.current_url
        if "token=" not in current_url:
            self.driver.get("https://mp.weixin.qq.com/")
            time.sleep(3)
            current_url = self.driver.current_url

        token_match = re.search(r"token=(\d+)", current_url)
        if not token_match:
            logger.error("无法提取 Token")
            self.driver.quit()
            self.driver = None
            return False

        self.token = token_match.group(1)
        self.cookies = {c["name"]: c["value"] for c in self.driver.get_cookies()}
        self.user_agent = self.driver.execute_script("return navigator.userAgent")

        logger.info(f"✓ Token: {self.token}, Cookie: {len(self.cookies)} 个")

        # 最小化浏览器窗口，不影响你操作电脑
        self.driver.minimize_window()
        logger.info("✓ 浏览器已最小化到后台，开始采集")
        return True

    def get_requests_session(self) -> requests.Session:
        """仅用于获取文章正文（公开页面）"""
        session = requests.Session()
        session.trust_env = False
        session.proxies = {"http": None, "https": None}
        session.headers.update({
            "User-Agent": self.user_agent,
            "Referer": "https://mp.weixin.qq.com/",
        })
        for name, value in self.cookies.items():
            session.cookies.set(name, value)
        return session

    def close(self):
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")


# ─────────────────────────── HTML → Markdown ───────────────────────────


def html_to_markdown(element) -> str:
    lines = []
    _walk(element, lines)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _walk(node, lines):
    for child in node.children:
        if isinstance(child, NavigableString):
            text = child.strip()
            if text:
                lines.append(text)
            continue
        if not isinstance(child, Tag):
            continue
        tag = child.name.lower()

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = child.get_text(strip=True)
            if text:
                lines.append(f"\n{'#' * int(tag[1])} {text}\n")
            continue
        if tag == "p":
            text = child.get_text(strip=True)
            if text:
                lines.append(f"\n{text}\n")
            continue
        if tag == "img":
            src = child.get("data-src") or child.get("src") or ""
            alt = child.get("alt", "")
            if src:
                lines.append(f"\n![{alt}]({src})\n")
            continue
        if tag in ("strong", "b"):
            text = child.get_text(strip=True)
            if text:
                lines.append(f"**{text}**")
            continue
        if tag in ("em", "i"):
            text = child.get_text(strip=True)
            if text:
                lines.append(f"*{text}*")
            continue
        if tag == "a":
            href = child.get("href", "")
            text = child.get_text(strip=True)
            if href and text:
                lines.append(f"[{text}]({href})")
            elif text:
                lines.append(text)
            continue
        if tag in ("ul", "ol"):
            lines.append("")
            for i, li in enumerate(child.find_all("li", recursive=False)):
                prefix = f"{i + 1}." if tag == "ol" else "-"
                text = li.get_text(strip=True)
                if text:
                    lines.append(f"{prefix} {text}")
            lines.append("")
            continue
        if tag == "blockquote":
            text = child.get_text(strip=True)
            if text:
                lines.append(f"\n> {text}\n")
            continue
        if tag == "pre":
            code = child.get_text()
            lines.append(f"\n```\n{code}\n```\n")
            continue
        if tag == "hr":
            lines.append("\n---\n")
            continue
        _walk(child, lines)


# ─────────────────────────── 采集器（真实页面操作） ───────────────────────────


class WeChatCollector:
    """
    完全模拟真人在页面上的操作：
    1. 进入图文编辑页
    2. 点击"超链接"按钮
    3. 点"选择其他账号"
    4. 输入公众号名称，回车搜索
    5. 从页面 DOM 中提取文章列表（标题、链接、日期）
    6. 翻页继续
    """

    def __init__(self, driver, token: str):
        self.driver = driver
        self.token = token

    def _go_to_editor(self):
        """进入图文编辑页面"""
        logger.info("进入图文编辑页面...")
        self.driver.get(
            f"https://mp.weixin.qq.com/cgi-bin/appmsg"
            f"?t=media/appmsg_edit_v2&action=edit&type=77"
            f"&token={self.token}&lang=zh_CN"
        )
        random_sleep(3, 5)

    def _click_hyperlink_button(self):
        """点击工具栏的'超链接'按钮"""
        try:
            link_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#js_editor_insertlink"))
            )
            link_btn.click()
            random_sleep(1, 2)
            logger.info("✓ 点击超链接按钮")
            return True
        except Exception as e:
            logger.error(f"点击超链接按钮失败: {e}")
            return False

    def _click_other_account(self):
        """点击'选择其他账号'按钮"""
        try:
            # 等待弹窗加载完成
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".weui-desktop-link-dialog"))
            )
            random_sleep(1, 2)

            # 精确定位：弹窗内 .weui-desktop-link-btn 里的 button
            btn = self.driver.find_element(
                By.CSS_SELECTOR,
                ".weui-desktop-link-dialog .weui-desktop-link-btn button"
            )
            if btn and btn.is_displayed():
                btn.click()
                random_sleep(2, 3)
                logger.info("✓ 点击选择其他账号")
                return True

            logger.info("'选择其他账号'按钮不可见，可能已在搜索界面")
            return True
        except NoSuchElementException:
            logger.info("未找到'选择其他账号'按钮，可能已在搜索界面")
            return True
        except Exception as e:
            logger.warning(f"点击选择其他账号异常: {e}")
            return True

    def _search_in_page(self, account_name: str) -> bool:
        """在搜索框输入公众号名称并回车"""
        try:
            # 搜索框在 .inner_link_account_area 里，placeholder 包含"账号名称或微信号"
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    ".inner_link_account_area input.weui-desktop-form__input"
                ))
            )

            # 确保搜索框可见可交互
            if not search_input.is_displayed():
                # 可能还有别的搜索框，用 placeholder 精确匹配
                inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".weui-desktop-link-dialog input.weui-desktop-form__input"
                )
                for inp in inputs:
                    ph = inp.get_attribute("placeholder") or ""
                    if "账号名称" in ph or "微信号" in ph:
                        search_input = inp
                        break

            search_input.clear()
            random_sleep(0.5, 1)

            # 模拟真人打字
            for char in account_name:
                search_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            random_sleep(0.5, 1)
            search_input.send_keys(Keys.RETURN)
            logger.info(f"✓ 输入并搜索: {account_name}")
            random_sleep(3, 5)
            return True
        except Exception as e:
            logger.error(f"搜索输入失败: {e}")
            return False

    def _select_account_from_page(self) -> str | None:
        """从搜索结果中选择公众号，返回公众号名称"""
        try:
            random_sleep(2, 3)
            # 等待搜索结果出现
            results = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((
                    By.CSS_SELECTOR,
                    ".inner_link_account_item, .account_item"
                ))
            )

            if not results:
                logger.warning("未找到搜索结果")
                return None

            # 点第一个结果
            results[0].click()
            random_sleep(2, 3)
            logger.info("✓ 选择了第一个公众号")
            return "selected"
        except Exception as e:
            logger.debug(f"选择账号时异常: {e}")
            # 可能搜索结果格式不同，继续尝试
            return "selected"

    def _extract_articles_from_page(self) -> list[dict]:
        """从当前页面的 DOM 中提取文章列表"""
        articles = []
        try:
            items = self.driver.find_elements(
                By.CSS_SELECTOR, ".inner_link_article_item, .weui-desktop-vm_primary"
            )
            for item in items:
                try:
                    # 标题
                    title_el = item.find_element(By.CSS_SELECTOR, ".inner_link_article_span")
                    title = title_el.text.strip()

                    # 日期
                    date_el = item.find_element(By.CSS_SELECTOR, ".inner_link_article_date span")
                    date_str = date_el.text.strip()

                    # 链接
                    url = ""
                    try:
                        link_el = item.find_element(By.CSS_SELECTOR, "a[href*='mp.weixin.qq.com']")
                        url = link_el.get_attribute("href") or ""
                    except NoSuchElementException:
                        pass

                    # 付费标记
                    is_paid = False
                    try:
                        item.find_element(By.CSS_SELECTOR, ".weui-desktop-key-tag_pay")
                        is_paid = True
                    except NoSuchElementException:
                        pass

                    if title:
                        articles.append({
                            "title": title,
                            "url": url,
                            "date_str": date_str,
                            "is_paid": is_paid,
                        })
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"提取文章异常: {e}")

        return articles

    def _click_next_page(self) -> bool:
        """点击下一页"""
        try:
            next_btns = self.driver.find_elements(By.CSS_SELECTOR, "a.weui-desktop-btn__nav__next, .pagination__next, [class*='next']")
            for btn in next_btns:
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
                    random_sleep(2, 4)
                    return True

            # 尝试通过文字找
            all_btns = self.driver.find_elements(By.CSS_SELECTOR, "a, button")
            for btn in all_btns:
                text = btn.text.strip()
                if text in ("下一页", "›", ">", "»"):
                    if btn.is_displayed():
                        btn.click()
                        random_sleep(2, 4)
                        return True

            return False
        except Exception:
            return False

    def search_account(self, account_name: str) -> dict | None:
        """
        完整的搜索流程：
        进入编辑页 → 点超链接 → 选其他账号 → 输入搜索 → 选择账号
        如果页面操作失败，回退到 XHR 方式
        """
        logger.info(f"搜索公众号: {account_name}")

        self._go_to_editor()

        if not self._click_hyperlink_button():
            return self._search_via_xhr(account_name)

        self._click_other_account()

        if not self._search_in_page(account_name):
            return self._search_via_xhr(account_name)

        self._select_account_from_page()

        # 提取当前公众号信息（从页面上看到的）
        # 返回一个标记，让 get_article_list 知道可以从页面提取文章
        return {"nickname": account_name, "fakeid": None, "_page_mode": True}

    def _search_via_xhr(self, account_name: str) -> dict | None:
        """XHR 兜底搜索"""
        logger.info("页面操作失败，使用 XHR 搜索...")
        try:
            self.driver.set_script_timeout(30)
            result = self.driver.execute_async_script(f"""
                var callback = arguments[arguments.length - 1];
                var xhr = new XMLHttpRequest();
                xhr.open('GET', '/cgi-bin/searchbiz?action=search_biz&begin=0&count=5&query={account_name}&token={self.token}&lang=zh_CN&f=json&ajax=1');
                xhr.onload = function() {{ callback(xhr.responseText); }};
                xhr.onerror = function() {{ callback('{{"_xhr_error":true}}'); }};
                xhr.send();
            """)
            data = json.loads(result)
            if data.get("_xhr_error") or data.get("base_resp", {}).get("ret") != 0:
                return None
            biz_list = data.get("list", [])
            if not biz_list:
                return None

            print(f"\n搜索结果（共 {len(biz_list)} 个）:")
            for i, biz in enumerate(biz_list):
                print(f"  [{i + 1}] {biz.get('nickname', '?')}  (微信号: {biz.get('alias', '无')})")
            if len(biz_list) == 1:
                target = biz_list[0]
                print(f"  → 自动选择: {target.get('nickname')}")
            else:
                while True:
                    choice = input(f"\n选择公众号 [1-{len(biz_list)}]: ").strip()
                    if choice.isdigit() and 1 <= int(choice) <= len(biz_list):
                        target = biz_list[int(choice) - 1]
                        break
            return target
        except Exception as e:
            logger.error(f"XHR 搜索失败: {e}")
            return None

    def get_article_list(
        self, fakeid: str, max_count: int = 9999, date_limit: datetime = None,
        page_mode: bool = False
    ) -> list[dict]:
        """
        获取文章列表：
        - page_mode=True: 从页面 DOM 提取 + 翻页（完全模拟真人）
        - page_mode=False: 用 XHR（兜底）
        """
        if page_mode:
            return self._get_articles_by_page(max_count, date_limit)
        else:
            return self._get_articles_by_xhr(fakeid, max_count, date_limit)

    def _get_articles_by_page(self, max_count: int, date_limit: datetime = None) -> list[dict]:
        """通过翻页从 DOM 提取文章（完全模拟真人操作）"""
        all_articles = []
        page = 1

        if date_limit:
            logger.info(f"从页面采集 {date_limit.strftime('%Y-%m-%d')} 之后的文章...")
        else:
            logger.info(f"从页面采集文章（最多 {max_count} 篇）...")

        while len(all_articles) < max_count:
            logger.info(f"  正在读取第 {page} 页...")
            random_sleep(2, 4)

            page_articles = self._extract_articles_from_page()
            if not page_articles:
                logger.info("  当前页无文章，采集结束")
                break

            reached_limit = False
            for art in page_articles:
                if len(all_articles) >= max_count:
                    break

                # 付费跳过
                if art.get("is_paid"):
                    logger.info(f"  [跳过·付费] {art['title']}")
                    continue

                # 日期检查
                if date_limit and art.get("date_str"):
                    try:
                        art_date = datetime.strptime(art["date_str"], "%Y-%m-%d")
                        if art_date < date_limit:
                            logger.info(f"  ✓ 已到日期限制 {date_limit.strftime('%Y-%m-%d')}，停止")
                            reached_limit = True
                            break
                    except ValueError:
                        pass

                all_articles.append({
                    "title": art["title"],
                    "url": art["url"],
                    "date_str": art.get("date_str", ""),
                    "create_time": 0,
                    "cover": "",
                })

            # 显示当前进度
            last_date = page_articles[-1].get("date_str", "?") if page_articles else "?"
            logger.info(f"  第 {page} 页完成，收录 {len(all_articles)} 篇，当前到 {last_date}")

            if reached_limit:
                break

            # 翻页
            if not self._click_next_page():
                logger.info("  没有更多页了")
                break

            page += 1

        logger.info(f"✓ 共获取 {len(all_articles)} 篇免费文章")
        return all_articles

    def _get_articles_by_xhr(self, fakeid: str, max_count: int, date_limit: datetime = None) -> list[dict]:
        """XHR 兜底方式获取文章列表"""
        articles = []
        begin = 0
        rate_limit_count = 0

        if date_limit:
            logger.info(f"[XHR] 获取 {date_limit.strftime('%Y-%m-%d')} 之后的文章...")
        else:
            logger.info(f"[XHR] 获取文章列表（最多 {max_count} 篇）...")

        while begin < max_count:
            if begin > 0:
                random_sleep(8, 15)

            try:
                self.driver.set_script_timeout(30)
                result = self.driver.execute_async_script(f"""
                    var callback = arguments[arguments.length - 1];
                    var xhr = new XMLHttpRequest();
                    xhr.open('GET', '/cgi-bin/appmsg?action=list_ex&begin={begin}&count=5&fakeid={fakeid}&type=9&query=&token={self.token}&lang=zh_CN&f=json&ajax=1');
                    xhr.onload = function() {{ callback(xhr.responseText); }};
                    xhr.onerror = function() {{ callback('{{"_xhr_error":true}}'); }};
                    xhr.send();
                """)
                data = json.loads(result)
                if data.get("_xhr_error"):
                    break

                ret = data.get("base_resp", {}).get("ret")
                if ret != 0:
                    if ret == 200013:
                        rate_limit_count += 1
                        wait_times = [30, 60, 120, 300]
                        if rate_limit_count > len(wait_times):
                            break
                        wait = wait_times[rate_limit_count - 1]
                        logger.warning(f"[XHR] 频率限制（第{rate_limit_count}次），等 {wait} 秒...")
                        time.sleep(wait)
                        continue
                    break

                rate_limit_count = 0
                app_msg_list = data.get("app_msg_list", [])
                if not app_msg_list:
                    break

                reached = False
                for item in app_msg_list:
                    ct = item.get("create_time", 0)
                    if date_limit and ct and datetime.fromtimestamp(ct) < date_limit:
                        reached = True
                        break
                    pay = item.get("pay_type", 0)
                    ist = item.get("item_show_type", 0)
                    if (pay and pay != 0) or ist == 12:
                        continue
                    articles.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "create_time": ct,
                        "date_str": datetime.fromtimestamp(ct).strftime("%Y-%m-%d") if ct else "",
                        "cover": item.get("cover", ""),
                    })

                if reached:
                    break

                lt = app_msg_list[-1].get("create_time", 0)
                ds = datetime.fromtimestamp(lt).strftime("%Y-%m-%d") if lt else "?"
                begin += len(app_msg_list)
                logger.info(f"  [XHR] 已扫描 {begin} 篇，收录 {len(articles)} 篇，当前到 {ds}")

            except Exception as e:
                logger.error(f"[XHR] 异常: {e}")
                break

        logger.info(f"✓ 共获取 {len(articles)} 篇免费文章")
        return articles


# ─────────────────────────── 文章解析 ───────────────────────────


class ArticleParser:
    """解析单篇文章正文，优先 requests（文章页是公开的），失败用 Selenium"""

    def __init__(self, session: requests.Session, driver=None):
        self.session = session
        self.driver = driver

    def parse(self, url: str) -> dict | None:
        html = self._fetch_html(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "lxml")
        data = {"url": url}

        tag = soup.find("h1", id="activity-name") or soup.find("h1", class_="rich_media_title") or soup.find("h1")
        data["title"] = tag.get_text(strip=True) if tag else "无标题"

        tag = soup.find("span", class_="rich_media_meta_text")
        data["author"] = tag.get_text(strip=True) if tag else ""

        tag = soup.find("a", id="js_name") or soup.find("strong", class_="profile_nickname")
        data["account_name"] = tag.get_text(strip=True) if tag else ""

        m = re.search(r'var\s+ct\s*=\s*"(\d+)"', html)
        if m:
            data["publish_time"] = datetime.fromtimestamp(int(m.group(1))).strftime("%Y-%m-%d")
        else:
            tag = soup.find("em", id="publish_time")
            data["publish_time"] = tag.get_text(strip=True) if tag else ""

        content = soup.find("div", id="js_content") or soup.find("div", class_="rich_media_content")
        data["content_md"] = html_to_markdown(content) if content else "> ⚠️ 未能提取正文"

        return data

    def _fetch_html(self, url: str) -> str | None:
        # 方式一：requests（文章是公开的，一般没问题）
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            return resp.text
        except Exception:
            pass

        # 方式二：Selenium 兜底
        if self.driver:
            try:
                self.driver.get(url)
                time.sleep(3)
                return self.driver.page_source
            except Exception as e:
                logger.error(f"获取文章失败: {e}")

        return None


# ─────────────────────────── Obsidian 保存 ───────────────────────────


def save_to_obsidian(data: dict, account_name: str, vault_path: str) -> Path | None:
    save_dir = Path(vault_path) / SAVE_SUBDIR / sanitize_filename(account_name)
    save_dir.mkdir(parents=True, exist_ok=True)

    title = data.get("title", "无标题")
    filepath = save_dir / (sanitize_filename(title) + ".md")

    if filepath.exists():
        return filepath

    source = data.get("account_name", account_name)
    md = f"""---
title: "{title}"
source: "{source}"
author: "{data.get('author', '')}"
date: {data.get('publish_time', '')}
url: "{data.get('url', '')}"
tags:
  - 微信公众号
  - {sanitize_filename(source)}
created: {datetime.now().strftime("%Y-%m-%d %H:%M")}
---

# {title}

> 来源：**{source}**  |  作者：{data.get('author', '')}  |  日期：{data.get('publish_time', '')}
> [查看原文]({data.get('url', '')})

---

{data.get('content_md', '')}
"""
    filepath.write_text(md, encoding="utf-8")
    return filepath


# ─────────────────────────── 主流程 ───────────────────────────


def main():
    print("""
╔═══════════════════════════════════════════════════╗
║   微信公众号文章采集 → Obsidian  v3.0             ║
║   全 Selenium 模式，模拟真人操作                  ║
║   扫码后浏览器自动最小化，不影响你操作电脑        ║
╚═══════════════════════════════════════════════════╝
    """)

    config = load_config()
    vault_path = get_vault_path(config)
    print(f"Obsidian vault: {vault_path}")
    print(f"保存目录: {Path(vault_path) / SAVE_SUBDIR}\n")

    wechat = WeChatSession()
    try:
        if not wechat.login():
            print("登录失败，请重试")
            return

        session = wechat.get_requests_session()
        collector = WeChatCollector(wechat.driver, wechat.token)
        parser = ArticleParser(session, driver=wechat.driver)

        while True:
            print("\n" + "-" * 45)
            account_name = input("输入公众号名称（输入 q 退出）: ").strip()
            if account_name.lower() == "q":
                break
            if not account_name:
                continue

            # 搜索
            random_sleep(2, 4)
            account = collector.search_account(account_name)
            if not account:
                print("未找到该公众号")
                continue

            nickname = account.get("nickname", account_name)
            fakeid = account.get("fakeid")
            page_mode = account.get("_page_mode", False)

            # 采集范围
            print("\n采集范围设置:")
            print("  直接回车 = 采集全部")
            print("  输入数字 = 采集指定篇数（如 20）")
            print("  输入日期 = 采集该日期之后的文章（如 2025-01-01）")
            range_input = input("请输入: ").strip()

            max_count = 9999
            date_limit = None

            if not range_input or range_input.lower() == "all":
                pass
            elif range_input.isdigit():
                max_count = int(range_input)
            else:
                try:
                    date_limit = datetime.strptime(range_input, "%Y-%m-%d")
                    logger.info(f"将采集 {range_input} 之后的文章")
                except ValueError:
                    print(f"无法识别: {range_input}，将采集全部")

            # 获取文章列表
            logger.info("等待几秒后开始...")
            random_sleep(3, 6)
            articles = collector.get_article_list(fakeid, max_count, date_limit, page_mode=page_mode)

            if not articles:
                print("未获取到文章")
                continue

            # 逐篇解析保存
            print(f"\n开始解析 {len(articles)} 篇文章...\n")
            success = 0
            skipped = 0

            for i, art in enumerate(articles, 1):
                title = art["title"]
                check_path = (
                    Path(vault_path) / SAVE_SUBDIR
                    / sanitize_filename(nickname)
                    / (sanitize_filename(title) + ".md")
                )
                if check_path.exists():
                    logger.info(f"[{i}/{len(articles)}] [已存在] {title}")
                    skipped += 1
                    continue

                logger.info(f"[{i}/{len(articles)}] 解析: {title}")
                parsed = parser.parse(art["url"])
                if not parsed:
                    logger.warning(f"  ✗ 解析失败")
                    continue

                saved = save_to_obsidian(parsed, nickname, vault_path)
                if saved:
                    logger.info(f"  ✓ → {saved.name}")
                    success += 1

                if i < len(articles):
                    random_sleep(2, 4)

            print(f"\n{'=' * 45}")
            print(f"  采集完成！公众号: {nickname}")
            print(f"  保存: {success} 篇  |  跳过: {skipped} 篇")
            print(f"  位置: {Path(vault_path) / SAVE_SUBDIR / sanitize_filename(nickname)}")
            print(f"{'=' * 45}")

            cont = input("\n继续采集其他公众号？(y/n): ").strip().lower()
            if cont != "y":
                break

    finally:
        wechat.close()
        print("\n再见！")


if __name__ == "__main__":
    main()
