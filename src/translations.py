"""UI strings in English, Turkish and German.

STRINGS maps each key to its three translations, so a string and its translations sit
side by side. Templates use str.format placeholders, which must be identical across
languages (tests/test_translations.py checks this).

Backend modules report user-facing messages as `Msg` objects: plain English strings
that also remember their key and parameters, so the UI can re-render them in the
selected language with `localize`.
"""

from __future__ import annotations

LANGUAGES = {"en": "🇬🇧 English", "tr": "🇹🇷 Türkçe", "de": "🇩🇪 Deutsch"}

STRINGS: dict[str, dict[str, str]] = {
    # ---------- sidebar ----------
    "sidebar_header": {"en": "Inputs", "tr": "Girdiler", "de": "Eingaben"},
    "upload_label": {"en": "Sales history CSV", "tr": "Satış geçmişi (CSV)", "de": "Verkaufshistorie (CSV)"},
    "upload_help": {
        "en": "Columns: Date, Price_Charged, Quantity_Sold, optional Cost_Per_Unit, Competitor_Price",
        "tr": "Sütunlar: Date, Price_Charged, Quantity_Sold; isteğe bağlı Cost_Per_Unit, Competitor_Price",
        "de": "Spalten: Date, Price_Charged, Quantity_Sold; optional Cost_Per_Unit, Competitor_Price",
    },
    "sample_caption": {
        "en": "No file uploaded: using the bundled sample data.",
        "tr": "Dosya yüklenmedi: hazır örnek veri kullanılıyor.",
        "de": "Keine Datei hochgeladen: Die mitgelieferten Beispieldaten werden verwendet.",
    },
    "sample_download": {"en": "Download sample CSV", "tr": "Örnek CSV'yi indir", "de": "Beispiel-CSV herunterladen"},
    "country_label": {"en": "Target country", "tr": "Hedef ülke", "de": "Zielland"},
    "country_US": {"en": "United States", "tr": "Amerika Birleşik Devletleri", "de": "Vereinigte Staaten"},
    "country_EU": {"en": "Eurozone", "tr": "Euro Bölgesi", "de": "Eurozone"},
    "country_DE": {"en": "Germany", "tr": "Almanya", "de": "Deutschland"},
    "country_FR": {"en": "France", "tr": "Fransa", "de": "Frankreich"},
    "country_IT": {"en": "Italy", "tr": "İtalya", "de": "Italien"},
    "country_ES": {"en": "Spain", "tr": "İspanya", "de": "Spanien"},
    "country_GB": {"en": "United Kingdom", "tr": "Birleşik Krallık", "de": "Vereinigtes Königreich"},
    "country_TR": {"en": "Turkey", "tr": "Türkiye", "de": "Türkei"},
    "country_BR": {"en": "Brazil", "tr": "Brezilya", "de": "Brasilien"},
    "country_WORLD": {"en": "Global (World)", "tr": "Küresel (Dünya)", "de": "Global (Welt)"},
    "timeframe_label": {"en": "Timeframe", "tr": "Dönem", "de": "Zeitraum"},
    "timeframe_help": {
        "en": "All profit, revenue and cost figures are shown for this period.",
        "tr": "Tüm kâr, gelir ve maliyet rakamları bu dönem için gösterilir.",
        "de": "Alle Gewinn-, Umsatz- und Kostenzahlen werden für diesen Zeitraum angezeigt.",
    },
    "timeframe_Monthly": {"en": "Monthly", "tr": "Aylık", "de": "Monatlich"},
    "timeframe_Quarterly": {"en": "Quarterly", "tr": "Çeyreklik", "de": "Quartalsweise"},
    "timeframe_Annual": {"en": "Annual", "tr": "Yıllık", "de": "Jährlich"},
    "per_Monthly": {"en": "per month", "tr": "aylık", "de": "pro Monat"},
    "per_Quarterly": {"en": "per quarter", "tr": "çeyreklik", "de": "pro Quartal"},
    "per_Annual": {"en": "per year", "tr": "yıllık", "de": "pro Jahr"},
    "cogs_label": {
        "en": "Default COGS per unit ({sym})",
        "tr": "Varsayılan birim maliyet (SMM) ({sym})",
        "de": "Standard-Stückkosten (COGS) ({sym})",
    },
    "cogs_help": {
        "en": "Used only for rows where the CSV has no Cost_Per_Unit.",
        "tr": "Yalnızca CSV'de Cost_Per_Unit değeri olmayan satırlar için kullanılır.",
        "de": "Wird nur für Zeilen ohne Cost_Per_Unit in der CSV verwendet.",
    },
    "fixed_label": {"en": "Monthly fixed costs ({sym})", "tr": "Aylık sabit giderler ({sym})", "de": "Monatliche Fixkosten ({sym})"},
    "fixed_help": {
        "en": "Rent, salaries, software… scaled to the selected timeframe.",
        "tr": "Kira, maaşlar, yazılım… seçilen döneme göre ölçeklenir.",
        "de": "Miete, Gehälter, Software … auf den gewählten Zeitraum hochgerechnet.",
    },
    "capacity_label": {
        "en": "Capacity / inventory ceiling ({per}, units)",
        "tr": "Kapasite / stok tavanı ({per}, adet)",
        "de": "Kapazität / Lagerobergrenze ({per}, Stück)",
    },
    "capacity_help": {
        "en": "Maximum units you can sell in the period. 0 = no limit.",
        "tr": "Dönem içinde satabileceğiniz en fazla adet. 0 = sınırsız.",
        "de": "Maximale Stückzahl, die Sie im Zeitraum verkaufen können. 0 = keine Grenze.",
    },
    "import_label": {
        "en": "Share of COGS priced in USD (%)",
        "tr": "SMM'nin USD cinsinden payı (%)",
        "de": "Anteil der Stückkosten in USD (%)",
    },
    "import_help": {
        "en": "Only this share of unit cost moves with the exchange rate.",
        "tr": "Birim maliyetin yalnızca bu kısmı döviz kuruyla birlikte değişir.",
        "de": "Nur dieser Anteil der Stückkosten bewegt sich mit dem Wechselkurs.",
    },
    "model_label": {"en": "Demand model", "tr": "Talep modeli", "de": "Nachfragemodell"},
    "model_linear": {"en": "Linear", "tr": "Doğrusal", "de": "Linear"},
    "model_loglog": {
        "en": "Log-log (constant elasticity)",
        "tr": "Log-log (sabit esneklik)",
        "de": "Log-Log (konstante Elastizität)",
    },
    "real_label": {
        "en": "Adjust history for inflation",
        "tr": "Geçmişi enflasyona göre düzelt",
        "de": "Historie inflationsbereinigen",
    },
    "real_help": {
        "en": "Deflate historical prices with CPI before fitting demand, so price rises caused by inflation "
              "aren't mistaken for real price changes.",
        "tr": "Talep modeli kurulmadan önce geçmiş fiyatlar TÜFE ile reel hale getirilir; böylece enflasyondan "
              "kaynaklanan fiyat artışları gerçek fiyat değişikliği sanılmaz.",
        "de": "Historische Preise vor der Nachfrageschätzung mit dem VPI deflationieren, damit inflationsbedingte "
              "Preiserhöhungen nicht als echte Preisänderungen gelten.",
    },
    "max_price_label": {
        "en": "Max price to test ({sym})",
        "tr": "Denenecek en yüksek fiyat ({sym})",
        "de": "Höchster Testpreis ({sym})",
    },
    "max_price_help": {
        "en": "Upper bound of the price search. Default: 2× the highest historical price.",
        "tr": "Fiyat aramasının üst sınırı. Varsayılan: geçmişteki en yüksek fiyatın 2 katı.",
        "de": "Obergrenze der Preissuche. Standard: 2× der höchste historische Preis.",
    },
    # ---------- page header and errors ----------
    "app_title": {"en": "Pricing Optimization Engine", "tr": "Fiyat Optimizasyon Motoru", "de": "Preisoptimierungs-Engine"},
    "app_caption": {
        "en": "Finds the profit-maximizing price from your sales history and stress-tests it against "
              "{country} inflation, exchange-rate and competitor shocks. Prices in {currency}.",
        "tr": "Satış geçmişinizden kârı en yüksek yapan fiyatı bulur ve bu fiyatı {country} enflasyonu, "
              "döviz kuru ve rakip şoklarına karşı test eder. Fiyatlar {currency} cinsindendir.",
        "de": "Ermittelt aus Ihrer Verkaufshistorie den gewinnmaximierenden Preis und testet ihn unter Inflations-, "
              "Wechselkurs- und Wettbewerbsschocks für {country}. Preise in {currency}.",
    },
    "err_file": {
        "en": "Could not use this file: {error}",
        "tr": "Bu dosya kullanılamadı: {error}",
        "de": "Diese Datei kann nicht verwendet werden: {error}",
    },
    "err_model": {
        "en": "Could not fit the {model} demand model: {error}",
        "tr": "{model} talep modeli kurulamadı: {error}",
        "de": "Das Nachfragemodell „{model}“ konnte nicht geschätzt werden: {error}",
    },
    "spinner_macro": {
        "en": "Fetching inflation and exchange rates…",
        "tr": "Enflasyon ve döviz kurları alınıyor…",
        "de": "Inflation und Wechselkurse werden abgerufen …",
    },
    # ---------- shock simulation ----------
    "shock_header": {"en": "Macro shock simulation", "tr": "Makro şok simülasyonu", "de": "Makroschock-Simulation"},
    "shock_caption": {
        "en": "Defaults come from live data: 12-month CPI inflation and the 12-month change in the "
              "local-currency/USD rate. Move them to test what-if scenarios.",
        "tr": "Varsayılan değerler canlı veriden gelir: 12 aylık TÜFE enflasyonu ve yerel para/USD kurundaki "
              "12 aylık değişim. Farklı senaryoları denemek için kaydırın.",
        "de": "Die Standardwerte stammen aus Live-Daten: 12-Monats-Inflation (VPI) und die 12-Monats-Veränderung "
              "des Kurses Landeswährung/USD. Verschieben Sie sie, um Was-wäre-wenn-Szenarien zu testen.",
    },
    "shock_infl": {"en": "Country inflation rate (%)", "tr": "Ülke enflasyon oranı (%)", "de": "Inflationsrate des Landes (%)"},
    "shock_infl_help": {
        "en": "Raises COGS and fixed costs.",
        "tr": "SMM'yi ve sabit giderleri artırır.",
        "de": "Erhöht Stückkosten und Fixkosten.",
    },
    "shock_fx": {"en": "Exchange rate shift (%)", "tr": "Döviz kuru değişimi (%)", "de": "Wechselkursänderung (%)"},
    "shock_fx_help": {
        "en": "Change in local currency per USD. Positive = local currency weakens, so imported inputs cost more.",
        "tr": "1 USD karşılığı yerel paradaki değişim. Pozitif = yerel para değer kaybeder, ithal girdiler pahalanır.",
        "de": "Veränderung der Landeswährung pro USD. Positiv = Landeswährung wertet ab, importierte Vorleistungen "
              "werden teurer.",
    },
    "shock_comp": {"en": "Competitor price change (%)", "tr": "Rakip fiyat değişimi (%)", "de": "Preisänderung der Konkurrenz (%)"},
    "shock_comp_help": {
        "en": "Needs a Competitor_Price column in the CSV.",
        "tr": "CSV'de Competitor_Price sütunu gerekir.",
        "de": "Erfordert eine Spalte Competitor_Price in der CSV.",
    },
    "shock_reset": {"en": "Reset to live data", "tr": "Canlı verilere sıfırla", "de": "Auf Live-Daten zurücksetzen"},
    "shock_comp_disabled": {
        "en": "Competitor slider disabled: the uploaded data has no Competitor_Price column, so cross-price "
              "effects can't be estimated.",
        "tr": "Rakip kaydırıcısı devre dışı: yüklenen veride Competitor_Price sütunu yok, bu yüzden çapraz fiyat "
              "etkileri tahmin edilemez.",
        "de": "Konkurrenz-Regler deaktiviert: Die hochgeladenen Daten enthalten keine Spalte Competitor_Price, "
              "daher lassen sich Kreuzpreiseffekte nicht schätzen.",
    },
    # ---------- metric cards and badges ----------
    "metric_opt_price": {"en": "Optimal price", "tr": "Optimum fiyat", "de": "Optimaler Preis"},
    # Deltas start with the signed number: st.metric colours the arrow from the leading sign.
    "metric_opt_delta": {"en": "{pct:+.1f}% vs current", "tr": "{pct:+.1f}% (mevcut fiyata göre)", "de": "{pct:+.1f}% ggü. aktuell"},
    "metric_opt_help": {"en": "Current price: {price}", "tr": "Mevcut fiyat: {price}", "de": "Aktueller Preis: {price}"},
    "metric_profit": {"en": "Peak net profit ({per})", "tr": "En yüksek net kâr ({per})", "de": "Maximaler Nettogewinn ({per})"},
    "metric_profit_help": {
        "en": "Delta vs keeping the current price under the same scenario ({profit}).",
        "tr": "Aynı senaryoda mevcut fiyatı korumaya göre fark ({profit}).",
        "de": "Differenz zur Beibehaltung des aktuellen Preises im selben Szenario ({profit}).",
    },
    "metric_ped": {"en": "Price elasticity at optimum", "tr": "Optimumda fiyat esnekliği", "de": "Preiselastizität im Optimum"},
    "metric_ped_help": {
        "en": "% change in quantity for a 1% price change. Below -1 = elastic.",
        "tr": "Fiyattaki %1'lik değişime karşılık miktardaki % değişim. -1'in altı = esnek.",
        "de": "Prozentuale Mengenänderung bei 1 % Preisänderung. Unter -1 = elastisch.",
    },
    "metric_r2": {"en": "Demand fit R²", "tr": "Talep uyumu R²", "de": "Nachfrage-Fit R²"},
    "metric_r2_help": {
        "en": "Share of month-to-month sales variation the model explains.",
        "tr": "Modelin açıkladığı aylık satış değişkenliğinin payı.",
        "de": "Anteil der monatlichen Absatzschwankungen, den das Modell erklärt.",
    },
    "metric_cpi": {"en": "CPI inflation (YoY)", "tr": "TÜFE enflasyonu (yıllık)", "de": "VPI-Inflation (ggü. Vorjahr)"},
    "metric_fx": {"en": "FX ({currency} per USD)", "tr": "Kur (USD başına {currency})", "de": "Wechselkurs ({currency} pro USD)"},
    "metric_fx_delta": {"en": "{pct:+.1f}% 12m", "tr": "{pct:+.1f}% 12 ay", "de": "{pct:+.1f}% 12 Mon."},
    "badge_periods_dropped": {
        "en": "{n_dropped} of {total} periods dropped (zero sales)",
        "tr": "{total} dönemden {n_dropped} tanesi çıkarıldı (sıfır satış)",
        "de": "{n_dropped} von {total} Perioden entfernt (keine Verkäufe)",
    },
    "badge_cpi": {"en": "CPI", "tr": "TÜFE", "de": "VPI"},
    "badge_fx": {"en": "FX", "tr": "Kur", "de": "Wechselkurs"},
    "badge_live": {"en": "live", "tr": "canlı", "de": "live"},
    "badge_offline": {
        "en": "{label}: offline, using manual default",
        "tr": "{label}: çevrimdışı, manuel varsayılan kullanılıyor",
        "de": "{label}: offline, manueller Standardwert",
    },
    # ---------- charts ----------
    "chart_main_title": {
        "en": "Profit, revenue and cost vs price ({per})",
        "tr": "Fiyata göre kâr, gelir ve maliyet ({per})",
        "de": "Gewinn, Umsatz und Kosten nach Preis ({per})",
    },
    "chart_capacity": {"en": "capacity binding", "tr": "kapasite sınırında", "de": "Kapazität ausgeschöpft"},
    "chart_net_profit": {"en": "Net profit", "tr": "Net kâr", "de": "Nettogewinn"},
    "chart_revenue": {"en": "Revenue", "tr": "Gelir", "de": "Umsatz"},
    "chart_total_cost": {"en": "Total cost", "tr": "Toplam maliyet", "de": "Gesamtkosten"},
    "chart_optimal": {"en": "Optimal {price}", "tr": "Optimum {price}", "de": "Optimal {price}"},
    "chart_current": {"en": "Current {price}", "tr": "Mevcut {price}", "de": "Aktuell {price}"},
    "chart_peak": {"en": "Peak profit", "tr": "Zirve kâr", "de": "Gewinnmaximum"},
    "axis_price": {"en": "Price ({sym})", "tr": "Fiyat ({sym})", "de": "Preis ({sym})"},
    "axis_price_kind": {"en": "Price ({sym}, {kind})", "tr": "Fiyat ({sym}, {kind})", "de": "Preis ({sym}, {kind})"},
    "price_real": {"en": "real", "tr": "reel", "de": "real"},
    "price_nominal": {"en": "nominal", "tr": "nominal", "de": "nominal"},
    "axis_units": {"en": "Units", "tr": "Adet", "de": "Stück"},
    "units": {"en": "units", "tr": "adet", "de": "Stück"},
    "caption_break_even": {
        "en": "Break-even price(s): {prices} · Unit cost under scenario: {cogs} · Fixed costs: {fixed} {per}",
        "tr": "Başabaş fiyat(lar)ı: {prices} · Senaryodaki birim maliyet: {cogs} · Sabit giderler: {fixed} {per}",
        "de": "Break-even-Preis(e): {prices} · Stückkosten im Szenario: {cogs} · Fixkosten: {fixed} {per}",
    },
    "chart_demand_title": {
        "en": "Demand curve: units sold {per}",
        "tr": "Talep eğrisi: satılan adet ({per})",
        "de": "Nachfragekurve: verkaufte Stück {per}",
    },
    "chart_observed": {"en": "Observed months", "tr": "Gözlenen aylar", "de": "Beobachtete Monate"},
    "chart_fitted": {"en": "Fitted demand", "tr": "Tahmini talep", "de": "Geschätzte Nachfrage"},
    "chart_shock_title": {
        "en": "Shock impact on net profit ({per})",
        "tr": "Şokun net kâra etkisi ({per})",
        "de": "Schockwirkung auf den Nettogewinn ({per})",
    },
    "chart_today": {"en": "Today's costs, no shock", "tr": "Bugünkü maliyetler, şoksuz", "de": "Heutige Kosten, ohne Schock"},
    "chart_scenario": {"en": "Scenario", "tr": "Senaryo", "de": "Szenario"},
    "caption_shock": {
        "en": "Scenario moves the optimal price by {d_price} and peak profit by {d_profit} {per}.",
        "tr": "Senaryo, optimum fiyatı {d_price} ve zirve kârı {per} {d_profit} değiştiriyor.",
        "de": "Das Szenario verschiebt den optimalen Preis um {d_price} und den maximalen Gewinn um {d_profit} {per}.",
    },
    "chart_history_title": {
        "en": "Price history (monthly average)",
        "tr": "Fiyat geçmişi (aylık ortalama)",
        "de": "Preisverlauf (Monatsdurchschnitt)",
    },
    "chart_your_price": {"en": "Your price", "tr": "Sizin fiyatınız", "de": "Ihr Preis"},
    "chart_comp_price": {"en": "Competitor price", "tr": "Rakip fiyatı", "de": "Konkurrenzpreis"},
    "chart_real_price": {
        "en": "Your price (inflation-adjusted)",
        "tr": "Sizin fiyatınız (enflasyondan arındırılmış)",
        "de": "Ihr Preis (inflationsbereinigt)",
    },
    # ---------- details expander ----------
    "details_expander": {
        "en": "Model details and data notes",
        "tr": "Model ayrıntıları ve veri notları",
        "de": "Modelldetails und Datenhinweise",
    },
    "details_fitted": {
        "en": "Fitted demand (monthly units)",
        "tr": "Tahmini talep (aylık adet)",
        "de": "Geschätzte Nachfrage (Stück pro Monat)",
    },
    "col_model": {"en": "Model", "tr": "Model", "de": "Modell"},
    "col_r2": {"en": "R²", "tr": "R²", "de": "R²"},
    "col_periods": {"en": "Periods used", "tr": "Kullanılan dönem", "de": "Verwendete Perioden"},
    "col_coef": {"en": "Own-price coef", "tr": "Öz fiyat katsayısı", "de": "Eigenpreis-Koeffizient"},
    "details_ped_current": {
        "en": "Elasticity at current price: **{value}**",
        "tr": "Mevcut fiyatta esneklik: **{value}**",
        "de": "Elastizität beim aktuellen Preis: **{value}**",
    },
    "details_xed": {
        "en": "Cross-price elasticity at optimum: **{value}**",
        "tr": "Optimumda çapraz fiyat esnekliği: **{value}**",
        "de": "Kreuzpreiselastizität im Optimum: **{value}**",
    },
    "details_xed_na": {
        "en": "Cross-price elasticity: n/a (no competitor data)",
        "tr": "Çapraz fiyat esnekliği: yok (rakip verisi yok)",
        "de": "Kreuzpreiselastizität: k. A. (keine Konkurrenzdaten)",
    },
    "details_price_range": {
        "en": "Observed real price range: {low} – {high}",
        "tr": "Gözlenen reel fiyat aralığı: {low} – {high}",
        "de": "Beobachtete reale Preisspanne: {low} – {high}",
    },
    "details_notes": {"en": "Data notes", "tr": "Veri notları", "de": "Datenhinweise"},
    "details_no_issues": {"en": "No data issues found.", "tr": "Veri sorunu bulunmadı.", "de": "Keine Datenprobleme gefunden."},
    "details_months": {
        "en": "{n} months of data, {start} – {end}",
        "tr": "{n} aylık veri, {start} – {end}",
        "de": "{n} Monate Daten, {start} – {end}",
    },
    "details_agg": {"en": "Monthly aggregated data", "tr": "Aylık toplulaştırılmış veri", "de": "Monatlich aggregierte Daten"},
    "months": {
        "en": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
        "tr": "Oca,Şub,Mar,Nis,May,Haz,Tem,Ağu,Eyl,Eki,Kas,Ara",
        "de": "Jan,Feb,Mär,Apr,Mai,Jun,Jul,Aug,Sep,Okt,Nov,Dez",
    },
    # ---------- backend messages (data_ingestion.py, optimizer.py) ----------
    "warn_cpi_stale": {
        "en": "CPI data ends {as_of}: later months are not inflation-adjusted.",
        "tr": "TÜFE verisi {as_of} itibarıyla bitiyor: sonraki aylar enflasyona göre düzeltilmedi.",
        "de": "VPI-Daten enden {as_of}: Spätere Monate sind nicht inflationsbereinigt.",
    },
    "err_missing_cols": {
        "en": "Missing required column(s): {cols}",
        "tr": "Gerekli sütun(lar) eksik: {cols}",
        "de": "Erforderliche Spalte(n) fehlen: {cols}",
    },
    "warn_rows_dropped": {
        "en": "{dropped} of {n_raw} rows dropped (unparseable date, missing or non-positive price, negative quantity).",
        "tr": "{n_raw} satırdan {dropped} tanesi çıkarıldı (okunamayan tarih, eksik veya pozitif olmayan fiyat, "
              "negatif miktar).",
        "de": "{dropped} von {n_raw} Zeilen entfernt (Datum nicht lesbar, Preis fehlt oder nicht positiv, "
              "negative Menge).",
    },
    "err_no_valid_rows": {
        "en": "No valid rows left after cleaning.",
        "tr": "Temizlemeden sonra geçerli satır kalmadı.",
        "de": "Nach der Bereinigung sind keine gültigen Zeilen übrig.",
    },
    "warn_no_cost_col": {
        "en": "No Cost_Per_Unit column: using the default COGS for all rows.",
        "tr": "Cost_Per_Unit sütunu yok: tüm satırlar için varsayılan SMM kullanılıyor.",
        "de": "Keine Spalte Cost_Per_Unit: Für alle Zeilen werden die Standard-Stückkosten verwendet.",
    },
    "warn_cost_filled": {
        "en": "{n} missing Cost_Per_Unit values filled with the default COGS.",
        "tr": "Eksik {n} Cost_Per_Unit değeri varsayılan SMM ile dolduruldu.",
        "de": "{n} fehlende Cost_Per_Unit-Werte mit den Standard-Stückkosten aufgefüllt.",
    },
    "warn_comp_empty": {
        "en": "Competitor_Price column is empty: competitor effects disabled.",
        "tr": "Competitor_Price sütunu boş: rakip etkileri devre dışı.",
        "de": "Spalte Competitor_Price ist leer: Konkurrenzeffekte deaktiviert.",
    },
    "err_too_few_months": {
        "en": "Only {n} month(s) of data: at least {min_n} are needed to fit demand.",
        "tr": "Yalnızca {n} aylık veri var: talebi tahmin etmek için en az {min_n} ay gerekir.",
        "de": "Nur {n} Monat(e) an Daten: Für die Nachfrageschätzung sind mindestens {min_n} nötig.",
    },
    "warn_few_months": {
        "en": "Only {n} months of data: the demand estimate will be unreliable ({min_n}+ recommended).",
        "tr": "Yalnızca {n} aylık veri var: talep tahmini güvenilir olmayacak ({min_n}+ ay önerilir).",
        "de": "Nur {n} Monate an Daten: Die Nachfrageschätzung wird unzuverlässig sein ({min_n}+ empfohlen).",
    },
    "err_price_constant": {
        "en": "Price never varies in the data, so demand response to price cannot be estimated.",
        "tr": "Verilerde fiyat hiç değişmiyor; bu nedenle talebin fiyata tepkisi tahmin edilemez.",
        "de": "Der Preis ändert sich in den Daten nie, daher lässt sich die Preisreaktion der Nachfrage nicht schätzen.",
    },
    "warn_cpi_unavailable": {
        "en": "CPI data unavailable: demand fitted on nominal prices.",
        "tr": "TÜFE verisi alınamadı: talep nominal fiyatlarla tahmin edildi.",
        "de": "VPI-Daten nicht verfügbar: Nachfrage auf Basis nominaler Preise geschätzt.",
    },
    "warn_loglog_dropped": {
        "en": "{n_dropped} of {total} periods dropped (zero sales) for the log-log fit.",
        "tr": "Log-log tahmini için {total} dönemden {n_dropped} tanesi çıkarıldı (sıfır satış).",
        "de": "{n_dropped} von {total} Perioden für die Log-Log-Schätzung entfernt (keine Verkäufe).",
    },
    "err_not_enough_periods": {
        "en": "Not enough usable periods ({n}) to fit a {kind} demand model.",
        "tr": "{kind} talep modeli için yeterli kullanılabilir dönem yok ({n}).",
        "de": "Nicht genügend nutzbare Perioden ({n}) für ein {kind}-Nachfragemodell.",
    },
    "warn_upward_slope": {
        "en": "Fitted demand slopes upward (higher price → more sales). The data can't identify the price "
              "effect, likely because price changes coincided with other demand drivers. Treat the optimum with caution.",
        "tr": "Tahmini talep eğrisi yukarı eğimli (daha yüksek fiyat → daha fazla satış). Veriler fiyat etkisini "
              "ayırt edemiyor; büyük olasılıkla fiyat değişiklikleri başka talep etkenleriyle aynı zamana denk geldi. "
              "Optimum fiyatı temkinle değerlendirin.",
        "de": "Die geschätzte Nachfrage steigt mit dem Preis (höherer Preis → mehr Absatz). Die Daten können den "
              "Preiseffekt nicht identifizieren, vermutlich weil Preisänderungen mit anderen Nachfragetreibern "
              "zusammenfielen. Das Optimum mit Vorsicht behandeln.",
    },
    "warn_inelastic": {
        "en": "Demand is inelastic (elasticity {b:.2f} > -1): under a constant-elasticity model profit keeps "
              "rising with price, so the optimum will sit at the top of the search range.",
        "tr": "Talep esnek değil (esneklik {b:.2f} > -1): sabit esneklik modelinde kâr fiyatla birlikte artmaya "
              "devam eder, bu yüzden optimum arama aralığının en üstünde çıkar.",
        "de": "Die Nachfrage ist unelastisch (Elastizität {b:.2f} > -1): Bei konstanter Elastizität steigt der "
              "Gewinn mit dem Preis immer weiter, daher liegt das Optimum am oberen Rand des Suchbereichs.",
    },
    "warn_opt_at_top": {
        "en": "The optimum is at the top of the price search range. Raise 'Max price to test' or treat it as unbounded.",
        "tr": "Optimum, fiyat arama aralığının en üstünde. 'Denenecek en yüksek fiyat' değerini artırın veya "
              "sonucu sınırsız kabul edin.",
        "de": "Das Optimum liegt am oberen Rand des Suchbereichs. Erhöhen Sie „Höchster Testpreis“ oder betrachten "
              "Sie es als unbegrenzt.",
    },
    "warn_extrapolated": {
        "en": "Optimal price is outside the historically observed range ({p_min:,.2f}–{p_max:,.2f}): "
              "the demand curve is being extrapolated.",
        "tr": "Optimum fiyat geçmişte gözlenen aralığın dışında ({p_min:,.2f}–{p_max:,.2f}): talep eğrisi "
              "gözlenen aralığın ötesine uzatılıyor.",
        "de": "Der optimale Preis liegt außerhalb der historisch beobachteten Spanne ({p_min:,.2f}–{p_max:,.2f}): "
              "Die Nachfragekurve wird extrapoliert.",
    },
    "warn_loss_only": {
        "en": "No price makes a profit under this scenario: the optimum only minimises the loss.",
        "tr": "Bu senaryoda hiçbir fiyat kâr getirmiyor: optimum yalnızca zararı en aza indiriyor.",
        "de": "In diesem Szenario ist kein Preis profitabel: Das Optimum minimiert nur den Verlust.",
    },
    "warn_cap_binding": {
        "en": "Capacity is binding at the optimum: more inventory/capacity would raise profit.",
        "tr": "Optimumda kapasite sınırı bağlayıcı: daha fazla stok/kapasite kârı artırır.",
        "de": "Die Kapazität ist im Optimum ausgeschöpft: Mehr Lager/Kapazität würde den Gewinn erhöhen.",
    },
}


def translate(key: str, lang: str = "en", **params) -> str:
    """Render `key` in `lang`, falling back to English, then to the key itself."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry["en"]
    return text.format(**params) if params else text


class Msg(str):
    """A user-facing message: its value is the English text, and it keeps its key and
    parameters so the UI can show it in another language. Pickles cleanly, so it can be
    returned from st.cache_data functions."""

    def __new__(cls, key: str, **params):
        obj = super().__new__(cls, translate(key, "en", **params))
        obj.key, obj.params = key, params
        return obj

    def __getnewargs_ex__(self):
        return (self.key,), self.params


def localize(message, lang: str) -> str:
    """Show a backend message in `lang`; anything that isn't a Msg is returned as text."""
    if isinstance(message, Msg):
        return translate(message.key, lang, **message.params)
    return str(message)
