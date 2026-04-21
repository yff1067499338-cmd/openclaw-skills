import subprocess
import sys


def test_placeholder_script_runs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "skills.aba_fetch.main"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "第一版可运行演示优化" in result.stdout
    assert "第 5 步 / 共 5 步：模拟写入飞书" in result.stdout
    assert "未进行真实抓取、真实解析、真实飞书写入" in result.stdout
