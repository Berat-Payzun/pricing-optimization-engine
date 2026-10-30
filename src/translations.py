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
    "upload_label": {
        "en": "Sales history (CSV or Excel)",
        "tr": "Satış geçmişi (CSV veya Excel)",
        "de": "Verkaufshistorie (CSV oder Excel)",
    },
    "upload_help": {
        "en": "Columns: Date, Price_Charged, Quantity_Sold; optional Cost_Per_Unit, Competitor_Price, Product, Flag "
              "(stockout or promo, left out of the demand fit). "
              "Turkish and German headers work too (e.g. Tarih, Fiyat, Adet / Datum, Preis, Menge).",
        "tr": "Sütunlar: Date, Price_Charged, Quantity_Sold; isteğe bağlı Cost_Per_Unit, Competitor_Price, Product, Flag "
              "(stok yok veya kampanya; talep modeline katılmaz). "
              "Türkçe ve Almanca başlıklar da kullanılabilir (ör. Tarih, Fiyat, Adet / Datum, Preis, Menge).",
        "de": "Spalten: Date, Price_Charged, Quantity_Sold; optional Cost_Per_Unit, Competitor_Price, Product, Flag "
              "(ausverkauft oder Aktion, nicht in der Nachfrageschätzung). "
              "Deutsche und türkische Spaltennamen funktionieren auch (z. B. Datum, Preis, Menge / Tarih, Fiyat, Adet).",
    },
    "product_label": {"en": "Product", "tr": "Ürün", "de": "Produkt"},
    "product_help": {
        "en": "Your file has a product column: pick the product to analyse.",
        "tr": "Dosyanızda ürün sütunu var: analiz edilecek ürünü seçin.",
        "de": "Ihre Datei hat eine Produktspalte: Wählen Sie das zu analysierende Produkt.",
    },
    "cost_override_label": {
        "en": "Unit cost override ({sym})",
        "tr": "Birim maliyeti elle gir ({sym})",
        "de": "Stückkosten überschreiben ({sym})",
    },
    "cost_override_help": {
        "en": "Replaces the latest Cost_Per_Unit from the data, to test 'what if my unit cost were X?'. 0 = use the data.",
        "tr": "Verideki son Cost_Per_Unit değerinin yerine geçer; 'birim maliyetim X olsaydı?' sorusunu test etmek için. "
              "0 = veriyi kullan.",
        "de": "Ersetzt die letzten Cost_Per_Unit aus den Daten, um „Was wäre, wenn meine Stückkosten X wären?“ zu testen. "
              "0 = Daten verwenden.",
    },
    "season_label": {"en": "Adjust for seasonality", "tr": "Mevsimselliğe göre düzelt", "de": "Saisonbereinigung"},
    "season_help": {
        "en": "Adds month-of-year effects to the demand fit, so seasonal swings (e.g. a December peak) aren't "
              "mistaken for price effects. On by default with {min_n}+ months of data.",
        "tr": "Talep modeline ay etkileri ekler; böylece mevsimsel dalgalanmalar (ör. Aralık zirvesi) fiyat etkisi "
              "sanılmaz. {min_n}+ aylık veri varsa varsayılan olarak açıktır.",
        "de": "Ergänzt das Nachfragemodell um Monatseffekte, damit saisonale Schwankungen (z. B. ein Dezember-Hoch) "
              "nicht als Preiseffekte gelten. Ab {min_n} Monaten Daten standardmäßig aktiv.",
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
        "en": "What if the next 12 months look like the last 12? Defaults come from live data: 12-month CPI "
              "inflation and the 12-month change in the local-currency/USD rate. The recommendation above is "
              "for today and does not move with these sliders.",
        "tr": "Önümüzdeki 12 ay son 12 ay gibi geçerse ne olur? Varsayılan değerler canlı veriden gelir: 12 aylık "
              "TÜFE enflasyonu ve yerel para/USD kurundaki 12 aylık değişim. Yukarıdaki öneri bugün içindir ve bu "
              "kaydırıcılarla değişmez.",
        "de": "Was, wenn die nächsten 12 Monate wie die letzten 12 verlaufen? Die Standardwerte stammen aus Live-Daten: "
              "12-Monats-Inflation (VPI) und die 12-Monats-Veränderung des Kurses Landeswährung/USD. Die Empfehlung "
              "oben gilt für heute und ändert sich mit diesen Reglern nicht.",
    },
    "shock_infl": {"en": "Country inflation rate (%)", "tr": "Ülke enflasyon oranı (%)", "de": "Inflationsrate des Landes (%)"},
    "shock_infl_help": {
        "en": "Raises fixed costs and the locally sourced share of COGS. With price pass-through on, it also "
              "raises customers' willingness to pay and the competitor's price.",
        "tr": "Sabit giderleri ve SMM'nin yerel kaynaklı kısmını artırır. Fiyat yansıtma açıksa müşterilerin "
              "ödemeye razı olduğu fiyatı ve rakip fiyatını da artırır.",
        "de": "Erhöht die Fixkosten und den lokal bezogenen Anteil der Stückkosten. Bei aktivierter "
              "Preisweitergabe steigen auch die Zahlungsbereitschaft der Kunden und der Konkurrenzpreis.",
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
    "shock_passthrough": {
        "en": "Customer prices rise with inflation",
        "tr": "Müşteri fiyatları enflasyonla birlikte artar",
        "de": "Kundenpreise steigen mit der Inflation",
    },
    "shock_passthrough_help": {
        "en": "On: inflation lifts the whole price level, so willingness to pay and the competitor's price rise "
              "with it and your price can keep pace. Off: only your costs rise (a margin squeeze where you "
              "can't pass costs on).",
        "tr": "Açık: enflasyon genel fiyat düzeyini yükseltir; müşterilerin ödemeye razı olduğu fiyat ve rakip "
              "fiyatı da artar, fiyatınız enflasyona ayak uydurabilir. Kapalı: yalnızca maliyetleriniz artar "
              "(maliyetleri fiyata yansıtamadığınız bir marj sıkışması).",
        "de": "An: Die Inflation hebt das gesamte Preisniveau, Zahlungsbereitschaft und Konkurrenzpreis steigen "
              "mit, und Ihr Preis kann Schritt halten. Aus: Nur Ihre Kosten steigen (Margendruck, weil Sie "
              "die Kosten nicht weitergeben können).",
    },
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
    "metric_profit": {"en": "Net profit ({per})", "tr": "Net kâr ({per})", "de": "Nettogewinn ({per})"},
    "metric_profit_help": {
        "en": "Profit at the recommended price. Delta vs keeping the current price ({profit}).",
        "tr": "Önerilen fiyattaki kâr. Mevcut fiyatı korumaya göre fark ({profit}).",
        "de": "Gewinn zum empfohlenen Preis. Differenz zur Beibehaltung des aktuellen Preises ({profit}).",
    },
    "metric_ped": {"en": "Price elasticity at recommended price", "tr": "Önerilen fiyatta fiyat esnekliği",
                   "de": "Preiselastizität beim empfohlenen Preis"},
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
    "metric_backtest": {"en": "Forecast error (backtest)", "tr": "Tahmin hatası (geriye dönük test)", "de": "Prognosefehler (Backtest)"},
    "metric_backtest_help": {
        "en": "Each of the last {n} months was forecast by a model fitted only on the months before it, at the price "
              "actually charged. The number is the average miss as a share of actual sales (WAPE). Unlike R², it "
              "measures how well the model predicts months it has not seen.",
        "tr": "Son {n} ayın her biri, yalnızca kendisinden önceki aylarla kurulan bir modelle, gerçekte uygulanan "
              "fiyattan tahmin edildi. Sayı, ortalama sapmanın gerçek satışlara oranıdır (WAPE). R²'den farklı olarak "
              "modelin görmediği ayları ne kadar iyi tahmin ettiğini ölçer.",
        "de": "Jeder der letzten {n} Monate wurde mit einem Modell prognostiziert, das nur auf den Monaten davor "
              "geschätzt wurde, zum tatsächlich verlangten Preis. Die Zahl ist die durchschnittliche Abweichung als "
              "Anteil am tatsächlichen Absatz (WAPE). Anders als R² misst sie, wie gut das Modell ungesehene Monate "
              "vorhersagt.",
    },
    "badge_bt_good": {"en": "Good · naive {naive}", "tr": "İyi · basit tahmin {naive}", "de": "Gut · naiv {naive}"},
    "badge_bt_ok": {"en": "Fair · naive {naive}", "tr": "Orta · basit tahmin {naive}", "de": "Mittel · naiv {naive}"},
    "badge_bt_poor": {
        "en": "No better than last month's sales ({naive})",
        "tr": "Geçen ayın satışından iyi değil ({naive})",
        "de": "Nicht besser als der Vormonatsabsatz ({naive})",
    },
    "caption_r2_insample": {
        "en": "In-sample fit: not enough months for a backtest.",
        "tr": "Örneklem içi uyum: geriye dönük test için yeterli ay yok.",
        "de": "Anpassung in der Stichprobe: zu wenige Monate für einen Backtest.",
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
    "chart_excluded": {
        "en": "Excluded (stockout/promo)",
        "tr": "Hariç tutuldu (stok yok/kampanya)",
        "de": "Ausgelassen (ausverkauft/Aktion)",
    },
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
    "col_backtest": {"en": "Backtest error", "tr": "Test hatası", "de": "Backtest-Fehler"},
    "col_naive": {"en": "Naive error", "tr": "Basit tahmin hatası", "de": "Naiver Fehler"},
    "col_month": {"en": "Month", "tr": "Ay", "de": "Monat"},
    "chart_backtest_title": {
        "en": "Backtest: forecast vs actual, last {n} months (monthly units)",
        "tr": "Geriye dönük test: tahmin ve gerçekleşen, son {n} ay (aylık adet)",
        "de": "Backtest: Prognose vs. Ist, letzte {n} Monate (Stück pro Monat)",
    },
    "chart_actual": {"en": "Actual", "tr": "Gerçekleşen", "de": "Ist"},
    "chart_forecast": {"en": "Model forecast", "tr": "Model tahmini", "de": "Modellprognose"},
    "chart_naive": {"en": "Naive (last month)", "tr": "Basit (geçen ay)", "de": "Naiv (Vormonat)"},
    "sheet_backtest": {"en": "Backtest", "tr": "Geriye dönük test", "de": "Backtest"},
    "sum_backtest_value": {
        "en": "{wape:.1f}% (naive {naive:.1f}%, last {n} months)",
        "tr": "%{wape:.1f} (basit tahmin %{naive:.1f}, son {n} ay)",
        "de": "{wape:.1f} % (naiv {naive:.1f} %, letzte {n} Monate)",
    },
    "col_coef": {"en": "Own-price coef", "tr": "Öz fiyat katsayısı", "de": "Eigenpreis-Koeffizient"},
    "details_ped_current": {
        "en": "Elasticity at current price: **{value}**",
        "tr": "Mevcut fiyatta esneklik: **{value}**",
        "de": "Elastizität beim aktuellen Preis: **{value}**",
    },
    "details_xed": {
        "en": "Cross-price elasticity at recommended price: **{value}**",
        "tr": "Önerilen fiyatta çapraz fiyat esnekliği: **{value}**",
        "de": "Kreuzpreiselastizität beim empfohlenen Preis: **{value}**",
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
    # ---------- uncertainty range ----------
    "metric_opt_range": {"en": "90% range: {low} – {high}", "tr": "%90 aralık: {low} – {high}", "de": "90%-Bereich: {low} – {high}"},
    "metric_opt_range_help": {
        "en": "Bootstrap: the demand model was refitted on {n} resampled versions of your history, and 90% of the "
              "resulting optimal prices fell in this range. A wide range means the data pins the price down only weakly.",
        "tr": "Bootstrap: talep modeli geçmiş verinizin yeniden örneklenmiş {n} versiyonuyla tekrar kuruldu; çıkan "
              "optimum fiyatların %90'ı bu aralıkta. Geniş bir aralık, verinin fiyatı zayıf belirlediği anlamına gelir.",
        "de": "Bootstrap: Das Nachfragemodell wurde auf {n} neu gezogenen Versionen Ihrer Historie geschätzt; 90 % der "
              "optimalen Preise lagen in diesem Bereich. Ein breiter Bereich heißt, dass die Daten den Preis nur "
              "schwach festlegen.",
    },
    "chart_range": {"en": "90% range", "tr": "%90 aralık", "de": "90%-Bereich"},
    # ---------- export ----------
    "export_header": {"en": "Export", "tr": "Dışa aktar", "de": "Export"},
    "export_caption": {
        "en": "Results for the current settings: today's recommendation first, then the 12-month scenario.",
        "tr": "Mevcut ayarlara göre sonuçlar: önce bugünkü öneri, ardından 12 aylık senaryo.",
        "de": "Ergebnisse für die aktuellen Einstellungen: zuerst die heutige Empfehlung, dann das 12-Monats-Szenario.",
    },
    "export_excel": {"en": "Download Excel", "tr": "Excel'i indir", "de": "Excel herunterladen"},
    "export_pdf": {"en": "Download PDF summary", "tr": "PDF özetini indir", "de": "PDF-Zusammenfassung herunterladen"},
    "sheet_summary": {"en": "Summary", "tr": "Özet", "de": "Zusammenfassung"},
    "sheet_curve": {"en": "Profit curve", "tr": "Kâr eğrisi", "de": "Gewinnkurve"},
    "sheet_monthly": {"en": "Monthly data", "tr": "Aylık veri", "de": "Monatsdaten"},
    "sheet_models": {"en": "Models", "tr": "Modeller", "de": "Modelle"},
    "sum_item": {"en": "Item", "tr": "Kalem", "de": "Position"},
    "sum_value": {"en": "Value", "tr": "Değer", "de": "Wert"},
    "sum_current_price": {"en": "Current price", "tr": "Mevcut fiyat", "de": "Aktueller Preis"},
    "sum_profit_current": {
        "en": "Profit at current price ({per})",
        "tr": "Mevcut fiyatta kâr ({per})",
        "de": "Gewinn zum aktuellen Preis ({per})",
    },
    "sum_unit_cost": {"en": "Unit cost under scenario", "tr": "Senaryodaki birim maliyet", "de": "Stückkosten im Szenario"},
    "sum_fixed": {"en": "Fixed costs ({per})", "tr": "Sabit giderler ({per})", "de": "Fixkosten ({per})"},
    "sum_break_even": {"en": "Break-even price(s)", "tr": "Başabaş fiyat(lar)ı", "de": "Break-even-Preis(e)"},
    "sum_range": {"en": "90% range of optimal price", "tr": "Optimum fiyatın %90 aralığı", "de": "90%-Bereich des optimalen Preises"},
    "sum_equation": {"en": "Fitted demand", "tr": "Tahmini talep", "de": "Geschätzte Nachfrage"},
    "sum_on": {"en": "On", "tr": "Açık", "de": "An"},
    "sum_off": {"en": "Off", "tr": "Kapalı", "de": "Aus"},
    "sum_none": {"en": "none", "tr": "yok", "de": "keine"},
    "col_price": {"en": "Price", "tr": "Fiyat", "de": "Preis"},
    "col_q_demand": {"en": "Units demanded", "tr": "Talep edilen adet", "de": "Nachgefragte Stück"},
    "col_q_sold": {"en": "Units sold", "tr": "Satılan adet", "de": "Verkaufte Stück"},
    "col_cap_binding": {"en": "Capacity binding", "tr": "Kapasite sınırında", "de": "Kapazität ausgeschöpft"},
    "pdf_notes": {"en": "Warnings and data notes", "tr": "Uyarılar ve veri notları", "de": "Warnungen und Datenhinweise"},
    "pdf_footer": {
        "en": "Generated {date} with the Pricing Optimization Engine",
        "tr": "{date} tarihinde Fiyat Optimizasyon Motoru ile oluşturuldu",
        "de": "Erstellt am {date} mit der Preisoptimierungs-Engine",
    },
    # ---------- duplicates ----------
    "dupes_label": {"en": "Remove duplicate rows", "tr": "Tekrarlanan satırları kaldır", "de": "Doppelte Zeilen entfernen"},
    "dupes_help": {
        "en": "Drops rows that are identical in every column, which usually come from combining overlapping "
              "exports. Turn off for transaction logs where two identical sales on one day are real.",
        "tr": "Tüm sütunlarda aynı olan satırları çıkarır; bunlar genellikle çakışan dışa aktarımların "
              "birleştirilmesinden gelir. Aynı gün iki özdeş satışın gerçek olduğu işlem kayıtlarında kapatın.",
        "de": "Entfernt Zeilen, die in allen Spalten gleich sind – meist Folge zusammengeführter, überlappender "
              "Exporte. Für Transaktionsprotokolle ausschalten, in denen zwei gleiche Verkäufe am selben Tag echt sind.",
    },
    # ---------- fees and taxes ----------
    "fees_header": {"en": "Fees & taxes", "tr": "Kesintiler ve vergiler", "de": "Gebühren & Steuern"},
    "commission_label": {"en": "Marketplace commission (%)", "tr": "Pazaryeri komisyonu (%)", "de": "Marktplatzprovision (%)"},
    "commission_help": {
        "en": "Share of the selling price the marketplace keeps (e.g. Trendyol, Amazon: often 15–25%).",
        "tr": "Pazaryerinin satış fiyatından aldığı pay (ör. Trendyol, Amazon: çoğunlukla %15–25).",
        "de": "Anteil am Verkaufspreis, den der Marktplatz einbehält (z. B. Amazon: oft 15–25 %).",
    },
    "payment_fee_label": {"en": "Payment fee (%)", "tr": "Ödeme komisyonu (%)", "de": "Zahlungsgebühr (%)"},
    "payment_fee_help": {
        "en": "Card or payment-provider fee as a share of the selling price.",
        "tr": "Satış fiyatının yüzdesi olarak kart veya ödeme kuruluşu komisyonu.",
        "de": "Karten- oder Zahlungsanbietergebühr als Anteil am Verkaufspreis.",
    },
    "vat_toggle": {"en": "Uploaded prices include VAT", "tr": "Yüklenen fiyatlara KDV dahil", "de": "Hochgeladene Preise enthalten MwSt."},
    "vat_toggle_help": {
        "en": "Turn on if your prices are what customers pay including VAT. The VAT part is then not counted as "
              "your revenue.",
        "tr": "Fiyatlarınız müşterinin KDV dahil ödediği tutarsa açın. KDV kısmı gelirinizden sayılmaz.",
        "de": "Einschalten, wenn Ihre Preise Endkundenpreise inklusive MwSt. sind. Der MwSt.-Anteil zählt dann "
              "nicht zu Ihrem Umsatz.",
    },
    "vat_label": {"en": "VAT rate (%)", "tr": "KDV oranı (%)", "de": "MwSt.-Satz (%)"},
    "vat_help": {
        "en": "Prefilled with the country's standard rate. Change it for reduced rates.",
        "tr": "Ülkenin standart oranıyla doldurulur. İndirimli oranlar için değiştirin.",
        "de": "Mit dem Regelsatz des Landes vorbelegt. Für ermäßigte Sätze anpassen.",
    },
    "extra_cost_label": {
        "en": "Extra cost per unit ({sym})",
        "tr": "Birim başına ek maliyet ({sym})",
        "de": "Zusatzkosten pro Stück ({sym})",
    },
    "extra_cost_help": {
        "en": "Shipping, packaging and other per-unit costs not in Cost_Per_Unit. Treated as local costs, so "
              "they rise with inflation in the scenario.",
        "tr": "Cost_Per_Unit içinde olmayan kargo, ambalaj ve diğer birim maliyetler. Yerel maliyet sayılır, "
              "senaryoda enflasyonla artar.",
        "de": "Versand, Verpackung und andere Stückkosten, die nicht in Cost_Per_Unit stecken. Gelten als lokale "
              "Kosten und steigen im Szenario mit der Inflation.",
    },
    # ---------- guardrails ----------
    "rails_header": {"en": "Guardrails", "tr": "Fiyat kuralları", "de": "Preisregeln"},
    "max_change_label": {
        "en": "Max change from current price (%)",
        "tr": "Mevcut fiyattan en fazla değişim (%)",
        "de": "Max. Änderung ggü. aktuellem Preis (%)",
    },
    "max_change_help": {
        "en": "Largest step up or down the recommendation may take in one go. 0 = no limit.",
        "tr": "Önerinin tek seferde yapabileceği en büyük artış veya indirim. 0 = sınır yok.",
        "de": "Größter Schritt nach oben oder unten, den die Empfehlung auf einmal machen darf. 0 = keine Grenze.",
    },
    "min_margin_label": {"en": "Min margin per unit (%)", "tr": "Birim başına asgari marj (%)", "de": "Mindestmarge pro Stück (%)"},
    "min_margin_help": {
        "en": "Net operating margin per unit (after VAT, fees and unit costs) as a share of the net price. 0 = off.",
        "tr": "Net fiyatın yüzdesi olarak birim başına net faaliyet marjı (KDV, kesintiler ve birim maliyetlerden "
              "sonra). 0 = kapalı.",
        "de": "Netto-Betriebsmarge pro Stück (nach MwSt., Gebühren und Stückkosten) als Anteil am Nettopreis. 0 = aus.",
    },
    "floor_label": {"en": "Price floor ({sym})", "tr": "Taban fiyat ({sym})", "de": "Preisuntergrenze ({sym})"},
    "ceiling_label": {"en": "Price ceiling ({sym})", "tr": "Tavan fiyat ({sym})", "de": "Preisobergrenze ({sym})"},
    "floor_ceiling_help": {"en": "0 = no limit.", "tr": "0 = sınır yok.", "de": "0 = keine Grenze."},
    "ending_label": {"en": "Price ending", "tr": "Fiyat sonu", "de": "Preisendung"},
    "ending_help": {
        "en": "Round the recommendation to a price point, picking the more profitable one below or above.",
        "tr": "Öneriyi bir fiyat noktasına yuvarlar; alttaki ve üstteki noktadan daha kârlı olanı seçer.",
        "de": "Rundet die Empfehlung auf einen Preispunkt und wählt den profitableren darunter oder darüber.",
    },
    "ending_none": {"en": "No rounding", "tr": "Yuvarlama yok", "de": "Keine Rundung"},
    "ending_99": {"en": "x.99", "tr": "x,99", "de": "x,99"},
    "ending_90": {"en": "x.90", "tr": "x,90", "de": "x,90"},
    "ending_whole": {"en": "Whole number", "tr": "Tam sayı", "de": "Ganze Zahl"},
    "limit_max_change": {"en": "max change", "tr": "en fazla değişim", "de": "max. Änderung"},
    "limit_min_margin": {"en": "min margin", "tr": "asgari marj", "de": "Mindestmarge"},
    "limit_floor": {"en": "price floor", "tr": "taban fiyat", "de": "Preisuntergrenze"},
    "limit_ceiling": {"en": "price ceiling", "tr": "tavan fiyat", "de": "Preisobergrenze"},
    # ---------- headline recommendation ----------
    "metric_rec_price": {"en": "Recommended price (today)", "tr": "Önerilen fiyat (bugün)", "de": "Empfohlener Preis (heute)"},
    "metric_rec_help": {
        "en": "Most profitable price at today's costs and price level ({month} money), within your guardrails. "
              "No inflation or exchange-rate shock is applied: see the scenario below for that. Current price: {price}.",
        "tr": "Bugünkü maliyetler ve fiyat düzeyinde ({month} parasıyla), fiyat kurallarınız içinde en kârlı fiyat. "
              "Enflasyon veya kur şoku uygulanmaz: bunun için aşağıdaki senaryoya bakın. Mevcut fiyat: {price}.",
        "de": "Profitabelster Preis bei heutigen Kosten und heutigem Preisniveau (Geld von {month}) innerhalb Ihrer "
              "Preisregeln. Ohne Inflations- oder Wechselkursschock – siehe dazu das Szenario unten. Aktueller Preis: {price}.",
    },
    "caption_unconstrained": {
        "en": "Unconstrained optimum: {price} · limited by {limits}",
        "tr": "Kısıtsız optimum: {price} · sınırlayan: {limits}",
        "de": "Optimum ohne Regeln: {price} · begrenzt durch {limits}",
    },
    "caption_unrounded": {"en": "Before rounding: {price}", "tr": "Yuvarlamadan önce: {price}", "de": "Vor Rundung: {price}"},
    "chart_recommended": {"en": "Recommended {price}", "tr": "Önerilen {price}", "de": "Empfohlen {price}"},
    "chart_unconstrained": {"en": "Unconstrained {price}", "tr": "Kısıtsız {price}", "de": "Ohne Regeln {price}"},
    # ---------- unit economics breakdown ----------
    "breakdown_expander": {
        "en": "Unit economics & tax breakdown",
        "tr": "Birim ekonomisi ve vergi dökümü",
        "de": "Stückökonomie & Steueraufschlüsselung",
    },
    "breakdown_title": {
        "en": "Where each unit's price goes at {price}",
        "tr": "{price} fiyatında her birimin fiyatı nereye gidiyor",
        "de": "Wohin der Preis jedes Stücks bei {price} geht",
    },
    "breakdown_price": {"en": "Headline price", "tr": "Satış fiyatı", "de": "Verkaufspreis"},
    "breakdown_vat": {"en": "VAT", "tr": "KDV", "de": "MwSt."},
    "breakdown_commission": {"en": "Marketplace commission", "tr": "Pazaryeri komisyonu", "de": "Marktplatzprovision"},
    "breakdown_payment": {"en": "Payment fee", "tr": "Ödeme komisyonu", "de": "Zahlungsgebühr"},
    "breakdown_cogs": {"en": "Unit cost (COGS)", "tr": "Birim maliyet (SMM)", "de": "Stückkosten"},
    "breakdown_extra": {"en": "Extra unit cost", "tr": "Ek birim maliyet", "de": "Zusatzkosten"},
    "breakdown_margin": {"en": "Net operating margin", "tr": "Net faaliyet marjı", "de": "Netto-Betriebsmarge"},
    "col_item": {"en": "Item", "tr": "Kalem", "de": "Position"},
    "col_per_unit": {"en": "Per unit", "tr": "Birim başına", "de": "Pro Stück"},
    "col_share": {"en": "% of price", "tr": "Fiyatın %'si", "de": "% vom Preis"},
    "breakdown_caption": {
        "en": "At this price you sell {units} units {per}: {contribution} margin minus {fixed} fixed costs = "
              "{profit} net profit.",
        "tr": "Bu fiyatta {per} {units} adet satarsınız: {contribution} marj eksi {fixed} sabit gider = "
              "{profit} net kâr.",
        "de": "Zu diesem Preis verkaufen Sie {units} Stück {per}: {contribution} Marge minus {fixed} Fixkosten = "
              "{profit} Nettogewinn.",
    },
    # ---------- scenario ----------
    "scenario_opt_label": {
        "en": "Scenario optimum (prices of {month})",
        "tr": "Senaryo optimumu ({month} fiyatlarıyla)",
        "de": "Szenario-Optimum (Preise von {month})",
    },
    "scenario_opt_delta": {"en": "{pct:+.1f}% vs recommended", "tr": "{pct:+.1f}% (önerilen fiyata göre)", "de": "{pct:+.1f}% ggü. Empfehlung"},
    "scenario_opt_help": {
        "en": "Most profitable price if the inflation, exchange-rate and competitor changes above play out over "
              "the next 12 months, in the nominal money of {month}. Guardrails are not applied.",
        "tr": "Yukarıdaki enflasyon, kur ve rakip değişimleri önümüzdeki 12 ayda gerçekleşirse en kârlı fiyat; "
              "{month} nominal parasıyla. Fiyat kuralları uygulanmaz.",
        "de": "Profitabelster Preis, wenn die obigen Inflations-, Wechselkurs- und Konkurrenzänderungen in den "
              "nächsten 12 Monaten eintreten, in nominalem Geld von {month}. Preisregeln werden nicht angewendet.",
    },
    "scenario_profit_label": {"en": "Scenario peak profit ({per})", "tr": "Senaryo zirve kârı ({per})", "de": "Szenario-Maximalgewinn ({per})"},
    "scenario_cogs_label": {"en": "Scenario unit cost", "tr": "Senaryo birim maliyeti", "de": "Szenario-Stückkosten"},
    # ---------- price test plan ----------
    "test_header": {"en": "Price test plan", "tr": "Fiyat testi planı", "de": "Preistest-Plan"},
    "test_caption": {
        "en": "The demand curve is estimated from your own price history, so it can be biased. A short controlled "
              "test checks it: alternate two prices week by week, so seasons and trends affect both alike, then "
              "enter the weekly units sold below.",
        "tr": "Talep eğrisi kendi fiyat geçmişinizden tahmin edildiği için yanlı olabilir. Kısa ve kontrollü bir "
              "test bunu sınar: iki fiyatı haftadan haftaya dönüşümlü uygulayın (böylece mevsim ve eğilimler ikisini "
              "de aynı etkiler), ardından haftalık satış adetlerini aşağıya girin.",
        "de": "Die Nachfragekurve wird aus Ihrer eigenen Preishistorie geschätzt und kann daher verzerrt sein. Ein "
              "kurzer, kontrollierter Test prüft sie: Wechseln Sie Woche für Woche zwischen zwei Preisen, damit "
              "Saison und Trend beide gleich treffen, und tragen Sie unten die wöchentlich verkauften Stück ein.",
    },
    "test_summary": {
        "en": "Run **{weeks} weeks**: {half} at the test price **{test}** and {half} at the current price "
              "**{current}**, alternating. Expected: about **{exp_test}** vs **{exp_current}** {units} per week.",
        "tr": "**{weeks} hafta** uygulayın: dönüşümlü olarak {half} hafta test fiyatı **{test}**, {half} hafta mevcut "
              "fiyat **{current}**. Beklenen: haftada yaklaşık **{exp_test}** ve **{exp_current}** {units}.",
        "de": "**{weeks} Wochen** durchführen: abwechselnd {half} zum Testpreis **{test}** und {half} zum aktuellen "
              "Preis **{current}**. Erwartet: etwa **{exp_test}** vs. **{exp_current}** {units} pro Woche.",
    },
    "test_step_label": {"en": "Test price step (%)", "tr": "Test fiyat adımı (%)", "de": "Testpreis-Schritt (%)"},
    "test_step_help": {
        "en": "How far the test price is from the current price, in the direction the model says is more "
              "profitable. A bigger step is easier to detect, so the test is shorter, but more sales are at stake "
              "if the model is wrong. Changing it starts a new plan.",
        "tr": "Test fiyatının mevcut fiyattan ne kadar uzak olduğu; modelin daha kârlı dediği yönde. Büyük bir adım "
              "daha kolay fark edilir ve test kısalır, ancak model yanılıyorsa daha fazla satış riske girer. "
              "Değiştirmek yeni bir plan başlatır.",
        "de": "Wie weit der Testpreis vom aktuellen Preis entfernt ist, in die Richtung, die laut Modell "
              "profitabler ist. Ein größerer Schritt ist leichter zu erkennen und verkürzt den Test, setzt aber "
              "mehr Absatz aufs Spiel, falls das Modell irrt. Eine Änderung startet einen neuen Plan.",
    },
    "test_weeks_metric": {"en": "Weeks needed", "tr": "Gereken hafta", "de": "Benötigte Wochen"},
    "test_weeks_help": {
        "en": "Total weeks (both prices) to detect the expected sales difference with 80% power at 90% confidence, "
              "given your sales' normal week-to-week variation. The plan is capped at {max_weeks} weeks.",
        "tr": "Satışlarınızın olağan haftalık değişkenliği göz önüne alındığında, beklenen satış farkını %90 güvenle "
              "ve %80 güçle saptamak için gereken toplam hafta (her iki fiyat). Plan en fazla {max_weeks} haftadır.",
        "de": "Wochen insgesamt (beide Preise), um den erwarteten Absatzunterschied bei normaler wöchentlicher "
              "Schwankung mit 80 % Trennschärfe und 90 % Konfidenz zu erkennen. Der Plan ist auf {max_weeks} "
              "Wochen begrenzt.",
    },
    "test_noise_caption": {
        "en": "Normal weekly swing ±{sd} {units}; expected difference between the prices {diff} {units} per week.",
        "tr": "Olağan haftalık dalgalanma ±{sd} {units}; fiyatlar arasındaki beklenen fark haftada {diff} {units}.",
        "de": "Normale Wochenschwankung ±{sd} {units}; erwarteter Unterschied zwischen den Preisen {diff} {units} "
              "pro Woche.",
    },
    "test_chart_title": {
        "en": "Bigger step, shorter test",
        "tr": "Daha büyük adım, daha kısa test",
        "de": "Größerer Schritt, kürzerer Test",
    },
    "test_chart_x": {"en": "Test price step", "tr": "Test fiyat adımı", "de": "Testpreis-Schritt"},
    "test_chart_y": {"en": "Weeks needed (log scale)", "tr": "Gereken hafta (log ölçek)", "de": "Benötigte Wochen (log. Skala)"},
    "test_chart_max": {"en": "max {weeks} weeks", "tr": "en fazla {weeks} hafta", "de": "max. {weeks} Wochen"},
    "test_chart_caption": {
        "en": "The sales difference grows with the step while weekly noise stays the same, so the weeks needed "
              "fall roughly with the square of the step: doubling the step cuts the test to about a quarter.",
        "tr": "Satış farkı adımla birlikte büyürken haftalık gürültü aynı kalır; bu yüzden gereken hafta sayısı "
              "kabaca adımın karesiyle azalır: adımı iki katına çıkarmak testi yaklaşık dörtte birine indirir.",
        "de": "Der Absatzunterschied wächst mit dem Schritt, das Wochenrauschen bleibt gleich. Die benötigten "
              "Wochen sinken daher etwa mit dem Quadrat des Schritts: Ein doppelter Schritt verkürzt den Test auf "
              "etwa ein Viertel.",
    },
    "col_week": {"en": "Week", "tr": "Hafta", "de": "Woche"},
    "col_arm": {"en": "Price group", "tr": "Fiyat grubu", "de": "Preisgruppe"},
    "col_expected": {"en": "Expected units", "tr": "Beklenen adet", "de": "Erwartete Stück"},
    "col_low": {"en": "90% low", "tr": "%90 alt", "de": "90 % unten"},
    "col_high": {"en": "90% high", "tr": "%90 üst", "de": "90 % oben"},
    "col_actual": {"en": "Actual units", "tr": "Gerçekleşen adet", "de": "Tatsächliche Stück"},
    "arm_test": {"en": "Test price", "tr": "Test fiyatı", "de": "Testpreis"},
    "arm_current": {"en": "Current price", "tr": "Mevcut fiyat", "de": "Aktueller Preis"},
    "test_need_more": {
        "en": "Enter actual units for at least two weeks at each price to get a verdict.",
        "tr": "Sonuç için her fiyatta en az iki haftanın gerçekleşen adedini girin.",
        "de": "Für ein Ergebnis mindestens zwei Wochen je Preis mit tatsächlichen Stückzahlen eintragen.",
    },
    "test_verdict_consistent": {
        "en": "Consistent with the model: the test price changed weekly sales by {observed} units (90% range "
              "{low} to {high}); the model expected {expected}. Elasticity observed {e_obs} vs model {e_model}.",
        "tr": "Modelle tutarlı: test fiyatı haftalık satışı {observed} adet değiştirdi (%90 aralık {low} ile {high}); "
              "model {expected} bekliyordu. Gözlenen esneklik {e_obs}, model {e_model}.",
        "de": "Passt zum Modell: Der Testpreis veränderte den Wochenabsatz um {observed} Stück (90 %-Bereich {low} "
              "bis {high}); das Modell erwartete {expected}. Elastizität beobachtet {e_obs} vs. Modell {e_model}.",
    },
    "test_verdict_more_sensitive": {
        "en": "Customers are more price-sensitive than the model thinks: weekly sales changed by {observed} units "
              "(90% range {low} to {high}) where the model expected {expected}. Elasticity observed {e_obs} vs "
              "model {e_model}. Be careful with price rises; add the test weeks to your data and refit.",
        "tr": "Müşteriler fiyata modelin sandığından daha duyarlı: haftalık satış {observed} adet değişti (%90 aralık "
              "{low} ile {high}), model {expected} bekliyordu. Gözlenen esneklik {e_obs}, model {e_model}. Fiyat "
              "artışlarında dikkatli olun; test haftalarını verinize ekleyip modeli yeniden kurun.",
        "de": "Kunden reagieren preisempfindlicher als vom Modell angenommen: Der Wochenabsatz änderte sich um "
              "{observed} Stück (90 %-Bereich {low} bis {high}), erwartet waren {expected}. Elastizität beobachtet "
              "{e_obs} vs. Modell {e_model}. Vorsicht bei Preiserhöhungen; Testwochen in die Daten aufnehmen und "
              "neu schätzen.",
    },
    "test_verdict_less_sensitive": {
        "en": "Customers are less price-sensitive than the model thinks: weekly sales changed by {observed} units "
              "(90% range {low} to {high}) where the model expected {expected}. Elasticity observed {e_obs} vs "
              "model {e_model}. There may be room to price higher; add the test weeks to your data and refit.",
        "tr": "Müşteriler fiyata modelin sandığından daha az duyarlı: haftalık satış {observed} adet değişti (%90 "
              "aralık {low} ile {high}), model {expected} bekliyordu. Gözlenen esneklik {e_obs}, model {e_model}. "
              "Daha yüksek fiyat için alan olabilir; test haftalarını verinize ekleyip modeli yeniden kurun.",
        "de": "Kunden reagieren weniger preisempfindlich als vom Modell angenommen: Der Wochenabsatz änderte sich "
              "um {observed} Stück (90 %-Bereich {low} bis {high}), erwartet waren {expected}. Elastizität "
              "beobachtet {e_obs} vs. Modell {e_model}. Möglicherweise ist ein höherer Preis drin; Testwochen in "
              "die Daten aufnehmen und neu schätzen.",
    },
    "test_level_shift": {
        "en": "Overall sales ran {pct:+.0f}% vs expected at both prices, likely a season or trend shift. The "
              "price comparison above is unaffected because both prices saw it.",
        "tr": "Toplam satışlar her iki fiyatta da beklenene göre {pct:+.0f}% saptı; büyük olasılıkla mevsim veya "
              "eğilim etkisi. Her iki fiyat da bundan etkilendiği için yukarıdaki karşılaştırma geçerlidir.",
        "de": "Der Gesamtabsatz lag bei beiden Preisen {pct:+.0f} % neben der Erwartung, vermutlich Saison oder "
              "Trend. Der Preisvergleich oben bleibt gültig, da beide Preise betroffen waren.",
    },
    "test_not_saved": {
        "en": "Entries are not saved when you close the page. The Excel export has the plan with an empty "
              "Actual column to fill in as the test runs.",
        "tr": "Girdiler sayfayı kapattığınızda kaydedilmez. Excel dışa aktarımında, test sürerken doldurmanız "
              "için boş bir Gerçekleşen sütunuyla plan yer alır.",
        "de": "Eingaben werden beim Schließen der Seite nicht gespeichert. Der Excel-Export enthält den Plan mit "
              "einer leeren Ist-Spalte zum Ausfüllen während des Tests.",
    },
    "sheet_test_plan": {"en": "Test plan", "tr": "Test planı", "de": "Testplan"},
    "sum_test_plan": {"en": "Price test plan", "tr": "Fiyat testi planı", "de": "Preistest-Plan"},
    "sum_test_plan_value": {
        "en": "test {test} for {weeks} weeks (alternating); expected {diff} units/week vs current",
        "tr": "{test} fiyatını {weeks} hafta test edin (dönüşümlü); mevcut fiyata göre beklenen {diff} adet/hafta",
        "de": "{test} {weeks} Wochen testen (abwechselnd); erwartet {diff} Stück/Woche ggü. aktuell",
    },
    # ---------- export summary ----------
    "sum_unconstrained": {"en": "Unconstrained optimum (today)", "tr": "Kısıtsız optimum (bugün)", "de": "Optimum ohne Regeln (heute)"},
    "sum_limits": {"en": "Limited by", "tr": "Sınırlayan", "de": "Begrenzt durch"},
    "sum_guardrails": {"en": "Guardrails", "tr": "Fiyat kuralları", "de": "Preisregeln"},
    "sum_guardrails_value": {
        "en": "max change ±{max_change:.0f}% · min margin {min_margin:.0f}% · floor {floor} · ceiling {ceiling} · {ending}",
        "tr": "en fazla değişim ±%{max_change:.0f} · asgari marj %{min_margin:.0f} · taban {floor} · tavan {ceiling} · {ending}",
        "de": "max. Änderung ±{max_change:.0f} % · Mindestmarge {min_margin:.0f} % · Untergrenze {floor} · "
              "Obergrenze {ceiling} · {ending}",
    },
    "sum_fees": {"en": "Fees & taxes", "tr": "Kesintiler ve vergiler", "de": "Gebühren & Steuern"},
    "sum_fees_value": {
        "en": "commission {commission:.1f}% · payment fee {payment:.1f}% · VAT {vat} · extra unit cost {extra}",
        "tr": "komisyon %{commission:.1f} · ödeme komisyonu %{payment:.1f} · KDV {vat} · ek birim maliyet {extra}",
        "de": "Provision {commission:.1f} % · Zahlungsgebühr {payment:.1f} % · MwSt. {vat} · Zusatzkosten {extra}",
    },
    "vat_included": {"en": "{rate:.1f}% included in prices", "tr": "%{rate:.1f} fiyatlara dahil", "de": "{rate:.1f} % in Preisen enthalten"},
    "vat_excluded": {"en": "not included in prices", "tr": "fiyatlara dahil değil", "de": "nicht in Preisen enthalten"},
    "sum_per_unit": {"en": "Per unit at recommended price", "tr": "Önerilen fiyatta birim başına", "de": "Pro Stück zum empfohlenen Preis"},
    "sum_scenario": {"en": "Scenario (next 12 months)", "tr": "Senaryo (önümüzdeki 12 ay)", "de": "Szenario (nächste 12 Monate)"},
    "sheet_scenario_curve": {"en": "Scenario curve", "tr": "Senaryo eğrisi", "de": "Szenario-Kurve"},
    "col_vat": {"en": "VAT", "tr": "KDV", "de": "MwSt."},
    "col_fees": {"en": "Fees", "tr": "Kesintiler", "de": "Gebühren"},
    "col_margin": {"en": "Margin per unit (%)", "tr": "Birim marj (%)", "de": "Marge pro Stück (%)"},
    # ---------- backend messages (data_ingestion.py, optimizer.py) ----------
    "warn_season_short": {
        "en": "Seasonality needs at least {min_n} months of data ({n} available): fitted without it.",
        "tr": "Mevsimsellik için en az {min_n} aylık veri gerekir ({n} ay mevcut): model mevsimsellik olmadan kuruldu.",
        "de": "Saisonbereinigung braucht mindestens {min_n} Monate Daten ({n} vorhanden): ohne Saison geschätzt.",
    },
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
    "warn_duplicates_dropped": {
        "en": "{n} exact duplicate row(s) removed (often from combining overlapping exports). Turn off "
              "'Remove duplicate rows' if they are real repeat sales.",
        "tr": "{n} birebir tekrarlanan satır çıkarıldı (genellikle çakışan dışa aktarımların birleştirilmesinden). "
              "Bunlar gerçek tekrar satışlarsa 'Tekrarlanan satırları kaldır' seçeneğini kapatın.",
        "de": "{n} exakt doppelte Zeile(n) entfernt (meist durch zusammengeführte, überlappende Exporte). "
              "Schalten Sie „Doppelte Zeilen entfernen“ aus, wenn es echte Wiederholungsverkäufe sind.",
    },
    "warn_duplicates_kept": {
        "en": "{n} exact duplicate row(s) kept and counted as separate sales.",
        "tr": "{n} birebir tekrarlanan satır korundu ve ayrı satışlar olarak sayıldı.",
        "de": "{n} exakt doppelte Zeile(n) beibehalten und als separate Verkäufe gezählt.",
    },
    "warn_fred_no_key": {
        "en": "No FRED API key is set, so FRED inflation/exchange-rate data was not fetched and built-in values "
              "are used. Add FRED_API_KEY to the app's secrets (see README).",
        "tr": "FRED API anahtarı tanımlı değil; FRED enflasyon/kur verisi alınamadı ve yerleşik değerler "
              "kullanılıyor. Uygulamanın gizli ayarlarına FRED_API_KEY ekleyin (README'ye bakın).",
        "de": "Kein FRED-API-Schlüssel gesetzt: FRED-Inflations-/Wechselkursdaten wurden nicht abgerufen, es "
              "gelten eingebaute Werte. FRED_API_KEY in den Secrets der App hinterlegen (siehe README).",
    },
    "warn_flag_unknown": {
        "en": "Unrecognised Flag value(s) treated as normal sales: {values}. Use 'stockout' or 'promo'.",
        "tr": "Tanınmayan Flag değer(ler)i normal satış sayıldı: {values}. 'stok yok' veya 'kampanya' kullanın.",
        "de": "Unbekannte Flag-Werte als normale Verkäufe behandelt: {values}. Verwenden Sie „ausverkauft“ oder "
              "„Aktion“.",
    },
    "warn_flag_scaled": {
        "en": "{n} month(s) had some stockout/promo days: those days were left out and the month's sales scaled "
              "up from its normal days.",
        "tr": "{n} ayda bazı stok yok/kampanya günleri vardı: bu günler çıkarıldı ve ayın satışları normal "
              "günlerinden ölçeklendi.",
        "de": "{n} Monat(e) mit einzelnen Ausverkauft-/Aktionstagen: Diese Tage wurden ausgelassen und der "
              "Monatsabsatz aus den normalen Tagen hochgerechnet.",
    },
    "warn_flag_excluded": {
        "en": "{n} month(s) left out of the demand fit because most days were flagged ({stockout} stockout, "
              "{promo} promo).",
        "tr": "Günlerinin çoğu işaretli olduğu için {n} ay talep modelinin dışında bırakıldı ({stockout} stok yok, "
              "{promo} kampanya).",
        "de": "{n} Monat(e) aus der Nachfrageschätzung ausgelassen, weil die meisten Tage markiert waren "
              "({stockout} ausverkauft, {promo} Aktion).",
    },
    "warn_test_underpowered": {
        "en": "Even {weeks} weeks may not be enough to tell the two prices apart reliably: the expected sales "
              "difference is small compared with normal week-to-week swings. Consider a bigger price step.",
        "tr": "{weeks} hafta bile iki fiyatı güvenilir biçimde ayırt etmeye yetmeyebilir: beklenen satış farkı, "
              "olağan haftalık dalgalanmalara göre küçük. Daha büyük bir fiyat adımı düşünün.",
        "de": "Selbst {weeks} Wochen reichen womöglich nicht, um die beiden Preise sicher zu unterscheiden: Der "
              "erwartete Absatzunterschied ist klein im Vergleich zu normalen Wochenschwankungen. Erwägen Sie "
              "einen größeren Preisschritt.",
    },
    "warn_test_step_clipped": {
        "en": "A {step:.1f}% step goes beyond your guardrails, so the test price is held at {price:,.2f}. Widen "
              "'Max change' or the floor/ceiling to test a bigger step.",
        "tr": "%{step:.1f} adım fiyat kurallarınızın dışına çıkıyor; test fiyatı {price:,.2f} olarak sınırlandı. "
              "Daha büyük bir adımı test etmek için 'En fazla değişim' veya taban/tavan fiyatı genişletin.",
        "de": "Ein Schritt von {step:.1f} % überschreitet Ihre Preisregeln, daher bleibt der Testpreis bei "
              "{price:,.2f}. Erweitern Sie „Max. Änderung“ oder Unter-/Obergrenze, um einen größeren Schritt zu testen.",
    },
    "warn_guardrail_conflict": {
        "en": "The price floor/ceiling lies outside the allowed step from the current price: the max-change "
              "limit was ignored.",
        "tr": "Fiyat tabanı/tavanı, mevcut fiyattan izin verilen değişim aralığının dışında: en fazla değişim "
              "sınırı yok sayıldı.",
        "de": "Preisuntergrenze/-obergrenze liegt außerhalb der erlaubten Änderung ggü. dem aktuellen Preis: "
              "Die maximale Änderung wurde ignoriert.",
    },
    "warn_guardrail_margin": {
        "en": "No price within the allowed range reaches the {margin:.0f}% minimum margin: the most profitable "
              "price in the range is shown instead.",
        "tr": "İzin verilen aralıktaki hiçbir fiyat %{margin:.0f} asgari marja ulaşmıyor: bunun yerine aralıktaki "
              "en kârlı fiyat gösteriliyor.",
        "de": "Kein Preis im erlaubten Bereich erreicht die Mindestmarge von {margin:.0f} %: Stattdessen wird der "
              "profitabelste Preis im Bereich gezeigt.",
    },
    "warn_guardrail_ending": {
        "en": "No price with the chosen ending fits the guardrails: the price is shown unrounded.",
        "tr": "Seçilen fiyat sonuyla kurallara uyan bir fiyat yok: fiyat yuvarlanmadan gösteriliyor.",
        "de": "Kein Preis mit der gewählten Endung erfüllt die Regeln: Der Preis wird ungerundet gezeigt.",
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
