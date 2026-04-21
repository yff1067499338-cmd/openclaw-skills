"""人工登录后抓 ABA 的低风险流程（页面状态检查骨架 v1）。

说明：
- 这是一个“接近真实执行器”的本地脚本骨架。
- 本版本只做页面状态检查骨架与后续流程占位。
- 不做真实 ABA 抓取。
- 不处理账号密码、验证码或自动登录。
- 不调用真实飞书接口。
"""

from dataclasses import dataclass
import platform
import subprocess


@dataclass
class RuntimeContext:
    """运行时上下文。后续可替换为真实浏览器状态对象。"""

    browser_open: bool | None = None
    is_amazon_page: bool = True
    aba_page_ready: bool = True


@dataclass
class CheckResult:
    """统一检查结果结构。"""

    ok: bool
    code: str
    message: str


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
        # Windows 优先：使用 tasklist，兼容 PowerShell / CMD。
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
            image_name = line.split('","', 1)[0].strip().lower()
            if image_name:
                process_names.add(image_name)
        return process_names

    # 非 Windows 环境：使用 ps，方便本地开发和 CI 自测。
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
    _log_step(1, 6, "检查浏览器是否已打开")
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


def check_amazon_page(ctx: RuntimeContext) -> CheckResult:
    """检查是否位于 Amazon 相关页面（占位实现）。"""
    _log_step(2, 6, "检查当前是否在 Amazon 页面")
    print("当前为占位检查：默认从 RuntimeContext 读取 is_amazon_page。")
    if ctx.is_amazon_page:
        return CheckResult(True, "AMAZON_PAGE_OK", "当前页面看起来属于 Amazon 站点。")
    return CheckResult(False, "AMAZON_PAGE_MISMATCH", "当前页面不是 Amazon，请手动切换。")


def check_aba_page_ready(ctx: RuntimeContext) -> CheckResult:
    """检查是否大致位于 ABA 页面且可继续（占位实现）。"""
    _log_step(3, 6, "检查 ABA 页面是否已基本就绪")
    print("当前为占位检查：默认从 RuntimeContext 读取 aba_page_ready。")
    if ctx.aba_page_ready:
        return CheckResult(True, "ABA_PAGE_READY", "ABA 页面已就绪，可进入后续动作。")
    return CheckResult(False, "ABA_PAGE_NOT_READY", "未检测到 ABA 页面可用状态，请手动检查加载情况。")


def export_aba_data() -> str:
    """第 4 步：模拟导出 ABA 数据。"""
    _log_step(4, 6, "执行导出动作（占位）")
    print("真实流程中：用户在 ABA 页面手动点击导出。")
    print("当前版本：仅返回一个示例导出路径，不做真实导出。")
    mock_file_path = "./mock_exports/aba_export_demo.csv"
    print(f"[PASS] EXPORT_PLACEHOLDER - 导出动作占位完成：{mock_file_path}")
    return mock_file_path


def parse_export_file(file_path: str) -> list[dict]:
    """第 5 步：模拟解析导出文件。"""
    _log_step(5, 6, "解析导出文件（占位）")
    print(f"目标文件：{file_path}")
    print("当前版本：不读取真实文件，只返回示例数据。")
    mock_rows = [
        {"sku": "DEMO-SKU-001", "keyword": "demo keyword", "aba_rank": 1},
    ]
    print(f"[PASS] PARSE_PLACEHOLDER - 解析占位完成，数据条数：{len(mock_rows)}")
    return mock_rows


def sync_to_feishu(rows: list[dict]) -> None:
    """第 6 步：模拟写入飞书。"""
    _log_step(6, 6, "写入飞书（占位）")
    print("真实流程中：会调用飞书 API 写入多维表格。")
    print("当前版本：不请求飞书接口，只输出计划写入条数。")
    print(f"[PASS] FEISHU_PLACEHOLDER - 计划写入 {len(rows)} 条数据。")


def main() -> None:
    """主流程入口。"""
    print("\n[RUNNER] 启动任务：人工登录后抓 ABA（页面状态检查骨架 v1）")
    print("[RUNNER] 低风险原则：不自动登录、不处理账号密码/验证码、不做真实抓取。")

    # 当前仅保留页面语义检查占位字段；浏览器开启状态默认走真实进程检查。
    ctx = RuntimeContext()

    browser_result = check_browser_open(ctx)
    _log_result(browser_result)
    if not browser_result.ok:
        print("\n[RUNNER] 任务终止：浏览器未准备好。")
        return

    amazon_result = check_amazon_page(ctx)
    _log_result(amazon_result)
    if not amazon_result.ok:
        print("\n[RUNNER] 任务终止：页面不是 Amazon。")
        return

    aba_result = check_aba_page_ready(ctx)
    _log_result(aba_result)
    if not aba_result.ok:
        print("\n[RUNNER] 任务终止：ABA 页面未就绪。")
        return

    export_file = export_aba_data()
    rows = parse_export_file(export_file)
    sync_to_feishu(rows)

    print("\n[RUNNER] 任务完成：页面状态检查骨架与占位流程执行完成。")
    print("[RUNNER] 提示：本版本未执行真实导出、真实解析、真实飞书写入。")


if __name__ == "__main__":
    main()
