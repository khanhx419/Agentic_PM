"""Xuất cấu trúc graph thật ra Mermaid, không gọi Gemini hoặc dịch vụ vẽ ảnh."""
from pathlib import Path
from workflow import build_graph

if __name__ == "__main__":
    output = Path(__file__).with_name("WORKFLOW.mmd")
    output.write_text(build_graph(None).get_graph().draw_mermaid(), encoding="utf-8")
    print("Saved WORKFLOW.mmd (no model calls).")
