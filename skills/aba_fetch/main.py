"""人工登录后抓 ABA 的低风险流程（本地浏览器读取页面信息 v2）。

说明：
- 本版本新增“真实能力”：通过浏览器调试端口读取当前页面信息（标题 / URL）。
- 不自动登录、不处理账号密码、不处理验证码。
- 不做真实 ABA 抓取。
- 不调用真实飞书接口。
"""

from dataclasses import dataclass
import platform
import subprocess
from typing import Any
from urllib.parse import urlparse

import requests


@dataclass
class RuntimeContext:
    """运行时上下文。"""

    browser_open: bool | None = None
    cdp_hosts: tuple[str, ...] = ("127.0.0.1", "localhost")
    cdp_ports: tuple[int, ...] = (9222, 9223)


@dataclass
class CheckResult:
    """统一检查结果结构。"""

    ok: bool
    code: str
    message: str


@dataclass
class BrowserPageInfo:
    """浏览器页面信息。"""

    debugger_address: str
    title: str
    url: str


@dataclass
class PageRecognition:
    """页面识别结果。"""

    is_amazon_page: bool
    is_aba_page: bool
    amazon_reasons: list[str]
    aba_reasons: list[str]


def _log_step(step_no: int, step_total: int, title: str) -> None:
    """输出标准步骤标题。"""
    print(f"\n========== 步骤 {step_no}/{step_total}：{title} ==========")


def _log_result(result: CheckResult) -> None:
    """输出检查结果。"""
    status = "PASS" if result.ok else "FAIL"
    print(f"[{status}] {result.code} - {result.message}")


