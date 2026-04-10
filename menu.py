import os
import sys
import subprocess
from pathlib import Path
from art import LOGO

BASE = Path(__file__).parent


def main():
    clear = True
    while True:
        if clear:
            os.system("cls" if os.name == "nt" else "clear")
        clear = True

        print(LOGO)
        print("=" * 72)
        print("  Select a build to run:")
        print()
        print("  1  Original   — course exercise, single file")
        print("  2  Advanced   — refactored build with config, classes & modules")
        print()
        print("  q  Quit")
        print("=" * 72)

        choice = input("\nYour choice: ").strip().lower()

        if choice == "1":
            path = BASE / "original" / "main.py"
            subprocess.run([sys.executable, str(path)], cwd=str(path.parent))
            input("\nPress Enter to return to menu...")
        elif choice == "2":
            path = BASE / "advanced" / "main.py"
            subprocess.run([sys.executable, str(path)], cwd=str(path.parent))
            input("\nPress Enter to return to menu...")
        elif choice == "q":
            break
        else:
            print("Invalid choice. Try again.")
            clear = False


if __name__ == "__main__":
    main()
