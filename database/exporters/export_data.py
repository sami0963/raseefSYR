"""
تصدير البيانات — بدون أي أدوات مدفوعة.
CSV: عبر مكتبة csv المدمجة في بايثون.
TXT: نص عادي لملف المناقصة.
"""
import csv
import io


def projects_to_csv(projects: list[dict]) -> str:
    output = io.StringIO()
    fieldnames = [
        "id", "title", "sector", "source", "governorate", "value",
        "deadline", "win_score", "risk_score", "profit_score", "recommendation",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for p in projects:
        writer.writerow(p)
    return output.getvalue()


def project_to_proposal_txt(project: dict, company: dict) -> str:
    return f"""ملف مناقصة — {project['title']}
=====================================

١. ملف تعريف الشركة
{company.get('company_name', '')}
رأس المال: {company.get('capital', '')}
المعدات المتوفرة: {company.get('equipment', '')}
الخبرة: {company.get('experience', '')}
المشاريع المنفذة: {company.get('executed_projects', '')}

٢. العرض الفني
الجهة المعلنة: {project.get('source', '')}
المحافظة: {project.get('governorate', '')}
القطاع: {project.get('sector', '')}

٣. العرض المالي
قيمة العقد: ${project.get('value', 0):,.0f}
فرصة الفوز: {project.get('win_score', 0)}%
درجة المخاطرة: {project.get('risk_score', 0)}%
مؤشر الربح: {project.get('profit_score', 0)}%
التوصية: {project.get('recommendation', '')}

٤. ملاحظات
{project.get('description', '')}
""".strip()
