import subprocess
import sys


def test_placeholder_script_runs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "skills.aba_fetch.main"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "页面状态检查骨架 v1" in result.stdout
    assert "步骤 1/6：检查浏览器是否已打开" in result.stdout
    assert "[PASS] BROWSER_OPEN" in result.stdout
    assert "[PASS] ABA_PAGE_READY" in result.stdout
    assert "未执行真实导出、真实解析、真实飞书写入" in result.stdout
