import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import re
import html as html_mod
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

USER_AGENT = "CorundChronicle/1.0 (+local news aggregator for Corund, Harghita)"

# 1. Targeted search feeds (already scoped to Corund / Korond)
SEARCH_FEEDS = [
    {
        "name": "Google News (RO)",
        "url": "https://" + "news.google.com/rss/search?" + urllib.parse.urlencode({
            "q": '"Corund" Harghita', "hl": "ro", "gl": "RO", "ceid": "RO:ro"
        }),
        "lang": "ro",
        "strict": False,
    },
    {
        "name": "Google News (HU)",
        "url": "https://" + "news.google.com/rss/search?" + urllib.parse.urlencode({
            "q": "Korond Harghita", "hl": "hu", "gl": "RO", "ceid": "RO:hu"
        }),
        "lang": "hu",
        "strict": False,
    },
    {
        "name": "Google News (Kerámia / Olărit)",
        "url": "https://" + "news.google.com/rss/search?" + urllib.parse.urlencode({
            "q": '"Corund" ceramica OR olărit OR kerámia OR fazekas', "hl": "ro", "gl": "RO", "ceid": "RO:ro"
        }),
        "lang": "ro",
        "strict": False,
    },
    {
        "name": "Google News (EN)",
        "url": "https://" + "news.google.com/rss/search?" + urllib.parse.urlencode({
            "q": '"Corund" Romania', "hl": "en-GB", "gl": "GB", "ceid": "GB:en"
        }),
        "lang": "en",
        "strict": False,
    },
    {
        "name": "Bing News",
        "url": "https://" + "www.bing.com/news/search?" + urllib.parse.urlencode({
            "q": "Corund Harghita", "format": "RSS"
        }),
        "lang": "ro",
        "strict": True,
    },
]

# 2. Regional outlet feeds (strictly filtered so ONLY Corund/Korond articles pass)
OUTLET_FEEDS = [
    {"name": "MASZOL", "url": "https://" + "maszol.ro/rss", "lang": "hu", "strict": True},
    {"name": "Uh.ro", "url": "https://" + "uh.ro/feed/", "lang": "hu", "strict": True},
    {"name": "Hargita Népe", "url": "https://" + "hargitanepe.ro/feed/", "lang": "hu", "strict": True},
    {"name": "Liget.ro", "url": "https://" + "liget.ro/feed/", "lang": "hu", "strict": True},
]

STRICT_KEYWORDS = ("korond", "corund")

CATEGORY_KEYWORDS = {
    "culture": ("olărit", "olar", "ceram", "kerámia", "korondi", "fazekas", "festival", "folclor", "muzeu", "múzeum", "kézműves", "hagyomány", "kiállít", "vásár", "aragonit"),
    "tourism": ("turism", "turist", "praid", "parajd", "sovata", "szováta", "salină", "sóbánya", "fürdő", "panzi", "száll", "cazare", "tábor", "kirándul"),
    "municipal": ("primar", "primărie", "primăria", "consiliu", "prefectur", "drum", "infrastructur", "canalizare", "buget", "polgármester", "önkormányzat", "tanács", "közút", "beruházás", "pályázat"),
    "community": ("sport", "baleset", "accident", "tűz", "rendőr", "iskol", "școal", "biserica", "templom", "egyház", "közösség", "comunitate", "egyesület", "asociație"),
}

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

def clean_text(raw):
    if not raw:
        return ""
    text = _TAG_RE.sub(" ", raw)
    text = html_mod.unescape(text)
    return _WS_RE.sub(" ", text).strip()

def classify(text):
    low = text.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(k in low for k in kws):
            return cat
    return "general"

def parse_dt(raw):
    if not raw:
        return datetime.now(timezone.utc)
    try:
        dt = parsedate_to_datetime(raw)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

items = []
seen_titles = set()
seen_links = set()

for feed in SEARCH_FEEDS + OUTLET_FEEDS:
    req = urllib.request.Request(feed["url"], headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        added = 0

        for item in root.iter():
            if item.tag.rsplit("}", 1)[-1] != "item":
                continue

            title = clean_text(item.findtext("{*}title"))
            link = (item.findtext("{*}link") or "").strip()
            summary = clean_text(item.findtext("{*}description"))[:280]
            raw_date = (
                item.findtext("{*}pubDate")
                or item.findtext("{http://purl.org}date")
                or ""
            ).strip()

            if not title or not link:
                continue

            # Extract original publisher attribution if present
            source = feed["name"]
            for child in item:
                if child.tag.rsplit("}", 1)[-1] in ("source", "Source") and child.text:
                    source = clean_text(child.text)
                    break

            # Strip trailing " - Publisher" from Google News titles
            for sep in (" - ", " – ", " | "):
                if title.endswith(f"{sep}{source}"):
                    title = title[:-len(f"{sep}{source}")].strip()
                    break

            # Strict relevance filter for broad feeds
            if feed["strict"]:
                haystack = f"{title} {summary}".lower()
                if not any(kw in haystack for kw in STRICT_KEYWORDS):
                    continue

            norm_title = title.lower()
            if link in seen_links or norm_title in seen_titles:
                continue

            seen_links.add(link)
            seen_titles.add(norm_title)
            dt = parse_dt(raw_date)
            formatted_date = dt.strftime("%Y-%m-%d %H:%M")

            items.append({
                "title": title,
                "link": link,
                "url": link,
                "source": source,
                "summary": summary,
                "category": classify(f"{title} {summary}"),
                "language": feed["lang"],
                "pubDate": formatted_date,
                "date": formatted_date,
                "published": formatted_date,
                "_ts": dt.timestamp(),
            })
            added += 1

        print(f"OK {feed['name']}: {added} articles")
    except Exception as e:
        print(f"SKIP {feed['name']}: {e}")

# Sort newest first and strip helper timestamp
items.sort(key=lambda x: x["_ts"], reverse=True)
for it in items:
    it.pop("_ts", None)

output = {
    "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "articles": items[:40],
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Saved {len(output['articles'])} total Corund articles.")
