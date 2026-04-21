"""人工登录后抓 ABA 的低风险流程骨架（第一版）。

说明：
- 这里只做流程框架，不做真实抓取。
- 不处理账号密码。
- 不处理验证码。
- 不自动登录。
"""


def check_login_status() -> bool:
    """检查是否已经由人工完成登录。"""
    print("[步骤 1] 检查登录状态：请先在浏览器中人工登录。")
    print("[提示] 本程序不会输入账号密码，也不会自动登录。")
    return True


def check_aba_page_ready() -> bool:
    """检查 ABA 页面是否准备好。"""
    print("[步骤 2] 检查 ABA 页面：请确认你已经手动打开 ABA 页面。")
    print("[提示] 页面准备完成后，流程才会继续。")
    return True


def export_aba_data() -> str:
    """导出 ABA 数据（占位）。"""
    print("[步骤 3] 导出 ABA 数据：这里是占位逻辑，暂不执行真实导出。")
    mock_file_path = "./mock_exports/aba_export_demo.csv"
    print(f"[提示] 先返回一个示例文件路径：{mock_file_path}")
    return mock_file_path


def parse_export_file(file_path: str) -> list[dict]:
    """解析导出文件（占位）。"""
    print(f"[步骤 4] 解析导出文件：这里是占位逻辑，暂不解析真实文件 -> {file_path}")
    mock_rows = [
        {"sku": "DEMO-SKU-001", "aba_value": "demo"},
    ]
    print(f"[提示] 返回示例解析结果，共 {len(mock_rows)} 条。")
    return mock_rows


def sync_to_feishu(rows: list[dict]) -> None:
    """同步到飞书（占位）。"""
    print(f"[步骤 5] 同步到飞书：这里是占位逻辑，暂不调用真实飞书接口。")
    print(f"[提示] 准备同步的数据条数：{len(rows)}")


def main() -> None:
    """主流程入口。"""
    print("开始执行：人工登录后抓 ABA（低风险骨架流程）")

    if not check_login_status():
        print("流程结束：未检测到人工登录状态。")
        return

    if not check_aba_page_ready():
        print("流程结束：ABA 页面未准备好。")
        return

    export_file = export_aba_data()
    rows = parse_export_file(export_file)
    sync_to_feishu(rows)

    print("流程结束：骨架流程执行完成（未进行真实抓取）。")


if __name__ == "__main__":
    main()
