import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timezone

QUERIES = [
    {"q": "Korond OR Parajd OR Székelyudvarhely", "hl": "hu", "gl": "HU", "ceid": "HU:hu"},
    {"q": "Corund OR Praid OR Harghita", "hl": "ro", "gl": "RO", "ceid": "RO:ro"},
    {"q": "Korond", "hl": "hu", "gl": "HU", "ceid": "HU:hu"}
]

items = []
seen_links = set()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

for query in QUERIES:
    params = urllib.parse.urlencode(query)
    url = "https://" + "://google.com" + "/rss/search?" + params
    req = urllib.request.Request(url, headers=headers)
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
        print(f"Error for {query['q']}: {e}")

output = {
    "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "articles": items[:30]
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Saved {len(output['articles'])} articles to news.json")
