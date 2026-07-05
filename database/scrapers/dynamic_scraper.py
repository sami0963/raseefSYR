"""
Scraper للمواقع التي تعتمد على JavaScript (React/Vue) — مثل بعض بوابات
المنظمات الدولية (UNGM, DevelopmentAid).
يعتمد على Playwright — مجاني بالكامل.

تثبيت (مرة واحدة):
    pip install playwright
    playwright install chromium
"""
from playwright.sync_api import sync_playwright

DYNAMIC_SOURCES = [
    {
        "name": "مثال - بوابة مناقصات ديناميكية",
        "source_type": "منظمة دولية",
        "url": "https://www.ungm.org/Public/Notice",
        "wait_selector": ".notice-list-item",
    },
]


def scrape_dynamic_source(cfg: dict) -> list[dict]:
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(cfg["url"], timeout=30000)
        try:
            page.wait_for_selector(cfg["wait_selector"], timeout=15000)
        except Exception:
            browser.close()
            return results

        nodes = page.query_selector_all(cfg["wait_selector"])
        for node in nodes:
            title = node.inner_text().strip()
            link_el = node.query_selector("a")
            href = link_el.get_attribute("href") if link_el else cfg["url"]
            results.append({
                "title": title.split("\n")[0][:200],
                "source_url": href,
                "raw_text": title,
                "source": cfg["name"],
                "source_type": cfg["source_type"],
                "deadline": None,
            })
        browser.close()
    return results


def scrape_all_dynamic_sources() -> list[dict]:
    all_results = []
    for cfg in DYNAMIC_SOURCES:
        try:
            all_results.extend(scrape_dynamic_source(cfg))
        except Exception as e:
            print(f"⚠️ فشل السحب من {cfg['name']}: {e}")
    return all_results


if __name__ == "__main__":
    data = scrape_all_dynamic_sources()
    print(f"تم استخراج {len(data)} عنصر")
    for d in data[:5]:
        print(d)
