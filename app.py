import os
import re
import time
from datetime import datetime, timezone

import feedparser
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request

load_dotenv()
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

app = Flask(__name__)
CACHE_SECONDS = 600 #10 MIN TO KEEP RESULTS
cache = {}

TOPICS = {
    "top": {"label": "Top business", "q": None},
    "markets": {"label": "Markets", "q": "stock market OR Wall Street"},
    "economy": {"label": "Economy", "q": "inflation OR Federal Reserve OR interest rates"},
    "fintech": {"label": "Fintech", "q": "fintech OR payments OR digital banking"},
    "crypto": {"label": "Crypto", "q": "bitcoin OR ethereum OR crypto"},
}

# Paste only the feeds that worked in your test
RSS_FEEDS = {
    "CNBC": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "MarketWatch": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
}


def clean(text):
    """Strips HTML tags and extra spaces from text."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def fetch_newsapi(query=None):
    if query:
        url = "https://newsapi.org/v2/everything"
        params = {"q": query, "language": "en", "sortBy": "publishedAt", "pageSize": 40}
    else:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"category": "business", "country": "us"}

    try:
        response = requests.get(
            url, params=params, headers={"X-Api-Key": NEWSAPI_KEY}, timeout=10
        )
        data = response.json()
    except requests.RequestException:
        raise RuntimeError("NewsAPI: could not connect.")

    if data.get("status") != "ok":
        raise RuntimeError("NewsAPI: " + data.get("message", "unknown error"))

    articles = []
    for item in data.get("articles", []):
        if not item["title"] or item["title"] == "[Removed]":
            continue
        articles.append({
            "title": clean(item["title"]),
            "url": item["url"],
            "source": item["source"]["name"],
            "summary": clean(item["description"]),
            "published": datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00")),
        })
    return articles


def fetch_rss(name, url, keywords):
    feed = feedparser.parse(url)
    if not feed.entries:
        raise RuntimeError(f"{name} feed returned nothing.")

    articles = []
    for entry in feed.entries:
        stamp = entry.get("published_parsed")
        if not stamp:
            continue
        article = {
            "title": clean(entry.get("title")),
            "url": entry.get("link"),
            "source": name,
            "summary": clean(entry.get("summary")),
            "published": datetime(*stamp[:6], tzinfo=timezone.utc),
        }
        # RSS feeds are general news, so filter by topic keywords when there are any
        text = (article["title"] + " " + article["summary"]).lower()
        if keywords and not any(k in text for k in keywords):
            continue
        articles.append(article)
    return articles

def dedupe_and_sort(articles):
    # Newest first
    articles = sorted(articles, key=lambda a: a["published"], reverse=True)

    seen = set()
    unique = []
    for a in articles:
        # Lowercase the title, drop punctuation and spaces, keep the first 60 characters
        fingerprint = re.sub(r"\W+", "", a["title"].lower())[:60]
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique.append(a)
    return unique[:60]


@app.template_filter("timeago")
def timeago(dt):
    seconds = int((datetime.now(timezone.utc) - dt).total_seconds())
    if seconds < 3600:
        return f"{max(seconds // 60, 1)}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"

def get_articles(query, keywords):
    cached = cache.get(query)
    if cached and time.time() - cached["time"] < CACHE_SECONDS:
        return cached["articles"], cached["errors"]

    articles, errors = [], []

    try:
        news = fetch_newsapi(query)
        print("NewsAPI returned:", len(news))
        articles += news
    except Exception as exc:
        print("NewsAPI error:", exc)
        errors.append(str(exc))

    for name, url in RSS_FEEDS.items():
        try:
            items = fetch_rss(name, url, keywords)
            print(name, "returned:", len(items))
            articles += items
        except Exception as exc:
            print(name, "error:", exc)
            errors.append(str(exc))

    articles = dedupe_and_sort(articles)

    if articles:  # don't save empty results
        cache[query] = {"time": time.time(), "articles": articles, "errors": errors}
    return articles, errors

@app.route("/")
def index():
    topic = request.args.get("topic", "top")
    if topic not in TOPICS:
        topic = "top"

    search = request.args.get("q", "").strip()
    query = search or TOPICS[topic]["q"]

    # Turn "bitcoin OR ethereum OR crypto" into ["bitcoin", "ethereum", "crypto"]
    keywords = []
    if query:
        keywords = [w.lower() for w in query.split() if w != "OR"]

    articles, errors = get_articles(query, keywords)

    return render_template(
        "index.html",
        articles=articles,
        topics=TOPICS,
        topic=topic,
        search=search,
    )


if __name__ == "__main__":
    app.run(debug=True)