
        items.append(
            {
                "title": title,
                "link": link,
                "published": published.isoformat().replace("+00:00", "Z")
                if published
                else pub_date_raw,
                "source": source or "Google News",
                "_sort_date": published or datetime.min.replace(tzinfo=timezone.utc),
            }
        )

    items.sort(key=lambda entry: entry["_sort_date"], reverse=True)
    for item in items:
        item.pop("_sort_date", None)
    return items[:20]


def main() -> int:
    try:
        news = fetch_items()
        payload = {
            "query": QUERY,
            "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "count": len(news),
            "articles": news,
        }
        OUTPUT_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Saved {len(news)} articles to {OUTPUT_FILE}")
        return 0
    except (urllib.error.URLError, TimeoutError, ET.ParseError, ValueError) as exc:
        print(f"Could not update news feed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
