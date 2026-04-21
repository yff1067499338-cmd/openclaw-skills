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
    assert "当前为真实检查：检测本机浏览器进程（Chrome / Edge）。" in result.stdout
    assert ("[PASS] BROWSER_OPEN" in result.stdout) or ("[FAIL] BROWSER_NOT_OPEN" in result.stdout)

    # 若浏览器未打开，流程应明确终止；若已打开，后续仍是占位流程。
    if "[FAIL] BROWSER_NOT_OPEN" in result.stdout:
        assert "任务终止：浏览器未准备好" in result.stdout
    else:
        assert "[PASS] ABA_PAGE_READY" in result.stdout
        assert "未执行真实导出、真实解析、真实飞书写入" in result.stdout
