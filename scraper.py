#!/usr/bin/env python3
import argparse
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from fetcher import fetch_reviews
from writer import append_combined_csv, update_log, write_per_app_csv, write_per_app_json


def load_app_ids(path: str) -> list[str]:
    ids = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                ids.append(line)
    return ids


def scrape_app(app_id: str, count: int, sort: str, output_dir: str) -> tuple[str, int, str]:
    time.sleep(random.uniform(1.0, 2.5))
    try:
        reviews = fetch_reviews(app_id, count=count, lang="en", sort=sort)
        if reviews:
            write_per_app_csv(app_id, reviews, output_dir)
            write_per_app_json(app_id, reviews, output_dir)
            append_combined_csv(reviews, output_dir)
            update_log(app_id, "success", len(reviews), output_dir)
            return app_id, len(reviews), "success"
        else:
            update_log(app_id, "empty", 0, output_dir)
            return app_id, 0, "empty"
    except Exception as exc:
        update_log(app_id, "failed", 0, output_dir)
        return app_id, 0, f"failed: {exc}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Google Play Store reviews")
    parser.add_argument("--apps", default="apps_list.txt", help="Path to app IDs file")
    parser.add_argument("--count", type=int, default=1000, help="Max reviews per app")
    parser.add_argument("--workers", type=int, default=3, help="Concurrent workers (1-5)")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument(
        "--sort",
        default="newest",
        choices=["newest", "rating", "helpfulness"],
        help="Review sort order",
    )
    args = parser.parse_args()

    workers = max(1, min(5, args.workers))
    os.makedirs(args.output, exist_ok=True)

    app_ids = load_app_ids(args.apps)
    if not app_ids:
        print("No app IDs found in", args.apps)
        return

    print(f"Scraping {len(app_ids)} apps | up to {args.count} reviews each | {workers} workers | sort={args.sort}")
    print(f"Output → {os.path.abspath(args.output)}\n")

    total_reviews = 0
    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(scrape_app, app_id, args.count, args.sort, args.output): app_id
            for app_id in app_ids
        }
        with tqdm(total=len(app_ids), unit="app") as bar:
            for future in as_completed(futures):
                app_id, count, status = future.result()
                if status == "success":
                    success_count += 1
                    total_reviews += count
                    bar.set_postfix({"last": app_id, "reviews": count})
                else:
                    fail_count += 1
                    bar.set_postfix({"last": app_id, "status": status})
                bar.update(1)

    print(f"\n--- Done ---")
    print(f"Apps succeeded : {success_count}")
    print(f"Apps failed    : {fail_count}")
    print(f"Total reviews  : {total_reviews}")
    print(f"Log            : {os.path.join(args.output, 'scrape_log.json')}")


if __name__ == "__main__":
    main()
