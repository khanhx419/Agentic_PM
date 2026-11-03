"""Explicit live verification. This script makes real Gemini calls only with --live."""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from importlib.metadata import version

from llm import Gemini
from pipeline import initial, advance

REQUEST = "Viết hàm validate_email(email), bỏ khoảng trắng hai đầu, đúng một @, local part không rỗng, domain có dấu chấm, không có khoảng trắng bên trong."
SEED = 'import re\nSECRET_KEY = "DEMO_ONLY_NOT_REAL"\ndef validate_email(email):\n return re.fullmatch(r"[^@\\s]+@[^@.\\s]+(?:\\.[^@.\\s]+)+", email.strip()) is not None\n'


def scenario(name, seed=""):
    model = Gemini()
    s = initial("hub", REQUEST, seed)
    phases = []
    blocked = False
    for _ in range(12):
        s = advance(s, model, confirmed=s["phase"] == "review")
        phases.append(s["phase"])
        blocked = blocked or s["phase"] == "blocked"
        print(name + ": " + s["phase"], flush=True)
        if s["status"] in ("accepted", "exhausted"):
            break
    if s["status"] != "accepted":
        raise ValueError("Live scenario did not pass; keep the real failure.")
    if seed and not blocked:
        raise ValueError("Secret sample was not blocked.")
    return {"scenario": name, "real_llm": True, "status": s["status"], "phases": phases,
            "qa_passed": s["qa"]["pass"], "qa_cases": len(s["qa"]["cases"]),
            "governance_passed": s["governance"]["pass"], "blocked_before_repair": blocked,
            "repairs": s["repairs"], "calls": s["calls"], "graph_steps": s["graph_steps"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Allow real Gemini API calls with the configured key.")
    args = parser.parse_args()
    if not args.live:
        parser.exit(message="No API calls made. Use --live deliberately.\n")
    start = time.monotonic()
    report = {"timestamp": datetime.now().astimezone().isoformat(), "langgraph": version("langgraph"),
              "scenarios": [scenario("generate"), scenario("secret-repair", SEED)],
              "seconds": round(time.monotonic() - start, 2)}
    folder = Path(__file__).with_name("verification")
    folder.mkdir(exist_ok=True)
    (folder / "live-summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Saved verification/live-summary.json without credentials or generated source.")
