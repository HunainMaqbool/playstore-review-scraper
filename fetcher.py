import time
import logging
from google_play_scraper import reviews, Sort

logger = logging.getLogger(__name__)

SORT_MAP = {
    "newest": Sort.NEWEST,
    "rating": Sort.RATING,
    "helpfulness": Sort.MOST_RELEVANT,
}

FIELDS = [
    "app_id", "review_id", "user_name", "rating",
    "content", "thumbs_up", "review_at",
    "reply_content", "replied_at",
]


def fetch_reviews(app_id: str, count: int, lang: str = "en", sort: str = "newest") -> list[dict]:
    sort_order = SORT_MAP.get(sort, Sort.NEWEST)
    collected = []
    continuation_token = None
    attempt = 0
    max_attempts = 3

    while len(collected) < count:
        batch_size = min(200, count - len(collected))
        delay = 0

        for attempt in range(1, max_attempts + 1):
            try:
                result, continuation_token = reviews(
                    app_id,
                    lang=lang,
                    country="us",
                    sort=sort_order,
                    count=batch_size,
                    continuation_token=continuation_token,
                )
                break
            except Exception as exc:
                delay = 2 ** attempt
                logger.warning("App %s attempt %d failed: %s — retrying in %ds", app_id, attempt, exc, delay)
                if attempt == max_attempts:
                    logger.error("App %s permanently failed after %d attempts", app_id, max_attempts)
                    return _normalize(app_id, collected)
                time.sleep(delay)

        if not result:
            break

        collected.extend(result)

        if continuation_token is None:
            break

    return _normalize(app_id, collected[:count])


def _normalize(app_id: str, raw: list) -> list[dict]:
    out = []
    for r in raw:
        out.append({
            "app_id": app_id,
            "review_id": r.get("reviewId", ""),
            "user_name": r.get("userName", ""),
            "rating": r.get("score", 0),
            "content": r.get("content", ""),
            "thumbs_up": r.get("thumbsUpCount", 0),
            "review_at": r.get("at", ""),
            "reply_content": r.get("replyContent", ""),
            "replied_at": r.get("repliedAt", ""),
        })
    return out
