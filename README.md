# File Change Detection

A small Python tool that detects **unauthorized or unexpected file modifications** by
comparing cryptographic hashes generated before and after changes.

It computes a **SHA-256** reference hash when you select a file, stores that value,
then recomputes the hash whenever you check the file again. If the two values no
longer match, the file has been modified.

Built with only the Python standard library (`hashlib`, `os`, plus `json`/`sys` for
storage and the CLI). No installation required.

## Requirements

* Python 3.6 or newer

```bash
python3 --version
```

## Quick start

Interactive menu (just answer the prompts):

```bash
python3 file_integrity.py
```

Or use the one-shot commands:

```bash
# 1. Select a file and store its SHA-256 reference hash
python3 file_integrity.py set document.txt

# 2. Check the file later against that reference
python3 file_integrity.py check document.txt

# 3. See every monitored file
python3 file_integrity.py list
```

## How it works

1. `set` reads the chosen file in 64 KB chunks, feeds it to `hashlib.sha256()`,
   and saves the resulting hex digest in `reference_hashes.json` keyed by the
   file's absolute path.
2. `check` recomputes SHA-256 for that path and compares it with the stored value.
3. The status printed is one of:
   * `UNCHANGED - file integrity verified` — hashes match, file is untouched
   * `MODIFIED - file differs from the reference hash` — file changed after baseline
   * `UNKNOWN` — no reference hash stored yet for that file
   * `File not found` — the monitored file was deleted or moved

Exit codes: `0` = verified/OK, `1` = modified, missing, or unknown, `2` = bad usage.

## Testing it

Make a scratch directory and a test file:

```bash
mkdir integrity-test && cd integrity-test
echo "original content" > sample.txt
cp /path/to/file_integrity.py .
```

**Test 1 — clean baseline (expected: UNCHANGED)**

```bash
python3 file_integrity.py set sample.txt
python3 file_integrity.py check sample.txt
```

Look for: `[OK] Status: UNCHANGED - file integrity verified.` and exit code `0`
(`echo $?` prints `0`).

**Test 2 — modified file (expected: MODIFIED)**

```bash
echo "tampered content" >> sample.txt
python3 file_integrity.py check sample.txt
```

Look for: `[TAMPERED] Status: MODIFIED - file differs from the reference hash.`
and exit code `1`.

**Test 3 — identical content written back (expected: UNCHANGED again)**

```bash
printf 'original content\n' > sample.txt
python3 file_integrity.py check sample.txt    # UNCHANGED
```

Hashes depend only on content, not timestamps, so restoring the exact bytes passes.

**Test 4 — file deleted (expected: FAILED)**

```bash
rm sample.txt
python3 file_integrity.py check sample.txt    # File not found, exit code 1
```

**Test 5 — checking a file with no baseline (expected: UNKNOWN)**

```bash
echo "hello" > other.txt
python3 file_integrity.py check other.txt     # No reference hash stored
```

**Test 6 — re-baselining (expected: UNCHANGED after an update)**

```bash
echo "new content" > other.txt
python3 file_integrity.py set other.txt       # reference hash updated
python3 file_integrity.py check other.txt     # UNCHANGED
```

**Test 7 — large file performance**

```bash
head -c 100000000 /dev/urandom > big.bin     # ~100 MB
python3 file_integrity.py set big.bin
python3 file_integrity.py check big.bin
```

The file is read in chunks, so memory use stays flat regardless of file size.

**Test 8 — `list` output**

```bash
python3 file_integrity.py list
```

Each monitored path is shown with its stored hash and whether it is still present.

## Notes

* Reference hashes live in `reference_hashes.json` next to the script — keep it
  somewhere the monitored files cannot write to.
* Any edit to a file changes its hash, including whitespace, line endings, and
  timestamps embedded by other programs.
* This is an integrity checker, not antivirus software: it tells you *that* a file
  changed, not whether the change was malicious.

## License

MIT
