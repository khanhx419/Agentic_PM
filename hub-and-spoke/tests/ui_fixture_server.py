"""Test-only HTTP server: fake LLM, real LangGraph and AST/QA. Never used by start.cmd."""
import sys
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_system import FakeModel
from app import make_server
from store import Store

with tempfile.TemporaryDirectory() as folder:
    with patch("config.settings", return_value={"key": "TEST_DOUBLE_NOT_REAL", "model": "TEST_DOUBLE"}):
        server = make_server(0, FakeModel(), Store(folder))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print("http://127.0.0.1:" + str(server.server_address[1]), flush=True)
        try:
            sys.stdin.readline()
        finally:
            server.shutdown()
            server.server_close()
