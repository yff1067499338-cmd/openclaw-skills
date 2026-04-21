import subprocess
import sys


def test_demo_script_runs_and_has_real_page_read_step() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "skills.aba_fetch.main"],
        capture_output=True,
        text=True,
        check=True,
    )
    output = result.stdout

    assert "本地浏览器读取页面信息 v2" in output
    assert "步骤 1/4：检查浏览器是否已打开" in output
    if "[FAIL] BROWSER_NOT_OPEN" in output:
        assert "任务终止：浏览器未准备好" in output
        return

    assert "[PASS] BROWSER_OPEN" in output
    assert "步骤 2/4：读取当前浏览器页面信息（真实动作）" in output
    assert ("[PASS] PAGE_INFO_READ_OK" in output) or ("[FAIL] PAGE_INFO_READ_FAILED" in output)

    if "[FAIL] PAGE_INFO_READ_FAILED" in output:
        assert "任务终止：无法读取当前页面信息" in output
    else:
        assert "当前页面标题" in output
        assert "当前页面 URL" in output
        assert "未执行真实导出、真实解析、真实飞书写入" in output
