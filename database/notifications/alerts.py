"""
نظام التنبيهات — قنوات مجانية بالكامل:
  1) Telegram Bot API
  2) Gmail SMTP
  3) Fallback: تخزين في جدول notifications

الإعدادات تُقرأ من متغيرات البيئة:
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  SMTP_EMAIL, SMTP_APP_PASSWORD, ALERT_EMAIL_TO
"""
import os
import smtplib
from email.mime.text import MIMEText

import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_APP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD")
ALERT_EMAIL_TO = os.environ.get("ALERT_EMAIL_TO")


def send_telegram(message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
        return True
    except Exception as e:
        print(f"⚠️ فشل إرسال Telegram: {e}")
        return False


def send_email(subject: str, message: str) -> bool:
    if not SMTP_EMAIL or not SMTP_APP_PASSWORD or not ALERT_EMAIL_TO:
        return False
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = SMTP_EMAIL
        msg["To"] = ALERT_EMAIL_TO
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"⚠️ فشل إرسال البريد: {e}")
        return False


def notify_new_opportunity(conn, project: dict, scored: dict):
    message = (
        f"🚨 فرصة جديدة عالية التقييم\n"
        f"{project.get('title')}\n"
        f"فرصة الفوز: {scored['win_score']}% | الربح المتوقع: {scored['profit_score']}%\n"
        f"القطاع: {project.get('sector')} | المحافظة: {project.get('governorate')}"
    )

    sent_tg = send_telegram(message)
    sent_email = send_email("رصيف — فرصة جديدة عالية التقييم", message)

    conn.execute(
        "INSERT INTO notifications (kind, message, sent_telegram, sent_email) VALUES (?,?,?,?)",
        ("فرصة ربح عالية", message, int(sent_tg), int(sent_email)),
    )
    conn.commit()
