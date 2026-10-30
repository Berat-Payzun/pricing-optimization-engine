import io

import numpy as np
import pandas as pd

from report import Chart, Series, VLine, build_excel, build_pdf


def test_excel_has_one_sheet_per_frame():
    xlsx = build_excel({"Özet": pd.DataFrame({"Kalem": ["Fiyat"], "Değer": ["₺10"]}),
                        "A very long sheet name that Excel would reject": pd.DataFrame({"x": [1.5, 2.5]})})
    book = pd.ExcelFile(io.BytesIO(xlsx))
    assert book.sheet_names == ["Özet", "A very long sheet name that Exc"]  # trimmed to 31 characters
    assert pd.read_excel(book, "Özet").iloc[0].tolist() == ["Fiyat", "₺10"]


def test_pdf_renders_turkish_text_and_lira_sign():
    x = np.linspace(10, 100, 500)
    chart = Chart("Kâr eğrisi", x, [Series("Net kâr", -(x - 50) ** 2 + 900, "#2a78d6")], xlabel="Fiyat (₺)",
                  vlines=[VLine(50, "Optimum ₺50", "#2a78d6"), VLine(30, "Mevcut ₺30", "#898781", dashed=True)],
                  band=(45, 55, "%90 aralık"))
    pdf = build_pdf("Fiyat Optimizasyon Motoru", "Şubat · ığüşöç İ", [("Optimum fiyat", "₺50,00")], chart,
                    "Notlar", ["Uyarı: talep eğrisi dışa doğru tahmin ediliyor."], "2026-10-26")
    assert pdf.startswith(b"%PDF") and len(pdf) > 5000


def test_excel_stores_formula_like_text_as_text():
    from openpyxl import load_workbook

    payload = '=HYPERLINK("http://example.com","click")'
    xlsx = build_excel({"Data": pd.DataFrame({"Product": [payload, "-5", "@SUM(A1)"], "Units": [1, 2, 3]})})
    ws = load_workbook(io.BytesIO(xlsx))["Data"]
    assert ws["A2"].data_type == "s" and ws["A2"].value == payload
    assert [ws[f"A{i}"].data_type for i in (3, 4)] == ["s", "s"]
    assert ws["B2"].value == 1


def test_pdf_with_long_summary_moves_chart_to_next_page():
    x = np.linspace(10, 100, 50)
    chart = Chart("Profit", x, [Series("Net profit", -(x - 50) ** 2 + 900, "#2a78d6")])
    pdf = build_pdf("Title", "Subtitle", [(f"Row {i}", "value") for i in range(40)], chart)
    assert pdf.count(b"/Type /Page") - pdf.count(b"/Type /Pages") == 2
