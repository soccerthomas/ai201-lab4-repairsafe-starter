import json
import os
from datetime import datetime, timezone
from config import LOG_FILE


def log_interaction(question: str, tier: str, response: str) -> None:
    """
    Append a structured record of this interaction to the audit log.
    Writes one JSON object per line to LOG_FILE in .jsonl format.
    Also prints a one-line summary to the terminal.
    """
    # 1. build the log record
    record: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tier": tier,
        "question": question[:300],
        "question_length": len(question),
        "response_preview": response[:200],
        "response_length": len(response),
    }

    # 2. create the logs/ directory if it doesn't exist
    log_dir: str = os.path.dirname(LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # 3. append the record as a single JSON line
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    # 4. print one-line terminal summary
    question_preview: str = question[:60]
    print(f'[LOGGED] tier={tier} | "{question_preview}" → {len(response)} chars')