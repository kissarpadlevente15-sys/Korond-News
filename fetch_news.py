import urllib.request
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timezone

FEEDS = [
    {"name": "Uh.ro (Udvarhelyi Híradó)", "url": "https://" + "uh.ro/feed/", "filter": True},
    {"name": "Hargita Népe", "url": "https://" + "hargitanepe.ro/feed/", "filter": True},
    {"name": "Liget.ro", "url": "https://" + "liget.ro/feed/", "filter": True},
    {"name": "Informatia Harghitei", "url": "https://" + "informatiahr.ro/feed/", "filter": True}
]

KEYWORDS = ["korond", "corund", "sóvidék", "parajd", "praid", "udvarhely", "harghita", "hargita", "atyha", "firtos"]

items = []
seen_links = set()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8"
}

for feed in FEEDS:
    req = urllib.request.Request(feed["url"], headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        feed_count = 0

        for item in root.findall("./channel/item"):
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()
            pub_date = item.findtext("pubDate", default="").strip()
            desc = item.findtext("description", default="").strip()

            if feed["filter"]:
                combined = (title + " " + desc).lower()
                if not any(kw in combined for kw in KEYWORDS):
                    continue

            if link and link not in seen_links:
                seen_links.add(link)
                feed_count += 1
                items.append({
                    "title": title,
                    "link": link,
                    "pubDate": pub_date,
                    "source": feed["name"]
                })
        print(f"OK {feed['name']}: found {feed_count} matching articles")
    except Exception as e:
        print(f"FAILED {feed['name']}: {e}")

output = {
    "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "articles": items[:30]
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Total saved: {len(output['articles'])}")
