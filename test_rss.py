import feedparser

FEEDS = {
    "CNBC": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "MarketWatch": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
}

for name, url in FEEDS.items():
    feed = feedparser.parse(url)
    print(name, "->", len(feed.entries), "articles")
    if feed.entries:
        e = feed.entries[0]
        print("  title:", e.title)
        print("  link:", e.link)
        print("  published:", e.get("published_parsed"))