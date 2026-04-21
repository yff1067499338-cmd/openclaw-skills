import subprocess
import sys


def test_placeholder_script_runs() -> None:
    result = subprocess.run(
        [sys.executable, "skills/aba_fetch/main.py"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "ABA fetch skill placeholder" in result.stdout
