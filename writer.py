import csv
import json
import os
from datetime import datetime

FIELDS = [
    "app_id", "review_id", "user_name", "rating",
    "content", "thumbs_up", "review_at",
    "reply_content", "replied_at",
]


def write_per_app_csv(app_id: str, reviews: list[dict], output_dir: str) -> None:
    path = os.path.join(output_dir, f"reviews_{app_id}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(reviews)


def write_per_app_json(app_id: str, reviews: list[dict], output_dir: str) -> None:
    path = os.path.join(output_dir, f"reviews_{app_id}.json")
    serializable = [_serialize(r) for r in reviews]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)


def append_combined_csv(reviews: list[dict], output_dir: str) -> None:
    path = os.path.join(output_dir, "combined_reviews.csv")
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerows(reviews)


def update_log(app_id: str, status: str, count: int, output_dir: str) -> None:
    path = os.path.join(output_dir, "scrape_log.json")
    log = {}
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            log = json.load(f)
    log[app_id] = {
        "status": status,
        "review_count": count,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)


def _serialize(r: dict) -> dict:
    out = {}
    for k, v in r.items():
        out[k] = str(v) if hasattr(v, "isoformat") else v
    return out