def _list_running_process_names() -> set[str]:
    """获取当前系统进程名集合（最小真实检查能力）。"""
    system_name = platform.system().lower()
    process_names: set[str] = set()

    if system_name == "windows":
        output = subprocess.check_output(
            ["tasklist", "/FO", "CSV", "/NH"],
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        for raw_line in output.splitlines():
            line = raw_line.strip().strip('"')
            if not line:
                continue
            image_name = line.split('\",\"', 1)[0].strip().lower()
            if image_name:
                process_names.add(image_name)
        return process_names

    output = subprocess.check_output(
        ["ps", "-A", "-o", "comm="],
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    for raw_line in output.splitlines():
        name = raw_line.strip().split("/")[-1].lower()
        if name:
            process_names.add(name)
    return process_names


def check_browser_open(ctx: RuntimeContext) -> CheckResult:
    """检查浏览器是否已打开（最小真实检查）。"""
    _log_step(1, 4, "检查浏览器是否已打开")
    print("当前为真实检查：检测本机浏览器进程（Chrome / Edge）。")

    if ctx.browser_open is not None:
        print("当前使用 RuntimeContext.browser_open 测试覆写结果（仅用于测试/演示）。")
        if ctx.browser_open:
            return CheckResult(True, "BROWSER_OPEN", "检测到浏览器已打开（覆写结果）。")
        return CheckResult(False, "BROWSER_NOT_OPEN", "未检测到浏览器（覆写结果），请先手动打开浏览器。")

    try:
        running_names = _list_running_process_names()
    except Exception as exc:  # noqa: BLE001
        return CheckResult(False, "BROWSER_CHECK_ERROR", f"浏览器进程检查失败：{exc}")

    target_names = {"chrome.exe", "msedge.exe", "chrome", "msedge"}
    hit_names = sorted(name for name in running_names if name in target_names)

    if hit_names:
        return CheckResult(True, "BROWSER_OPEN", f"检测到浏览器进程：{', '.join(hit_names)}。")
    return CheckResult(
        False,
        "BROWSER_NOT_OPEN",
        "未检测到 Chrome/Edge 进程，请先手动打开浏览器后再继续。",
    )


def _pick_page_target(targets: list[dict[str, Any]]) -> dict[str, Any] | None:
    """从 CDP 目标列表中选一个页面目标。"""
    page_targets = [t for t in targets if t.get("type") == "page"]
    if not page_targets:
        return None

    non_blank = [
        t
        for t in page_targets
        if t.get("url")
        and not str(t.get("url", "")).startswith("devtools://")
        and str(t.get("url", "")) != "about:blank"
    ]
    if non_blank:
        return non_blank[0]
    return page_targets[0]


def read_current_page_info(ctx: RuntimeContext) -> tuple[CheckResult, BrowserPageInfo | None]:
    """通过浏览器调试端口读取当前页面标题和 URL。"""
    _log_step(2, 4, "读取当前浏览器页面信息（真实动作）")
    print("当前为真实读取：尝试连接 CDP HTTP 端点 /json/list。")

    timeout_sec = 1.5
    errors: list[str] = []

    for host in ctx.cdp_hosts:
        for port in ctx.cdp_ports:
            base = f"http://{host}:{port}"
            try:
                response = requests.get(f"{base}/json/list", timeout=timeout_sec)
                response.raise_for_status()
                targets = response.json()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{host}:{port} -> {exc}")
                continue

            if not isinstance(targets, list):
                errors.append(f"{host}:{port} -> /json/list 返回结构不是列表")
                continue

            selected = _pick_page_target(targets)
            if not selected:
                errors.append(f"{host}:{port} -> 未发现 page 类型标签页")
                continue

            title = str(selected.get("title") or "(无标题)")
            url = str(selected.get("url") or "(无 URL)")
            page_info = BrowserPageInfo(
                debugger_address=f"{host}:{port}",
                title=title,
                url=url,
            )
            return (
                CheckResult(
                    True,
                    "PAGE_INFO_READ_OK",
                    f"已读取页面信息（{page_info.debugger_address}）: title={title} | url={url}",
                ),
                page_info,
            )

    joined_errors = " ; ".join(errors[-4:]) if errors else "未拿到可用错误信息"
    return (
        CheckResult(
            False,
            "PAGE_INFO_READ_FAILED",
            "无法通过 CDP 读取页面信息。请确认浏览器使用调试端口启动，例如 --remote-debugging-port=9222。"
            f" 最近错误：{joined_errors}",
        ),
        None,
    )


def _parse_domain(url: str) -> str:
    """尽量从 URL 中解析出 domain。"""
    try:
        parsed = urlparse(url)
        return (parsed.netloc or "").lower()
    except Exception:  # noqa: BLE001
        return ""


def recognize_page(page_info: BrowserPageInfo) -> PageRecognition:
    """基于 title / url 识别 Amazon 页面与疑似 ABA 页面。"""
    _log_step(3, 3, "页面识别（基于 title / URL）")

    title_l = page_info.title.lower()
    url_l = page_info.url.lower()
    domain = _parse_domain(page_info.url)

    amazon_reasons: list[str] = []
    aba_reasons: list[str] = []

    amazon_domain_keys = ("amazon.com", "amazon.", "sellercentral.amazon.")
    if any(key in domain for key in amazon_domain_keys):
        amazon_reasons.append(f"URL 域名命中 Amazon 特征：{domain}")
    if "amazon" in title_l:
        amazon_reasons.append(f"title 命中关键词：{page_info.title}")
    if "amazon" in url_l:
        amazon_reasons.append(f"url 命中关键词：{page_info.url}")

    aba_keywords = (
        "aba",
        "brand analytics",
        "brand-analytics",
        "search query performance",
        "search-query-performance",
        "amazon brand analytics",
    )
    for kw in aba_keywords:
        if kw in title_l:
            aba_reasons.append(f"title 命中：{kw}")
        if kw in url_l:
            aba_reasons.append(f"url 命中：{kw}")

    is_amazon_page = len(amazon_reasons) > 0
    is_aba_page = is_amazon_page and len(aba_reasons) > 0

    print("[PAGE_CHECK] 当前是否识别为 Amazon 页面：", "是" if is_amazon_page else "否")
    print("[PAGE_CHECK] 当前是否识别为 ABA 页面：", "是" if is_aba_page else "否")
    print("[PAGE_CHECK] Amazon 判断依据：")
    if amazon_reasons:
        for reason in amazon_reasons:
            print(f"  - {reason}")
    else:
        print("  - 未命中 Amazon 相关 title/url 特征")
    print("[PAGE_CHECK] ABA 判断依据：")
    if aba_reasons:
        for reason in aba_reasons:
            print(f"  - {reason}")
    else:
        print("  - 未命中 ABA 相关 title/url 特征")

    return PageRecognition(
        is_amazon_page=is_amazon_page,
        is_aba_page=is_aba_page,
        amazon_reasons=amazon_reasons,
        aba_reasons=aba_reasons,
    )


def _print_scope_boundary() -> None:
    print("\n[RUNNER] 当前版本边界：")
    print("[RUNNER] 未执行自动登录、账号密码处理、验证码处理。")
    print("[RUNNER] 未执行真实 ABA 抓取、真实点击导出、真实解析、真实飞书写入。")


def parse_export_file_placeholder() -> list[dict]:
    """占位：保留结构，明确不执行真实导出解析。"""
    mock_rows = [
        {"sku": "DEMO-SKU-001", "keyword": "demo keyword", "aba_rank": 1, "note": "placeholder"},
    ]
    return mock_rows


def main() -> None:
    """主流程入口。"""
    print("\n[RUNNER] 启动任务：人工登录后抓 ABA（本地浏览器读取页面信息 + 页面识别 v3）")
    print("[RUNNER] 低风险原则：不自动登录、不处理账号密码/验证码、不做真实抓取。")

    ctx = RuntimeContext()

    browser_result = check_browser_open(ctx)
    _log_result(browser_result)
    if not browser_result.ok:
        print("\n[RUNNER] 任务终止：浏览器未准备好。")
        return

    page_result, page_info = read_current_page_info(ctx)
    _log_result(page_result)
    if not page_result.ok:
        print("\n[RUNNER] 任务终止：无法读取当前页面信息。")
        print("[RUNNER] 提示：请用带调试端口的浏览器启动命令后重试。")
        return

    print("\n[RUNNER] 真实读取结果：")
    print(f"[RUNNER] 调试端点：{page_info.debugger_address}")
    print(f"[RUNNER] 当前页面标题：{page_info.title}")
    print(f"[RUNNER] 当前页面 URL：{page_info.url}")
    recognize_page(page_info)
    parse_export_file_placeholder()
    _print_scope_boundary()

    print("\n[RUNNER] 任务完成：已具备读取浏览器当前页面信息的真实能力。")
    print("[RUNNER] 提示：本版本仍未执行真实导出、真实解析、真实飞书写入。")


if __name__ == "__main__":
    main()
