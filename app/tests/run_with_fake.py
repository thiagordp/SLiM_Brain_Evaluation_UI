"""Look at the app in a browser without a Google workbook. TEST TOOL ONLY.

    python app/tests/run_with_fake.py            # http://localhost:8599

Bootstraps the configured round into an in-memory workbook and serves the app
against it. Every answer is lost when the process stops: this is for looking at
the interface, never for evaluation. The deployed app has no such mode.
"""
from __future__ import annotations

import contextlib
import io
import os
import pathlib
import sys

APP = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(APP), str(APP / "tests"), str(APP / "tools")]
os.environ.setdefault("HE_APP_PASSWORD", "preview")
os.environ.setdefault("HE_ADMIN_SECRET", "preview-admin")

import bootstrap_round  # noqa: E402
import fakes  # noqa: E402
import store  # noqa: E402


def main() -> None:
    store.use_workbook(fakes.FakeWorkbook())
    sys.argv = ["bootstrap_round.py"]
    with contextlib.redirect_stdout(io.StringIO()):
        assert bootstrap_round.main() == 0
    print("in-memory round ready · password 'preview' · admin 'preview-admin'")
    from streamlit.web import bootstrap

    bootstrap.run(str(APP / "streamlit_app.py"), False, [],
                  {"server_port": 8599, "server_headless": True})


if __name__ == "__main__":
    main()
