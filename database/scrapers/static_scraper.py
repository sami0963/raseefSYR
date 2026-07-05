"""
Scraper لمصادر HTML/RSS ثابتة (لا تحتاج JavaScript).
يعتمد على: requests + BeautifulSoup — مجاني بالكامل.

⚠️ مهم: كل موقع له بنية HTML مختلفة. القيم هنا (SOURCES و selectors)
أمثلة تحتاج تعديل بعد فتح "Inspect" على الموقع الحقيقي.

⚠️ احترم ملف robots.txt وشروط استخدام كل موقع قبل تفعيل السحب عليه.
"""
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; RaseefBot/1.0; +https://example.com/bot)"
}

SOURCES = [
    {
        "name": "مثال - صفحة مناقصات عامة",
        "source_type": "حكومي",
        "url": "https://example-gov.sy/tenders",
        "list_selector": "div.tender-item",
        "title_selector": "h3.tender-title",
        "link_selector": "a",
        "date_selector": "span.deadline",
    },
]


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_listing(html: str, source_cfg: dict) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for node in soup.select(source_cfg["list_selector"]):
        title_el = node.select_one(source_cfg["title_selector"])
        link_el = node.select_one(source_cfg["link_selector"])
        date_el = node.select_one(source_cfg["date_selector"])

        if not title_el:
            continue

        items.append({
            "title": title_el.get_text(strip=True),
            "source_url": link_el["href"] if link_el and link_el.has_attr("href") else source_cfg["url"],
            "deadline": date_el.get_text(strip=True) if date_el else None,
            "raw_text": node.get_text(" ", strip=True),
            "source": source_cfg["name"],
            "source_type": source_cfg["source_type"],
        })
    return items


def scrape_all_static_sources() -> list[dict]:
    results = []
    for cfg in SOURCES:
        try:
            html = fetch_html(cfg["url"])
            results.extend(parse_listing(html, cfg))
        except Exception as e:
            print(f"⚠️ فشل السحب من {cfg['name']}: {e}")
    return results


if __name__ == "__main__":
    data = scrape_all_static_sources()
    print(f"تم استخراج {len(data)} عنصر")
    for d in data[:5]:
        print(d)
