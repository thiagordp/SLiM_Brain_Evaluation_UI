"""Refuse to hand over an archive that carries credentials.

    python app/tools/check_archive.py ../SLiM_Brain_Evaluation_UI.zip

Lists every entry that looks like key material or local secrets — a
service-account key, `.streamlit/` contents, `.env` files, private keys — and
exits 1 if there is any. Run it on any project archive before sharing it.
"""
from __future__ import annotations

import fnmatch
import sys
import zipfile

PATTERNS = ("*service-account*.json", "*service_account*.json", "*credentials*.json",
            "*client_secret*.json", "*/.streamlit/*", ".streamlit/*", "*secrets.toml",
            "*.env", "*/.env.*", "*.pem", "*.p12", "*.key", "*.pfx", "*id_rsa*")


def flagged(names):
    return [n for n in names if not n.endswith("/")
            and any(fnmatch.fnmatch(n, p) for p in PATTERNS)]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    with zipfile.ZipFile(sys.argv[1]) as archive:
        found = flagged(archive.namelist())
    for name in found:
        print(f"CREDENTIAL  {name}")
    if found:
        print(f"\n{len(found)} file(s) must not be shared. Rebuild the archive without "
              f"them, and rotate any key it contained.")
        return 1
    print("no credential files found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
