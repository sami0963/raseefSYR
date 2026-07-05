"""
المنسّق الرئيسي — يشغّل كل الـ scrapers، يصنّف ويقيّم كل مشروع، ويخزّنه.
تشغيل يدوي:   python scraper/run_scraper.py
تشغيل مجدول:  أضفه إلى crontab كل 6 ساعات (راجع README.md)
"""
import sys
import os
import sqlite3
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.static_scraper import scrape_all_static_sources
from scrapers.dynamic_scraper import scrape_all_dynamic_sources
from engine.scoring import score_project
from notifications.alerts import notify_new_opportunity

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "raseef.db")

SECTOR_KEYWORDS = {
    "إعادة إعمار": ["ترميم", "إعادة إعمار", "تأهيل"],
    "طرق وبنية تحتية": ["طريق", "أوتوستراد", "رصيف", "إنارة", "جسر"],
    "زراعي": ["ري", "زراع", "بئر", "مضخة", "بيوت بلاستيكية"],
    "طاقة": ["طاقة شمسية", "كهرباء", "مولد"],
    "مياه وصرف صحي": ["صرف صحي", "شبكة مياه", "خزان"],
    "صناعي": ["مصنع", "مستودع", "خط إنتاج"],
}

GOVERNORATES = [
    "دمشق", "ريف دمشق", "حلب", "حمص", "حماة", "اللاذقية", "طرطوس",
    "درعا", "السويداء", "القنيطرة", "دير الزور", "الرقة", "الحسكة", "إدلب",
]


def guess_sector(text: str) -> str:
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(k in text for k in keywords):
            return sector
    return "غير مصنّف"


def guess_governorate(text: str) -> str | None:
    for gov in GOVERNORATES:
        if gov in text:
            return gov
    return None


def guess_value(text: str) -> float:
    match = re.search(r"([\d,\.]+)\s*(مليون)?\s*(\$|دولار)?", text)
    if not match:
        return 0
    num = match.group(1).replace(",", "")
    try:
        value = float(num)
        if match.group(2):
            value *= 1_000_000
        return value
    except ValueError:
        return 0


def store_project(conn, item: dict):
    scored = score_project(item)
    try:
        conn.execute("""
            INSERT INTO projects
                (title, sector, source, source_type, source_url, value, deadline,
                 governorate, description, raw_text, competition, duration_days,
                 win_score, risk_score, profit_score, recommendation)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            item["title"], item.get("sector"), item.get("source"), item.get("source_type"),
            item.get("source_url"), item.get("value", 0), item.get("deadline"),
            item.get("governorate"), item.get("raw_text", "")[:500], item.get("raw_text"),
            item.get("competition", "متوسطة"), item.get("duration_days", 180),
            scored["win_score"], scored["risk_score"], scored["profit_score"], scored["recommendation"],
        ))
        conn.commit()
        return True, scored
    except sqlite3.IntegrityError:
        return False, scored


def run():
    conn = sqlite3.connect(DB_PATH)

    raw_items = []
    raw_items += scrape_all_static_sources()
    raw_items += scrape_all_dynamic_sources()

    new_count = 0
    for item in raw_items:
        text = item.get("raw_text", "") + " " + item.get("title", "")
        item["sector"] = guess_sector(text)
        item["governorate"] = guess_governorate(text)
        item["value"] = item.get("value") or guess_value(text)
        item.setdefault("competition", "متوسطة")
        item.setdefault("duration_days", 180)

        inserted, scored = store_project(conn, item)
        if inserted:
            new_count += 1
            if scored["recommendation"] == "YES":
                notify_new_opportunity(conn, item, scored)

    status = "ok" if raw_items else "no_data"
    conn.execute(
        "INSERT INTO scrape_log (source, status, new_projects, message) VALUES (?,?,?,?)",
        ("all_sources", status, new_count, f"تم فحص {len(raw_items)} عنصر"),
    )
    conn.commit()
    conn.close()
    print(f"✅ اكتمل السحب — عناصر جديدة: {new_count} من أصل {len(raw_items)} تم فحصها")


if __name__ == "__main__":
    run()