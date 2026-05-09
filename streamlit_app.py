import csv
import io
import re
import sys
import os

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
from fetcher import fetch_reviews

# ── helpers ──────────────────────────────────────────────────────────────────

def extract_app_id(raw: str) -> str:
    raw = raw.strip()
    # Full Play Store URL — pull the id= param
    match = re.search(r"[?&]id=([a-zA-Z0-9._]+)", raw)
    if match:
        return match.group(1)
    # Bare package name (e.g. com.king.candycrushsaga)
    if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+", raw):
        return raw
    return ""


def reviews_to_csv_bytes(reviews: list[dict]) -> bytes:
    fields = [
        "app_id", "review_id", "user_name", "rating",
        "content", "thumbs_up", "review_at",
        "reply_content", "replied_at",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(reviews)
    return buf.getvalue().encode("utf-8")


# ── page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Play Store Review Scraper",
    page_icon="🎮",
    layout="centered",
)

st.title("🎮 Play Store Review Scraper")
st.caption("Paste an app ID or full Play Store URL to download reviews as CSV.")

# ── inputs ───────────────────────────────────────────────────────────────────

raw_input = st.text_input(
    "App ID or Play Store URL",
    placeholder="e.g. com.king.candycrushsaga  or  https://play.google.com/store/apps/details?id=...",
)

count = st.selectbox("Number of reviews to scrape", [100, 500, 1000], index=2)

sort = st.selectbox("Sort by", ["newest", "rating", "helpfulness"], index=0)

scrape_btn = st.button("Scrape Reviews", type="primary", use_container_width=True)

# ── scrape ───────────────────────────────────────────────────────────────────

if scrape_btn:
    if not raw_input.strip():
        st.error("Please enter an app ID or Play Store URL.")
    else:
        app_id = extract_app_id(raw_input)
        if not app_id:
            st.error(
                "Could not recognise a valid app ID or Play Store URL. "
                "Example: `com.spotify.music` or the full store URL."
            )
        else:
            st.info(f"Scraping **{count}** reviews for `{app_id}` …")
            with st.spinner("Fetching reviews from Play Store …"):
                try:
                    reviews = fetch_reviews(app_id, count=count, sort=sort)
                except Exception as exc:
                    reviews = []
                    st.error(f"Scrape failed: {exc}")

            if reviews:
                st.success(f"Fetched **{len(reviews)}** reviews.")

                # Preview table
                import pandas as pd
                df = pd.DataFrame(reviews)
                st.subheader("Preview (first 10 rows)")
                st.dataframe(
                    df[["user_name", "rating", "content", "review_at"]].head(10),
                    use_container_width=True,
                )

                # Download button
                csv_bytes = reviews_to_csv_bytes(reviews)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_bytes,
                    file_name=f"reviews_{app_id}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            elif not st.session_state.get("scrape_error"):
                st.warning(
                    f"No reviews found for `{app_id}`. "
                    "Check that the app ID is correct and the app has reviews."
                )
