import urllib.request
import xml.etree.ElementTree as ET
import json
import urllib.parse
from datetime import datetime

# Direct RSS feeds from regional news sites + Google News fallback
FEEDS = [
    {"url": "https://szekelyhon.ro", "filter": True},
    {"url": "https://maszol.ro", "filter": True},
    {"url": "https://transtelex.ro", "filter": True},
    {"url": "https://google.com", "filter": False},
    {"url": "https://google.com", "filter": False}
]

KEYWORDS = ["korond", "corund", "sóvidék", "parajd", "praid", "atyha", "firtos", "pálpataka"]

items = []
seen_links = set()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8"
}

for feed in FEEDS:
    url = feed["url"]
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        channel_title = root.findtext("./channel/title", default="Helyi Hírek").strip()

        for item in root.findall("./channel/item"):
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()
            pub_date = item.findtext("pubDate", default="").strip()
            desc = item.findtext("description", default="").strip()
            source_el = item.find("source")
            source = source_el.text.strip() if source_el is not None and source_el.text else channel_title

            # If it's a general regional feed, check if it mentions Korond or nearby Sóvidék villages
            if feed["filter"]:
                combined = (title + " " + desc).lower()
                if not any(kw in combined for kw in KEYWORDS):
                    continue

            if link and link not in seen_links:
                seen_links.add(link)
                items.append({
                    "title": title,
                    "link": link,
                    "pubDate": pub_date,
                    "source": source
                })
    except Exception as e:
        print(f"Could not fetch {url}: {e}")

output = {
    "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    "articles": items[:30]
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Saved {len(output['articles'])} articles to news.json")
