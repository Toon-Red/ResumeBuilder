"""One-time setup: install dependencies, create config, ensure directories."""

import shutil
import subprocess
import sys
from pathlib import Path


def main():
    base = Path(__file__).parent

    # Install dependencies
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(base / "requirements.txt")])

    # Create config.json from example if it doesn't exist
    config = base / "config.json"
    example = base / "config.example.json"
    if not config.exists() and example.exists():
        shutil.copy(example, config)
        print(f"Created {config} from example — edit it to set your pdflatex path.")
    elif config.exists():
        print(f"{config} already exists, skipping.")

    # Ensure data directories exist
    (base / "data" / "active").mkdir(parents=True, exist_ok=True)
    (base / "output").mkdir(exist_ok=True)

    print("\nSetup complete! Run the server with:")
    print(f"  {sys.executable} run_server.py")


if __name__ == "__main__":
    main()
