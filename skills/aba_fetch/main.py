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


def export_aba_data() -> str:
    """第 3 步：模拟导出 ABA 数据。"""
    _log_step(3, 4, "执行导出动作（占位）")
    print("真实流程中：用户在 ABA 页面手动点击导出。")
    print("当前版本：仅返回一个示例导出路径，不做真实导出。")
    mock_file_path = "./mock_exports/aba_export_demo.csv"
    print(f"[PASS] EXPORT_PLACEHOLDER - 导出动作占位完成：{mock_file_path}")
    return mock_file_path


def parse_export_file(file_path: str) -> list[dict]:
    """第 4 步：模拟解析导出文件。"""
    _log_step(4, 4, "解析导出文件（占位）")
    print(f"目标文件：{file_path}")
    print("当前版本：不读取真实文件，只返回示例数据。")
    mock_rows = [
        {"sku": "DEMO-SKU-001", "keyword": "demo keyword", "aba_rank": 1},
    ]
    print(f"[PASS] PARSE_PLACEHOLDER - 解析占位完成，数据条数：{len(mock_rows)}")
    return mock_rows


def main() -> None:
    """主流程入口。"""
    print("\n[RUNNER] 启动任务：人工登录后抓 ABA（本地浏览器读取页面信息 v2）")
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

    export_file = export_aba_data()
    parse_export_file(export_file)

    print("\n[RUNNER] 任务完成：已具备读取浏览器当前页面信息的真实能力。")
    print("[RUNNER] 提示：本版本仍未执行真实导出、真实解析、真实飞书写入。")


if __name__ == "__main__":
    main()
