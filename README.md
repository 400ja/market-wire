# Market Wire Project
A financial news aggregator built with Pyhton and Flask. It pulls articles from NewsAPI and RSS feeds (CNBC, MarketWatch, Yahoo Finance), merges them, removes duplicates, and shows them newest first.

# Features
- 5 different topic tabs (Top business, Markets, Economy, Fintech, Crypto)  and keyword search

- Combines NewsAPI and RSS sources into one feed

- Removes duplicate headlines and sorts by publish time

- 10-minute in-memory cache to stay within NewsAPI's free request limit

## Setup
1. Clone the repo and create a virtual environment:
   python -m venv venv
   venv\Scripts\activate
   Install dependencies: python -m pip install -r requirements.txt
2. Get a free key at newsapi.org, create an `.env` file, and add your key
3. Run: python app.py
4. Open http://127.0.0.1:5000


## Notes
-  NewsAPI's free plan delays articles by 24 hours and is for development use only, so RSS feeds provide the fresh articles.
-  General RSS feeds rarely use words like 'Fintech' so topic filtering works well on some tabs and poorly on others. Fixing that would need better matching than keywords. 
- This caused me to run into a bug where the Fintech tab went blank because my error handling edit made it fail on every tab, and RSS had been covering it for all the tabs except Fintech. This caused me to print each source's results to figure that out. 