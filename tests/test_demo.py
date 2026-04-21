import subprocess
import sys


def test_placeholder_script_runs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "skills.aba_fetch.main"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "人工登录后抓 ABA（低风险骨架流程）" in result.stdout
    assert "未进行真实抓取" in result.stdout
