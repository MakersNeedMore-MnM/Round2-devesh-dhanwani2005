from pathlib import Path
import json

from app.data.demo_attack import DEMO_ATTACK_LOGS


def load_demo_rows() -> list:
    candidates = [
        Path(__file__).resolve().parents[3] / "sample-data" / "attack_logs.json",
        Path(__file__).resolve().parent / "attack_logs.json",
        Path("/app/sample-data/attack_logs.json"),
    ]
    for path in candidates:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return DEMO_ATTACK_LOGS
