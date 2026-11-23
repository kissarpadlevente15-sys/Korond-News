import urllib.request
import xml.etree.ElementTree as ET
import json
import urllib.parse
from datetime import datetime

FEEDS = [
    "https://google.com" + urllib.parse.quote("Korond") + "&hl=hu&gl=RO&ceid=RO:hu",
    "https://google.com" + urllib.parse.quote("Corund") + "&hl=ro&gl=RO&ceid=RO:ro"
]

items = []
seen_links = set()

for url in FEEDS:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        for item in root.findall("./channel/item"):
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()
            pub_date = item.findtext("pubDate", default="").strip()
            source_el = item.find("source")
            source = source_el.text.strip() if source_el is not None and source_el.text else "Google News"

            if link and link not in seen_links:
                seen_links.add(link)
                items.append({
                    "title": title,
                    "link": link,
                    "pubDate": pub_date,
                    "source": source
                })
    except Exception as e:
        print(f"Error fetching {url}: {e}")

output = {
    "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    "articles": items[:25]
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Saved {len(output['articles'])} articles to news.json")
