import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _venv_python(root: Path) -> Path | None:
    p = root / ".venv" / "Scripts" / "python.exe"
    return p if p.exists() else None


def main() -> int:
    root = _repo_root()
    os.chdir(root)

    python_exe = _venv_python(root)
    cmd = [str(python_exe or sys.executable), "-m", "app.main"]
    try:
        completed = subprocess.run(cmd)
        return int(completed.returncode or 0)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    code = main()
    if "--no-pause" not in sys.argv:
        try:
            input("Press Enter to continue...")
        except EOFError:
            pass
    raise SystemExit(code)
