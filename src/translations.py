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
        "en": "Replaces the latest Cost_Per_Unit from the data, to test 'what if my unit cost were X?'. Leave empty to use the data; 0 is a zero unit cost.",
        "tr": "Verideki son Cost_Per_Unit değerinin yerine geçer; 'birim maliyetim X olsaydı?' sorusunu test etmek için. "
              "Veriyi kullanmak için boş bırakın; 0 sıfır birim maliyet demektir.",
        "de": "Ersetzt die letzten Cost_Per_Unit aus den Daten, um „Was wäre, wenn meine Stückkosten X wären?“ zu testen. "
              "Leer lassen, um die Daten zu verwenden; 0 bedeutet Stückkosten von null.",
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
    "trend_label": {"en": "Adjust for growth trend", "tr": "Büyüme eğilimine göre düzelt", "de": "Wachstumstrend bereinigen"},
    "trend_help": {
        "en": "Adds a linear time trend to the demand fit, so steady growth or decline isn't mistaken for a price "
              "effect. Worth turning on with real prices under high inflation, where the real price falls month "
              "after month. Demand is then priced at the latest month's level; the 12-month scenario does not "
              "project the trend forward.",
        "tr": "Talep modeline doğrusal bir zaman eğilimi ekler; böylece istikrarlı büyüme veya düşüş fiyat etkisi "
              "sanılmaz. Reel fiyatlar ve yüksek enflasyonla açılması önerilir; bu durumda reel fiyat her ay düşer. "
              "Talep son ayın düzeyinde fiyatlanır; 12 aylık senaryo eğilimi ileriye taşımaz.",
        "de": "Ergänzt das Nachfragemodell um einen linearen Zeittrend, damit stetiges Wachstum oder ein Rückgang "
              "nicht als Preiseffekt gilt. Empfehlenswert bei realen Preisen und hoher Inflation, wenn der reale "
              "Preis Monat für Monat sinkt. Die Nachfrage wird dann auf dem Niveau des letzten Monats bepreist; das "
              "12-Monats-Szenario schreibt den Trend nicht fort.",
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
        "en": "Upper bound of the price search, in today's money. Default: 2× the highest historical price. "
              "With price pass-through, the scenario searches up to this × its price level.",
        "tr": "Fiyat aramasının bugünkü parayla üst sınırı. Varsayılan: geçmişteki en yüksek fiyatın 2 katı. "
              "Fiyat yansıtma açıkken senaryo bu değerin fiyat seviyesiyle çarpımına kadar arar.",
        "de": "Obergrenze der Preissuche, in heutigem Geld. Standard: 2× der höchste historische Preis. "
              "Mit Preisweitergabe sucht das Szenario bis zu diesem Wert × seinem Preisniveau.",
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
    "shock_usd_infl": {"en": "US inflation on imported costs (%)", "tr": "İthal maliyetlerde ABD enflasyonu (%)",
                       "de": "US-Inflation auf Importkosten (%)"},
    "shock_usd_infl_help": {
        "en": "The share of COGS priced in USD rises with US inflation (as well as the exchange rate). Prefilled "
              "with the latest US CPI ({source}, {as_of}).",
        "tr": "SMM'nin USD cinsinden kısmı ABD enflasyonuyla (ve döviz kuruyla) artar. Son ABD TÜFE değeriyle "
              "doldurulur ({source}, {as_of}).",
        "de": "Der in USD bepreiste Anteil der Stückkosten steigt mit der US-Inflation (und dem Wechselkurs). "
              "Mit dem letzten US-VPI vorbelegt ({source}, {as_of}).",
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
    "metric_opt_range": {"en": "90% range of the optimum: {low} – {high}", "tr": "Optimumun %90 aralığı: {low} – {high}",
                         "de": "90%-Bereich des Optimums: {low} – {high}"},
    "metric_opt_range_help": {
        "en": "Bootstrap: the demand model was refitted on {n} resampled versions of your history, and 90% of the "
              "resulting optimal prices fell in this range. A wide range means the data pins the price down only weakly.",
        "tr": "Bootstrap: talep modeli geçmiş verinizin yeniden örneklenmiş {n} versiyonuyla tekrar kuruldu; çıkan "
              "optimum fiyatların %90'ı bu aralıkta. Geniş bir aralık, verinin fiyatı zayıf belirlediği anlamına gelir.",
        "de": "Bootstrap: Das Nachfragemodell wurde auf {n} neu gezogenen Versionen Ihrer Historie geschätzt; 90 % der "
              "optimalen Preise lagen in diesem Bereich. Ein breiter Bereich heißt, dass die Daten den Preis nur "
              "schwach festlegen.",
    },
    "chart_range": {"en": "90% range of the optimum", "tr": "Optimumun %90 aralığı", "de": "90%-Bereich des Optimums"},
    # ---------- model choice, elasticity confidence, sensitivity, portfolio ----------
    "model_auto": {"en": "Auto", "tr": "Otomatik", "de": "Automatisch"},
    "model_help": {
        "en": "Auto picks the model with the lower out-of-sample forecast error (rolling backtest), or the higher "
              "R² when there is too little data for a backtest.",
        "tr": "Otomatik, örneklem dışı tahmin hatası (kayan geriye dönük test) daha düşük olan modeli seçer; geriye "
              "dönük test için veri yetersizse R² değeri daha yüksek olanı.",
        "de": "Automatisch wählt das Modell mit dem kleineren Prognosefehler außerhalb der Stichprobe (rollierender "
              "Backtest) bzw. dem höheren R², wenn die Daten für einen Backtest nicht reichen.",
    },
    "model_auto_caption": {
        "en": "Auto chose {model} (backtest error {wape}).",
        "tr": "Otomatik seçim: {model} (geriye dönük test hatası {wape}).",
        "de": "Automatisch gewählt: {model} (Backtest-Fehler {wape}).",
    },
    "metric_ped_ci": {"en": "90% CI: {low} to {high}", "tr": "%90 GA: {low} ile {high} arası", "de": "90%-KI: {low} bis {high}"},
    "metric_ped_ci_help": {
        "en": "Bootstrap: the demand model was refitted on {n} resampled versions of your history, and the price "
              "elasticity at the recommended price fell in this range 90% of the time.",
        "tr": "Bootstrap: talep modeli geçmiş verinizin yeniden örneklenmiş {n} versiyonuyla tekrar kuruldu; önerilen "
              "fiyattaki fiyat esnekliği zamanın %90'ında bu aralıkta kaldı.",
        "de": "Bootstrap: Das Nachfragemodell wurde auf {n} neu gezogenen Versionen Ihrer Historie geschätzt; die "
              "Preiselastizität beim empfohlenen Preis lag in 90 % der Fälle in diesem Bereich.",
    },
    "badge_conf_high": {"en": "High confidence", "tr": "Yüksek güven", "de": "Hohe Sicherheit"},
    "badge_conf_medium": {"en": "Medium confidence", "tr": "Orta güven", "de": "Mittlere Sicherheit"},
    "badge_conf_low": {"en": "Low confidence", "tr": "Düşük güven", "de": "Geringe Sicherheit"},
    "sum_ped_ci": {"en": "Price elasticity, 90% CI", "tr": "Fiyat esnekliği, %90 GA", "de": "Preiselastizität, 90%-KI"},
    "sens_expander": {"en": "What moves the optimal price?", "tr": "Optimum fiyatı ne etkiliyor?",
                      "de": "Was bewegt den optimalen Preis?"},
    "sens_na": {
        "en": "Not available: there is no optimum inside the tested price range.",
        "tr": "Kullanılamıyor: denenen fiyat aralığında bir optimum yok.",
        "de": "Nicht verfügbar: Im getesteten Preisbereich gibt es kein Optimum.",
    },
    "sens_title": {"en": "Change in optimal price ({price}) with each input ±10%",
                   "tr": "Her girdi ±%10 değiştiğinde optimum fiyattaki ({price}) değişim",
                   "de": "Änderung des optimalen Preises ({price}) bei ±10 % je Eingabe"},
    "sens_axis": {"en": "Change in optimal price ({sym})", "tr": "Optimum fiyattaki değişim ({sym})",
                  "de": "Änderung des optimalen Preises ({sym})"},
    "sens_low": {"en": "Input −10%", "tr": "Girdi −%10", "de": "Eingabe −10 %"},
    "sens_high": {"en": "Input +10%", "tr": "Girdi +%10", "de": "Eingabe +10 %"},
    "sens_profit": {"en": "profit", "tr": "kâr", "de": "Gewinn"},
    "sens_caption": {
        "en": "Each bar re-runs today's optimization with one input moved and all others unchanged (unconstrained "
              "optimum, before guardrails). Exchange rate and competitor price move as a ±10% shift, inflation by ±10 "
              "percentage points. The longest bars are the inputs worth pinning down first.",
        "tr": "Her çubuk, bir girdi değiştirilip diğerleri sabit tutularak bugünkü optimizasyonu yeniden çalıştırır "
              "(kısıtsız optimum, fiyat kurallarından önce). Döviz kuru ve rakip fiyatı ±%10 kayma olarak, enflasyon "
              "±10 puan değişir. En uzun çubuklar, önce netleştirilmesi gereken girdilerdir.",
        "de": "Jeder Balken rechnet die heutige Optimierung mit einer geänderten Eingabe neu, alle anderen bleiben "
              "gleich (Optimum ohne Preisregeln). Wechselkurs und Konkurrenzpreis ändern sich um ±10 %, die Inflation "
              "um ±10 Prozentpunkte. Die längsten Balken zeigen die Eingaben, die zuerst geklärt werden sollten.",
    },
    "sens_factor_cogs": {"en": "Unit cost", "tr": "Birim maliyet", "de": "Stückkosten"},
    "sens_factor_elasticity": {"en": "Price sensitivity", "tr": "Fiyat duyarlılığı", "de": "Preissensibilität"},
    "sens_factor_fees": {"en": "Variable selling costs", "tr": "Değişken satış giderleri", "de": "Variable Vertriebskosten"},
    "sens_factor_competitor": {"en": "Competitor price", "tr": "Rakip fiyatı", "de": "Konkurrenzpreis"},
    "sens_factor_fx": {"en": "Exchange rate", "tr": "Döviz kuru", "de": "Wechselkurs"},
    "sens_factor_inflation": {"en": "Inflation", "tr": "Enflasyon", "de": "Inflation"},
    "sens_factor_vat": {"en": "VAT rate", "tr": "KDV oranı", "de": "MwSt.-Satz"},
    "sens_col_factor": {"en": "Input", "tr": "Girdi", "de": "Eingabe"},
    "sens_col_price_low": {"en": "Optimal price at −10%", "tr": "−%10'da optimum fiyat", "de": "Optimaler Preis bei −10 %"},
    "sens_col_price_high": {"en": "Optimal price at +10%", "tr": "+%10'da optimum fiyat", "de": "Optimaler Preis bei +10 %"},
    "sens_col_profit_low": {"en": "Profit at −10%", "tr": "−%10'da kâr", "de": "Gewinn bei −10 %"},
    "sens_col_profit_high": {"en": "Profit at +10%", "tr": "+%10'da kâr", "de": "Gewinn bei +10 %"},
    "sheet_sensitivity": {"en": "Sensitivity", "tr": "Duyarlılık", "de": "Sensitivität"},
    "sheet_portfolio": {"en": "All products", "tr": "Tüm ürünler", "de": "Alle Produkte"},
    "pf_spinner": {"en": "Pricing every product…", "tr": "Tüm ürünler fiyatlanıyor…", "de": "Alle Produkte werden bepreist…"},
    "pf_expander": {"en": "All products ({n}): recommended prices", "tr": "Tüm ürünler ({n}): önerilen fiyatlar",
                    "de": "Alle Produkte ({n}): empfohlene Preise"},
    "pf_caption": {
        "en": "Today's recommendation for every product, with the same fees, VAT, import share, competitor reaction, "
              "max change, minimum margin and price ending. Price floor/ceiling and the cost override apply to the "
              "selected product only. Gains are contribution ({per}): profit before fixed costs, which aren't "
              "split by product.",
        "tr": "Her ürün için bugünkü öneri; aynı kesintiler, KDV, ithal payı, rakip tepkisi, en fazla değişim, minimum "
              "marj ve fiyat bitişiyle. Taban/tavan fiyat ve maliyet geçersiz kılma yalnızca seçili ürüne uygulanır. "
              "Kazançlar katkı payıdır ({per}): ürünlere bölünmeyen sabit giderlerden önceki kâr.",
        "de": "Die heutige Empfehlung für jedes Produkt, mit denselben Gebühren, MwSt., Importanteil, "
              "Konkurrenzreaktion, max. Änderung, Mindestmarge und Preisendung. Unter-/Obergrenze und Kosten-"
              "Überschreibung gelten nur für das gewählte Produkt. Zuwächse sind Deckungsbeiträge ({per}): Gewinn vor "
              "Fixkosten, die nicht auf Produkte aufgeteilt werden.",
    },
    "pf_col_product": {"en": "Product", "tr": "Ürün", "de": "Produkt"},
    "pf_col_model": {"en": "Model", "tr": "Model", "de": "Modell"},
    "pf_col_current": {"en": "Current price", "tr": "Mevcut fiyat", "de": "Aktueller Preis"},
    "pf_col_rec": {"en": "Recommended price", "tr": "Önerilen fiyat", "de": "Empfohlener Preis"},
    "pf_col_change": {"en": "Change", "tr": "Değişim", "de": "Änderung"},
    "pf_col_ped": {"en": "Price elasticity", "tr": "Fiyat esnekliği", "de": "Preiselastizität"},
    "pf_col_uplift": {"en": "Contribution gain ({per})", "tr": "Katkı payı artışı ({per})", "de": "Mehr-Deckungsbeitrag ({per})"},
    "pf_col_wape": {"en": "Backtest error", "tr": "Geriye dönük test hatası", "de": "Backtest-Fehler"},
    "pf_col_status": {"en": "Status", "tr": "Durum", "de": "Status"},
    "pf_status_ok": {"en": "OK", "tr": "Tamam", "de": "OK"},
    "pf_status_no_optimum": {"en": "No optimum in range", "tr": "Aralıkta optimum yok", "de": "Kein Optimum im Bereich"},
    "pf_status_no_profit": {"en": "No profitable price", "tr": "Kârlı fiyat yok", "de": "Kein profitabler Preis"},
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
    # ---------- saved scenarios ----------
    "scen_header": {"en": "Scenario: save / load", "tr": "Senaryo: kaydet / yükle", "de": "Szenario: speichern / laden"},
    "scen_save": {"en": "Save scenario", "tr": "Senaryoyu kaydet", "de": "Szenario speichern"},
    "scen_save_help": {
        "en": "Downloads your current settings, and any actual units typed into the price test, as a small JSON "
              "file. Your sales data is not included.",
        "tr": "Mevcut ayarlarınızı ve fiyat testine girdiğiniz gerçekleşen adetleri küçük bir JSON dosyası olarak "
              "indirir. Satış verileriniz dahil edilmez.",
        "de": "Lädt Ihre aktuellen Einstellungen und die im Preistest eingetragenen Ist-Stückzahlen als kleine "
              "JSON-Datei herunter. Ihre Verkaufsdaten sind nicht enthalten.",
    },
    "scen_load": {"en": "Load scenario (.json)", "tr": "Senaryo yükle (.json)", "de": "Szenario laden (.json)"},
    "scen_load_help": {
        "en": "Restores the settings from a file saved with 'Save scenario'. Upload the matching sales file too.",
        "tr": "'Senaryoyu kaydet' ile kaydedilen dosyadaki ayarları geri yükler. İlgili satış dosyasını da yükleyin.",
        "de": "Stellt die Einstellungen aus einer mit „Szenario speichern“ gesicherten Datei wieder her. Laden Sie "
              "auch die passende Verkaufsdatei hoch.",
    },
    "scen_loaded": {
        "en": "Loaded scenario saved {saved_at} for {file}.",
        "tr": "{file} için {saved_at} tarihinde kaydedilen senaryo yüklendi.",
        "de": "Szenario vom {saved_at} für {file} geladen.",
    },
    "scen_err_invalid": {
        "en": "This file is not valid JSON, so no settings were changed.",
        "tr": "Bu dosya geçerli bir JSON değil; hiçbir ayar değiştirilmedi.",
        "de": "Diese Datei ist kein gültiges JSON; es wurden keine Einstellungen geändert.",
    },
    "scen_err_not_ours": {
        "en": "This JSON file is not a scenario saved by this app, so no settings were changed.",
        "tr": "Bu JSON dosyası bu uygulamayla kaydedilmiş bir senaryo değil; hiçbir ayar değiştirilmedi.",
        "de": "Diese JSON-Datei ist kein mit dieser App gespeichertes Szenario; es wurden keine Einstellungen "
              "geändert.",
    },
    "scen_warn_newer": {
        "en": "Saved by a newer version of the app: settings it doesn't know were skipped.",
        "tr": "Uygulamanın daha yeni bir sürümüyle kaydedilmiş: tanınmayan ayarlar atlandı.",
        "de": "Mit einer neueren App-Version gespeichert: Unbekannte Einstellungen wurden übersprungen.",
    },
    "scen_warn_dropped": {
        "en": "Skipped unknown or invalid settings: {keys}.",
        "tr": "Bilinmeyen veya geçersiz ayarlar atlandı: {keys}.",
        "de": "Unbekannte oder ungültige Einstellungen übersprungen: {keys}.",
    },
    "scen_warn_clipped": {
        "en": "Brought into the allowed range: {keys}.",
        "tr": "İzin verilen aralığa çekildi: {keys}.",
        "de": "In den erlaubten Bereich gebracht: {keys}.",
    },
    "scen_warn_plan_invalid": {
        "en": "The saved price test was damaged and was not restored.",
        "tr": "Kaydedilen fiyat testi bozuk olduğu için geri yüklenmedi.",
        "de": "Der gespeicherte Preistest war beschädigt und wurde nicht wiederhergestellt.",
    },
    "scen_warn_other_file": {
        "en": "This scenario was saved with a different sales file ({file}). Results can differ; upload that "
              "file to reproduce them.",
        "tr": "Bu senaryo farklı bir satış dosyasıyla kaydedildi ({file}). Sonuçlar farklı olabilir; aynı "
              "sonuçlar için o dosyayı yükleyin.",
        "de": "Dieses Szenario wurde mit einer anderen Verkaufsdatei gespeichert ({file}). Die Ergebnisse können "
              "abweichen; laden Sie diese Datei hoch, um sie nachzubilden.",
    },
    "scen_warn_product": {
        "en": "The saved product '{product}' is not in this file, so the product was not changed.",
        "tr": "Kaydedilen '{product}' ürünü bu dosyada yok; ürün değiştirilmedi.",
        "de": "Das gespeicherte Produkt „{product}“ ist nicht in dieser Datei; das Produkt wurde nicht geändert.",
    },
    "scen_plan_restored": {
        "en": "Restored {n} week(s) of actual units from the saved scenario.",
        "tr": "Kaydedilen senaryodan {n} haftalık gerçekleşen adet geri yüklendi.",
        "de": "{n} Woche(n) mit Ist-Stückzahlen aus dem gespeicherten Szenario wiederhergestellt.",
    },
    "scen_plan_changed": {
        "en": "The saved price test used different prices or length, so its actual units were not restored here.",
        "tr": "Kaydedilen fiyat testi farklı fiyatlar veya süre kullanıyordu; gerçekleşen adetleri burada geri "
              "yüklenmedi.",
        "de": "Der gespeicherte Preistest hatte andere Preise oder eine andere Dauer; seine Ist-Stückzahlen wurden "
              "hier nicht wiederhergestellt.",
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
    "fee_label": {"en": "Variable selling costs (%)", "tr": "Değişken satış giderleri (%)",
                  "de": "Variable Vertriebskosten (%)"},
    "fee_help": {
        "en": "Every cost charged as a share of the selling price, added up: marketplace commission (e.g. Trendyol, "
              "Amazon: often 15–25%), card or payment fee, sales-rep or distributor commission. Calculated on the "
              "gross customer price (including VAT), matching standard marketplace terms (e.g. Amazon, Trendyol).",
        "tr": "Satış fiyatının yüzdesi olarak kesilen tüm giderlerin toplamı: pazaryeri komisyonu (ör. Trendyol, "
              "Amazon: çoğunlukla %15–25), kart veya ödeme komisyonu, satış temsilcisi ya da distribütör komisyonu. "
              "Pazaryerlerinin standart koşullarına (ör. Amazon, Trendyol) uygun olarak müşterinin ödediği KDV dahil "
              "fiyat üzerinden hesaplanır.",
        "de": "Alle Kosten, die als Anteil am Verkaufspreis anfallen, zusammengezählt: Marktplatzprovision (z. B. "
              "Amazon: oft 15–25 %), Karten- oder Zahlungsgebühr, Vertreter- oder Händlerprovision. Berechnet auf den "
              "Bruttopreis des Kunden (inkl. MwSt.), wie bei den üblichen Marktplatzkonditionen (z. B. Amazon, Trendyol).",
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
    # ---------- competitor reaction ----------
    "reaction_header": {"en": "Competitor reaction", "tr": "Rakip tepkisi", "de": "Reaktion der Konkurrenz"},
    "match_cut_label": {
        "en": "Competitor matches your price cuts",
        "tr": "Rakip fiyat indirimlerinize uyar",
        "de": "Konkurrenz zieht bei Preissenkungen mit",
    },
    "match_cut_help": {
        "en": "Share of a price cut the competitor copies. 100% = they cut by the same %, so a cut wins fewer "
              "customers from them. 0% = they ignore it (the default, and the optimistic case).",
        "tr": "Rakibin bir fiyat indiriminden kopyaladığı pay. %100 = aynı oranda indirir, böylece indirim "
              "rakipten daha az müşteri kazandırır. %0 = görmezden gelir (varsayılan ve iyimser durum).",
        "de": "Anteil einer Preissenkung, den die Konkurrenz übernimmt. 100 % = sie senkt um denselben Prozentsatz, "
              "eine Senkung gewinnt also weniger Kunden. 0 % = sie ignoriert sie (Standard, der optimistische Fall).",
    },
    "match_rise_label": {
        "en": "Competitor matches your price rises",
        "tr": "Rakip fiyat artışlarınıza uyar",
        "de": "Konkurrenz zieht bei Preiserhöhungen mit",
    },
    "match_rise_help": {
        "en": "Share of a price rise the competitor copies. Competitors often follow cuts quickly but rises "
              "rarely, so this is usually lower than the cut setting.",
        "tr": "Rakibin bir fiyat artışından kopyaladığı pay. Rakipler indirimleri çoğu zaman hızla izler, "
              "artışları ise nadiren; bu yüzden genellikle indirim ayarından düşüktür.",
        "de": "Anteil einer Preiserhöhung, den die Konkurrenz übernimmt. Senkungen werden oft schnell "
              "nachgezogen, Erhöhungen selten – daher meist niedriger als bei Senkungen.",
    },
    "reaction_disabled": {
        "en": "Needs a Competitor_Price column in the data.",
        "tr": "Veride Competitor_Price sütunu gerekir.",
        "de": "Erfordert eine Spalte Competitor_Price in den Daten.",
    },
    "caption_no_reaction": {
        "en": "Without a competitor reaction: {price}",
        "tr": "Rakip tepkisi olmasaydı: {price}",
        "de": "Ohne Reaktion der Konkurrenz: {price}",
    },
    "sum_reaction_value": {
        "en": "matches {cut}% of cuts, {rise}% of rises",
        "tr": "indirimlerin %{cut}'ine, artışların %{rise}'ine uyar",
        "de": "zieht {cut} % der Senkungen und {rise} % der Erhöhungen nach",
    },
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
    "breakdown_fees": {"en": "Variable selling costs", "tr": "Değişken satış giderleri", "de": "Variable Vertriebskosten"},
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
    "scenario_no_rails": {
        "en": "The scenario shows the unconstrained optimum: max change, minimum margin, floor/ceiling and price "
              "endings apply only to today's recommendation.",
        "tr": "Senaryo kısıtsız optimumu gösterir: en fazla değişim, minimum marj, taban/tavan fiyat ve fiyat "
              "bitişleri yalnızca bugünkü öneriye uygulanır.",
        "de": "Das Szenario zeigt das Optimum ohne Preisregeln: Max. Änderung, Mindestmarge, Unter-/Obergrenze und "
              "Preisendungen gelten nur für die heutige Empfehlung.",
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
        "en": "variable selling costs {fees:.1f}% · VAT {vat} · extra unit cost {extra}",
        "tr": "değişken satış giderleri %{fees:.1f} · KDV {vat} · ek birim maliyet {extra}",
        "de": "Variable Vertriebskosten {fees:.1f} % · MwSt. {vat} · Zusatzkosten {extra}",
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
    "warn_season_partial": {
        "en": "No data for {n} calendar month(s) in the fit: seasonality treats them as an average month.",
        "tr": "Modelde {n} takvim ayı için veri yok: mevsimsellik bu ayları ortalama bir ay sayar.",
        "de": "Für {n} Kalendermonat(e) gibt es keine Daten in der Schätzung: Die Saison behandelt sie als "
              "durchschnittlichen Monat.",
    },
    "warn_season_one_month": {
        "en": "Every month in the fit is the same calendar month, so seasonality can't be estimated: fitted without it.",
        "tr": "Modeldeki tüm aylar aynı takvim ayı olduğu için mevsimsellik tahmin edilemez: model mevsimsellik "
              "olmadan kuruldu.",
        "de": "Alle Monate in der Schätzung sind derselbe Kalendermonat, daher lässt sich keine Saison schätzen: "
              "ohne Saison geschätzt.",
    },
    "warn_dates_dmy": {
        "en": "Dates like 05/02/2024 can be read either way: read as day/month (5 February). If that's wrong, "
              "pick the file format in the sidebar.",
        "tr": "05/02/2024 gibi tarihler iki türlü okunabilir: gün/ay olarak okundu (5 Şubat). Yanlışsa kenar "
              "çubuğundan dosya biçimini seçin.",
        "de": "Datumsangaben wie 05/02/2024 sind mehrdeutig: als Tag/Monat gelesen (5. Februar). Falls das falsch "
              "ist, wählen Sie das Dateiformat in der Seitenleiste.",
    },
    "warn_dates_mdy": {
        "en": "Dates like 05/02/2024 can be read either way: read as month/day (2 May). If that's wrong, "
              "pick the file format in the sidebar.",
        "tr": "05/02/2024 gibi tarihler iki türlü okunabilir: ay/gün olarak okundu (2 Mayıs). Yanlışsa kenar "
              "çubuğundan dosya biçimini seçin.",
        "de": "Datumsangaben wie 05/02/2024 sind mehrdeutig: als Monat/Tag gelesen (2. Mai). Falls das falsch "
              "ist, wählen Sie das Dateiformat in der Seitenleiste.",
    },
    "warn_numbers_comma": {
        "en": "Numbers like 1,250 can be read either way: read with a decimal comma (1.25). If that's wrong, "
              "pick the file format in the sidebar.",
        "tr": "1,250 gibi sayılar iki türlü okunabilir: ondalık virgülle okundu (1,25). Yanlışsa kenar "
              "çubuğundan dosya biçimini seçin.",
        "de": "Zahlen wie 1,250 sind mehrdeutig: mit Dezimalkomma gelesen (1,25). Falls das falsch ist, wählen "
              "Sie das Dateiformat in der Seitenleiste.",
    },
    "warn_numbers_point": {
        "en": "Numbers like 1,250 can be read either way: read with a thousands comma (1250). If that's wrong, "
              "pick the file format in the sidebar.",
        "tr": "1,250 gibi sayılar iki türlü okunabilir: binlik ayırıcı olarak okundu (1250). Yanlışsa kenar "
              "çubuğundan dosya biçimini seçin.",
        "de": "Zahlen wie 1,250 sind mehrdeutig: mit Tausenderkomma gelesen (1250). Falls das falsch ist, wählen "
              "Sie das Dateiformat in der Seitenleiste.",
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
    "warn_comp_nonpositive": {
        "en": "{n} Competitor_Price values were zero or negative and were treated as missing.",
        "tr": "{n} Competitor_Price değeri sıfır veya negatifti ve eksik kabul edildi.",
        "de": "{n} Competitor_Price-Werte waren null oder negativ und wurden als fehlend behandelt.",
    },
    "warn_cost_negative": {
        "en": "{n} Cost_Per_Unit values were negative and were replaced with the default COGS.",
        "tr": "{n} Cost_Per_Unit değeri negatifti ve varsayılan SMM ile değiştirildi.",
        "de": "{n} Cost_Per_Unit-Werte waren negativ und wurden durch die Standard-Stückkosten ersetzt.",
    },
    "warn_cost_above_price": {
        "en": "In {n} of {n_raw} rows the unit cost is above the price charged. Check that cost and price use "
              "the same unit and currency.",
        "tr": "{n_raw} satırın {n} tanesinde birim maliyet satış fiyatından yüksek. Maliyet ve fiyatın aynı birim "
              "ve para biriminde olduğunu kontrol edin.",
        "de": "In {n} von {n_raw} Zeilen liegen die Stückkosten über dem Verkaufspreis. Prüfen Sie, ob Kosten und "
              "Preis dieselbe Einheit und Währung haben.",
    },
    "warn_comp_sign": {
        "en": "Fitted demand falls when the competitor's price rises, the opposite of what a substitute does. "
              "The competitor effect is probably mixed up with other demand drivers; treat it with caution.",
        "tr": "Tahmini talep, rakip fiyatı arttığında düşüyor; bu bir ikame ürünün beklenen davranışının tersi. "
              "Rakip etkisi büyük olasılıkla başka talep etkenleriyle karışıyor; temkinle değerlendirin.",
        "de": "Die geschätzte Nachfrage sinkt, wenn der Konkurrenzpreis steigt, das Gegenteil eines Substituts. "
              "Der Konkurrenzeffekt ist vermutlich mit anderen Nachfragetreibern vermischt; mit Vorsicht behandeln.",
    },
    "err_no_interior": {
        "en": "No profit-maximizing price inside the tested range: profit keeps rising up to the max price to "
              "test ({max}). The recommended price is the edge of your guardrails, not an optimum, and the 90% "
              "range is hidden. Run a price test before relying on it.",
        "tr": "Denenen aralıkta kârı en üst düzeye çıkaran bir fiyat yok: kâr, denenecek en yüksek fiyata ({max}) "
              "kadar artmaya devam ediyor. Önerilen fiyat bir optimum değil, fiyat kurallarınızın sınırıdır ve %90 "
              "aralık gizlendi. Ona güvenmeden önce bir fiyat testi yapın.",
        "de": "Kein gewinnmaximaler Preis im getesteten Bereich: Der Gewinn steigt bis zum höchsten Testpreis "
              "({max}) weiter. Der empfohlene Preis ist die Grenze Ihrer Preisregeln, kein Optimum, und der "
              "90%-Bereich ist ausgeblendet. Führen Sie einen Preistest durch, bevor Sie sich darauf verlassen.",
    },
    "err_no_interior_low": {
        "en": "No profit-maximizing price inside the tested range: profit keeps rising as the price falls, down "
              "to the lowest price tested ({min}). This usually means the unit cost is missing or zero. The "
              "recommended price is the edge of your guardrails, not an optimum, and the 90% range is hidden.",
        "tr": "Denenen aralıkta kârı en üst düzeye çıkaran bir fiyat yok: kâr, fiyat düştükçe denenen en düşük "
              "fiyata ({min}) kadar artmaya devam ediyor. Bu genellikle birim maliyetin eksik ya da sıfır olduğu "
              "anlamına gelir. Önerilen fiyat bir optimum değil, fiyat kurallarınızın sınırıdır ve %90 aralık gizlendi.",
        "de": "Kein gewinnmaximaler Preis im getesteten Bereich: Der Gewinn steigt mit sinkendem Preis bis zum "
              "niedrigsten Testpreis ({min}) weiter. Meist fehlen die Stückkosten oder sind null. Der empfohlene "
              "Preis ist die Grenze Ihrer Preisregeln, kein Optimum, und der 90%-Bereich ist ausgeblendet.",
    },
    "err_no_profit": {
        "en": "No price covers the variable costs: at every price tested, unit cost, selling costs and VAT take "
              "more than the price brings in, so every unit sold loses money. The figures shown are not a "
              "recommendation. Check the unit cost, the variable selling costs % and the VAT setting.",
        "tr": "Hiçbir fiyat değişken maliyetleri karşılamıyor: denenen her fiyatta birim maliyet, satış giderleri "
              "ve KDV fiyattan fazlasını götürüyor, yani satılan her birim zarar ettiriyor. Gösterilen değerler bir "
              "öneri değildir. Birim maliyeti, değişken satış giderleri yüzdesini ve KDV ayarını kontrol edin.",
        "de": "Kein Preis deckt die variablen Kosten: Bei jedem getesteten Preis kosten Stückkosten, "
              "Vertriebskosten und MwSt. mehr, als der Preis einbringt, jede verkaufte Einheit bringt also "
              "Verlust. Die angezeigten Werte sind keine Empfehlung. Prüfen Sie Stückkosten, variable "
              "Vertriebskosten in % und die MwSt.-Einstellung.",
    },
    "err_no_sales": {
        "en": "The data has no sales: quantity sold is 0 in every month used for the fit, so demand can't be "
              "estimated.",
        "tr": "Veride satış yok: tahminde kullanılan her ayda satılan adet 0, bu yüzden talep tahmin edilemiyor.",
        "de": "Die Daten enthalten keine Verkäufe: Die verkaufte Menge ist in jedem für die Schätzung genutzten "
              "Monat 0, daher lässt sich die Nachfrage nicht schätzen.",
    },
    "warn_fees_exceed_price": {
        "en": "Variable selling costs ({fees:.1f}%) take the whole net price after VAT ({net:.1f}% of the "
              "price): every sale loses money at any price.",
        "tr": "Değişken satış giderleri (%{fees:.1f}), KDV sonrası net fiyatın tamamını alıyor (fiyatın "
              "%{net:.1f}'i): her fiyatta her satış zarar ettirir.",
        "de": "Die variablen Vertriebskosten ({fees:.1f} %) verbrauchen den gesamten Nettopreis nach MwSt. "
              "({net:.1f} % des Preises): Jeder Verkauf bringt bei jedem Preis Verlust.",
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
    "warn_opt_at_bottom": {
        "en": "The optimum is at the bottom of the price search range: profit still rises towards lower prices, "
              "so this is no real optimum.",
        "tr": "Optimum, fiyat arama aralığının en altında: kâr daha düşük fiyatlara doğru artmaya devam ediyor, "
              "bu yüzden bu gerçek bir optimum değil.",
        "de": "Das Optimum liegt am unteren Ende des Suchbereichs: Der Gewinn steigt zu niedrigeren Preisen hin "
              "weiter, daher ist dies kein echtes Optimum.",
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
    "warn_flag_col_ignored": {
        "en": "Column '{column}' was not used as the Flag column: none of its values is 'stockout' or 'promo' "
              "(e.g. a transaction status). Rename it to 'Flag' to use it anyway.",
        "tr": "'{column}' sütunu Flag sütunu olarak kullanılmadı: hiçbir değeri 'stok yok' veya 'kampanya' değil "
              "(ör. bir işlem durumu). Yine de kullanmak için adını 'Flag' yapın.",
        "de": "Spalte „{column}“ wurde nicht als Flag-Spalte verwendet: Keiner ihrer Werte ist „ausverkauft“ "
              "oder „Aktion“ (z. B. ein Transaktionsstatus). Benennen Sie sie in „Flag“ um, um sie trotzdem zu nutzen.",
    },
    "file_format_label": {"en": "File format", "tr": "Dosya biçimi", "de": "Dateiformat"},
    "file_format_help": {
        "en": "How to read dates like 05/02/2024 and numbers like 1,250 when the file itself doesn't settle it. "
              "Auto follows the selected country; a fixed format keeps the data the same when you switch countries.",
        "tr": "Dosyanın kendisi belirlemediğinde 05/02/2024 gibi tarihlerin ve 1,250 gibi sayıların nasıl okunacağı. "
              "Otomatik seçili ülkeyi izler; sabit bir biçim, ülke değiştirdiğinizde veriyi aynı tutar.",
        "de": "Wie Datumsangaben wie 05/02/2024 und Zahlen wie 1,250 gelesen werden, wenn die Datei es nicht "
              "eindeutig macht. Automatisch folgt dem gewählten Land; ein festes Format hält die Daten beim "
              "Länderwechsel gleich.",
    },
    "file_format_auto": {"en": "Auto (from the country)", "tr": "Otomatik (ülkeye göre)",
                         "de": "Automatisch (nach Land)"},
    "file_format_dmy_comma": {"en": "dd/mm/yyyy · 1.234,56", "tr": "gg/aa/yyyy · 1.234,56",
                              "de": "TT/MM/JJJJ · 1.234,56"},
    "file_format_dmy_point": {"en": "dd/mm/yyyy · 1,234.56", "tr": "gg/aa/yyyy · 1,234.56",
                              "de": "TT/MM/JJJJ · 1,234.56"},
    "file_format_mdy_point": {"en": "mm/dd/yyyy · 1,234.56", "tr": "aa/gg/yyyy · 1,234.56",
                              "de": "MM/TT/JJJJ · 1,234.56"},
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
    "warn_test_no_change": {
        "en": "Within your guardrails and price ending the test price stays at the current price ({price:,.2f}), "
              "so there is nothing to test. Widen 'Max change' or the floor/ceiling, or pick another price ending.",
        "tr": "Fiyat kurallarınız ve fiyat bitişiyle test fiyatı mevcut fiyatta ({price:,.2f}) kalıyor, bu yüzden "
              "test edilecek bir şey yok. 'En fazla değişim' veya taban/tavan fiyatı genişletin ya da başka bir "
              "fiyat bitişi seçin.",
        "de": "Mit Ihren Preisregeln und der Preisendung bleibt der Testpreis beim aktuellen Preis ({price:,.2f}), "
              "es gibt also nichts zu testen. Erweitern Sie „Max. Änderung“ oder Unter-/Obergrenze oder wählen Sie "
              "eine andere Preisendung.",
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


DECIMAL_COMMA = {"tr", "de"}  # languages that write 1.234,56 instead of 1,234.56
_SWAP = str.maketrans(",.", ".,")


def fmt_number(x: float, spec: str, lang: str) -> str:
    """`format(x, spec)` with the separators of `lang` (1.234,56 in Turkish and German)."""
    text = format(x, spec)
    return text.translate(_SWAP) if lang in DECIMAL_COMMA else text


def fmt_money(x: float, sym: str, lang: str, decimals: int = 2) -> str:
    """An amount with its currency symbol: $1,234.56 in English, 1.234,56 ₺ in Turkish and German.
    No minus sign on an amount that rounds to zero."""
    amount = fmt_number(abs(x), f",.{decimals}f", lang)
    sign = "-" if x < 0 and round(abs(x), decimals) > 0 else ""
    return f"{sign}{amount} {sym}" if lang in DECIMAL_COMMA else f"{sign}{sym}{amount}"


class _LocalFloat(float):
    """A float that formats with a language's separators inside str.format (see translate)."""
    lang = "en"

    def __format__(self, spec: str) -> str:
        return fmt_number(float(self), spec, self.lang)


class _LocalInt(int):
    lang = "en"

    def __format__(self, spec: str) -> str:
        return fmt_number(int(self), spec, self.lang)


def _localized(value, lang: str):
    if lang not in DECIMAL_COMMA or isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    out = (_LocalFloat if isinstance(value, float) else _LocalInt)(value)
    out.lang = lang
    return out


def translate(key: str, lang: str = "en", **params) -> str:
    """Render `key` in `lang`, falling back to English, then to the key itself. Numbers in the
    text use the language's separators."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry["en"]
    return text.format(**{k: _localized(v, lang) for k, v in params.items()}) if params else text


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
