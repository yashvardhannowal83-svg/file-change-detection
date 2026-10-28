#!/usr/bin/env python3
"""File integrity monitoring tool.

Generates a SHA-256 reference hash for a file, regenerates it later, and
compares the two to detect unauthorized or unexpected modifications.

Usage:
    python file_integrity.py                 # interactive menu
    python file_integrity.py set <file>      # store reference hash
    python file_integrity.py check <file>    # compare with reference
    python file_integrity.py list            # show all monitored files
"""

import hashlib
import json
import os
import sys

STORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference_hashes.json")
CHUNK_SIZE = 65536

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Fall back to plain text when the terminal does not support colour codes.
if not sys.stdout.isatty():
    GREEN = RED = YELLOW = CYAN = RESET = BOLD = ""


def compute_hash(path):
    """Return the SHA-256 hex digest of a file, read in chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_store():
    """Load the stored reference hashes, or return an empty mapping."""
    if not os.path.isfile(STORE_FILE):
        return {}
    try:
        with open(STORE_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        return {}


def save_store(store):
    with open(STORE_FILE, "w", encoding="utf-8") as handle:
        json.dump(store, handle, indent=2, sort_keys=True)
        handle.write("\n")


def set_reference(path):
    """Select a file and store its SHA-256 hash as the reference value."""
    if not os.path.isfile(path):
        print(f"{RED}[ERROR]{RESET} Not a readable file: {path}")
        return False

    path = os.path.abspath(path)
    file_hash = compute_hash(path)
    store = load_store()
    first_time = path not in store
    store[path] = file_hash
    save_store(store)

    label = "Reference hash generated" if first_time else "Reference hash updated"
    print(f"{GREEN}[OK]{RESET} {label} for: {path}")
    print(f"     SHA-256: {file_hash}")
    print(f"     Size   : {os.path.getsize(path)} bytes")
    print(f"     Stored in: {STORE_FILE}")
    return True


def check_integrity(path):
    """Regenerate the hash of a file and compare it with the stored value."""
    if not os.path.isfile(path):
        print(f"{RED}[FAILED]{RESET} File not found: {path}")
        return False

    path = os.path.abspath(path)
    store = load_store()
    reference = store.get(path)

    if reference is None:
        print(f"{YELLOW}[UNKNOWN]{RESET} No reference hash stored for: {path}")
        print("         Run 'set' first to establish a baseline.")
        return False

    current = compute_hash(path)
    print(f"File      : {path}")
    print(f"Reference : {reference}")
    print(f"Current   : {current}")

    if current == reference:
        print(f"{GREEN}{BOLD}[OK]{RESET} Status: UNCHANGED - file integrity verified.")
        return True

    print(f"{RED}{BOLD}[TAMPERED]{RESET} Status: MODIFIED - file differs from the reference hash.")
    print("         The file was changed after the reference hash was generated.")
    return False


def list_files():
    """Show every monitored file and its stored reference hash."""
    store = load_store()
    if not store:
        print("No files are being monitored yet.")
        return
    print(f"{CYAN}Monitored files ({len(store)}){RESET}")
    for path in sorted(store):
        state = "present" if os.path.isfile(path) else "MISSING"
        print(f"  [{state}] {path}")
        print(f"      {store[path]}")


def prompt_path(prompt_text):
    try:
        return input(prompt_text).strip().strip('"')
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def interactive_menu():
    """Simple text menu used when the script is started without arguments."""
    actions = {
        "1": "Select a file and generate its reference hash",
        "2": "Check a file against its reference hash",
        "3": "List monitored files",
        "4": "Exit",
    }
    while True:
        print(f"\n{CYAN}{BOLD}=== File Integrity Monitor ==={RESET}")
        for key, text in actions.items():
            print(f"  {key}) {text}")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            path = prompt_path("Enter the file to monitor: ")
            if path:
                set_reference(path)
        elif choice == "2":
            path = prompt_path("Enter the file to check: ")
            if path:
                check_integrity(path)
        elif choice == "3":
            list_files()
        elif choice == "4":
            print("Exiting.")
            break
        else:
            print("Invalid option, try again.")


def main(argv):
    if len(argv) == 1:
        interactive_menu()
        return 0

    command = argv[1].lower()
    if command in ("set", "hash", "monitor"):
        if len(argv) < 3:
            print("Usage: python file_integrity.py set <file>")
            return 2
        return 0 if set_reference(argv[2]) else 1
    if command in ("check", "verify"):
        if len(argv) < 3:
            print("Usage: python file_integrity.py check <file>")
            return 2
        return 0 if check_integrity(argv[2]) else 1
    if command == "list":
        list_files()
        return 0
    if command in ("-h", "--help", "help"):
        print(__doc__.strip())
        return 0

    print(f"Unknown command: {command}")
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
