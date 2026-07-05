"""
محرك التقييم — Rule-Based Scoring Engine
لا يعتمد على أي API مدفوع أو نموذج ذكاء اصطناعي خارجي.
كل النتائج مبنية على قواعد واضحة وقابلة للتعديل.
"""

HARD_GOVERNORATES = {"الحسكة", "دير الزور", "الرقة", "إدلب"}

RECONSTRUCTION_SECTORS = {"إعادة إعمار", "طرق وبنية تحتية", "مياه وصرف صحي"}


def _clamp(n, lo=0, hi=100):
    return max(lo, min(hi, n))


def score_project(project: dict) -> dict:
    """
    project المتوقع أن يحتوي على المفاتيح:
    source_type, sector, competition, duration_days, value, governorate

    يُرجع: win_score, risk_score, profit_score, recommendation
    """
    source_type = project.get("source_type", "")
    sector = project.get("sector", "")
    competition = project.get("competition", "متوسطة")
    duration_days = project.get("duration_days") or 180
    value = project.get("value") or 0
    governorate = project.get("governorate", "")

    win = 40

    if source_type == "منظمة دولية":
        win += 20
    if sector in RECONSTRUCTION_SECTORS:
        win += 15
    if competition == "منخفضة":
        win += 25
    elif competition == "عالية":
        win -= 15
    if duration_days < 60:
        win -= 10
    if value > 1_000_000:
        win += 10
    if governorate in HARD_GOVERNORATES:
        win -= 15

    win_score = _clamp(win)

    risk = 25
    if competition == "عالية":
        risk += 25
    elif competition == "منخفضة":
        risk -= 10
    if governorate in HARD_GOVERNORATES:
        risk += 20
    if duration_days < 60:
        risk += 10
    if value > 2_000_000:
        risk += 10

    risk_score = _clamp(risk)

    profit = 50
    profit += (win_score - risk_score) * 0.4
    if source_type == "هيئة الاستثمار":
        profit += 10
    if sector == "طاقة":
        profit += 10

    profit_score = _clamp(round(profit))

    if win_score >= 65 and risk_score <= 40:
        recommendation = "YES"
    elif win_score >= 45:
        recommendation = "MAYBE"
    else:
        recommendation = "NO"

    return {
        "win_score": win_score,
        "risk_score": risk_score,
        "profit_score": profit_score,
        "recommendation": recommendation,
    }


if __name__ == "__main__":
    sample = {
        "source_type": "منظمة دولية",
        "sector": "زراعي",
        "competition": "منخفضة",
        "duration_days": 150,
        "value": 680_000,
        "governorate": "حماة",
    }
    print(score_project(sample))
