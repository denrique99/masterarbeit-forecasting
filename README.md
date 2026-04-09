# ML Revenue Forecasting – Dokumentation für die Präsentation

> **Zielgruppe:** Diese Dokumentation erklärt das Forecasting-Modell ohne Python- oder ML-Vorkenntnisse.

---

## Inhaltsverzeichnis

1. [Das große Bild: Was macht das Modell?](#1-das-große-bild-was-macht-das-modell)
2. [Die Datengrundlage: Was geht rein?](#2-die-datengrundlage-was-geht-rein)
3. [Feature Engineering – Was bedeutet das?](#3-feature-engineering--was-bedeutet-das)
4. [Die einzelnen Treiber erklärt](#4-die-einzelnen-treiber-erklärt)
5. [Modelltraining: Wie lernt XGBoost?](#5-modelltraining-wie-lernt-xgboost)
6. [SHAP – Wie wird der Forecast erklärbar?](#6-shap--wie-wird-der-forecast-erklärbar)
7. [Der 2026-Forecast: Wie entstehen die Zahlen?](#7-der-2026-forecast-wie-entstehen-die-zahlen)
8. [Wichtige Einschränkungen (Ehrlichkeit ist Pflicht)](#8-wichtige-einschränkungen-ehrlichkeit-ist-pflicht)
9. [Kernaussagen für den Chef in 3 Minuten](#9-kernaussagen-für-den-chef-in-3-minuten)

---

## 1. Das große Bild: Was macht das Modell?

Das Modell beantwortet eine ganz konkrete Frage:

> **„Wie viel Umsatz werden wir im Jahr 2026 mit unseren US-Kompressoren-Bestandskunden machen – bei Aufträgen, die wir noch gar nicht kennen?"**

Das ist die **B3-Schicht** des hybriden Forecasting-Systems:

| Schicht | Was ist das? | Woher kommen die Zahlen? |
|---------|-------------|--------------------------|
| **B1** | Bestätigte Aufträge + gewichtete Angebotspipeline | Direkt aus SAP – bekannte Zahlen |
| **B2** | Neukundengeschäft | Schätzungen des Vertriebs |
| **B3** | Unbekannte Opportunities bei Bestandskunden | **XGBoost-ML-Modell (dieses Projekt)** |

**Ergebnis = B3_gesamt − (B1 + B2)**

Das Modell ersetzt keine Planung – es gibt eine **datenbasierte Untergrenze**, mit der man Managementziele auf Plausibilität prüfen kann. Die Kernthese der Arbeit: Top-Down-Ziele ohne Datenbasis führen zu Overplanning.

---

## 2. Die Datengrundlage: Was geht rein?

Das Modell lernt aus zwei Datenquellen:

### Umsatzdaten (aus SAP)
- Quelle: SAP Analytics Cloud Export (VBRP/VBRK – Rechnungsdaten)
- Produkt: Compressors, Markt: US
- Zeitraum: Oktober 2022 – Dezember 2025 (33 Monate nach Bereinigung)
- Inhalt: Monatlicher Nettoumsatz in USD

### Makroökonomische Indikatoren (externe Daten, USA)
- **DGORDER** (FRED-Datenbank): US-Bestellvolumen für langlebige Industriegüter in Mrd. USD/Monat
- **INDPRO** (FRED-Datenbank): US-Industrieproduktionsindex (Basisjahr 2017 = 100)

**Warum keine deutschen Makrodaten?**
Deutsche Daten (Destatis) wurden bewusst ausgeschlossen. Der Umsatz ist rein US-seitig – deutsche Auftragsindizes hätten keinen direkten Kausalzusammenhang, sondern nur eine zufällige Korrelation erzeugt, die das Modell überanpassen würde.

---

## 3. Feature Engineering – Was bedeutet das?

### Die zentrale Idee einfach erklärt

Ein ML-Modell kann nicht einfach auf rohe Umsatzzahlen schauen und „raten". Es braucht strukturierte **Eingabevariablen** (Features = Treiber), aus denen es lernt.

**Feature Engineering** ist der Prozess, aus den Rohdaten sinnvolle Eingabevariablen zu bauen.

**Analogie:** Ein erfahrener Vertriebsleiter schaut auch nicht nur auf die aktuelle Monatszahl. Er denkt: „Letzten Monat lief es gut, das Quartal ist fast vorbei, und ich weiß, dass die Bestelleingänge in den USA vor 3 Monaten gestiegen sind." Genau das machen die Features – sie formalisieren dieses implizite Wissen.

### Die vier Gruppen von Features

---

### Feature-Gruppe 1: Makro-Lag-Features (12 Features)

**Was ist ein „Lag"?**
Ein Lag ist ein Zeitversatz. `lag_3` beim DGORDER für Monat Oktober bedeutet: „Was war der DGORDER-Wert im Juli?" Das Modell lernt, ob ein Wirtschaftsindikator von vor 1, 2, 3 ... 6 Monaten den heutigen Umsatz beeinflusst hat.

**Warum Lags und nicht der aktuelle Wert?**
Weil Makroökonomie mit Verzögerung wirkt. Wenn ein Industrieunternehmen in den USA im Januar mehr bestellt, kommt die Bestellung bei uns möglicherweise erst im März oder April an. Der beste Lag wurde nicht manuell festgelegt – das Modell wählt ihn selbst über SHAP.

**Warum First Differences (`_diff`)?**
Die Rohdaten von DGORDER und INDPRO sind „nicht-stationär" – d. h., sie haben einen langfristigen Aufwärtstrend. ML-Modelle lernen besser aus Veränderungen als aus absoluten Niveaus. Deshalb wird die monatliche Veränderung (`diff`) verwendet: „Hat sich die Industrieproduktion gegenüber dem Vormonat erhöht oder verringert?"

---

### Feature-Gruppe 2: Kalender-Features (4 Features)

| Feature | Bedeutung | Warum wichtig? |
|---------|-----------|----------------|
| `month` | Monatsnummer 1–12 | Saisonalität – z. B. Januar oft schwächer |
| `quarter` | Quartal 1–4 | Quartalsrhythmus im B2B-Geschäft |
| `year` | Jahreszahl | Langfristiger Trend |
| `is_q4` | 1 = Q4, 0 = sonst | Q4-Effekt: Jahresend-Budgets werden oft noch ausgegeben |

---

### Feature-Gruppe 3: Autoregressive Features – Revenue Lags (3 Features)

| Feature | Bedeutung |
|---------|-----------|
| `revenue_lag_1` | Umsatz des Vormonats |
| `revenue_lag_2` | Umsatz vor 2 Monaten |
| `revenue_lag_3` | Umsatz vor 3 Monaten |

**Was bedeutet „autoregressive" Features?**
Das Modell schaut auf seine eigene Vergangenheit. Wenn der Umsatz die letzten 3 Monate stark war, ist die Wahrscheinlichkeit hoch, dass auch der nächste Monat stark ist. Das ist das stärkste Signal im Modell (wie die SHAP-Analyse zeigt).

**Wichtig:** Diese Lags werden **pro Produkt separat** berechnet, damit Accessories und Compressors sich nicht gegenseitig beeinflussen (kein „Data Leakage").

---

### Feature-Gruppe 4: Rolling Window Features (4 Features)

| Feature | Bedeutung |
|---------|-----------|
| `revenue_rolling_3m_mean` | Durchschnitts-Umsatz der letzten 3 Monate |
| `revenue_rolling_3m_std` | Schwankungsbreite (Volatilität) der letzten 3 Monate |
| `revenue_rolling_6m_mean` | Durchschnitts-Umsatz der letzten 6 Monate |
| `revenue_rolling_6m_std` | Schwankungsbreite der letzten 6 Monate |

**Was ist ein Rolling Window?**
Ein gleitendes Fenster. Der 3-Monats-Durchschnitt im Oktober ist der Mittelwert aus Juli, August, September. Das Fenster „rollt" jeden Monat eine Stelle weiter.

**Warum Mean UND Std?**
- Der **Mittelwert** zeigt das Momentum: Läuft das Geschäft gerade gut oder schlecht?
- Die **Standardabweichung** zeigt die Unsicherheit: Ist das Geschäft stabil oder sehr volatil? Ein Modell kann bei stabilen Perioden zuverlässiger forecasen.

**Wichtig:** Das Fenster wird um einen Monat nach hinten verschoben (shift by 1), um sicherzustellen, dass der aktuelle Monatswert nicht in die eigene Vorhersage eingeht – das wäre „Schummeln" (Data Leakage).

---

## 4. Die einzelnen Treiber erklärt

Hier sind alle 23 Features mit ihrer Bedeutung:

### Makro-Treiber: US Durable Goods Orders (DGORDER)

**Was ist das?** Der monatliche Bestellwert für langlebige Industriegüter in den USA (Maschinen, Kompressoren, Ausrüstung), in Milliarden USD. Veröffentlicht von der US-Bundesstatistikbehörde (Census Bureau via FRED).

**Warum ist das relevant?** Unsere Kunden sind US-Industrieunternehmen. Wenn der Sektor insgesamt mehr bestellt, kaufen sie auch mehr Kompressoren von uns. DGORDER ist ein **führender Indikator** – er zeigt die Nachfrage an, bevor sie sich in unseren Auftragsbüchern niederschlägt.

| Feature | Bedeutung |
|---------|-----------|
| `us_durable_goods_orders_musd_diff_lag_1` | Veränderung des DGORDER vor 1 Monat |
| `us_durable_goods_orders_musd_diff_lag_2` | Veränderung des DGORDER vor 2 Monaten |
| `us_durable_goods_orders_musd_diff_lag_3` | Veränderung des DGORDER vor 3 Monaten |
| `us_durable_goods_orders_musd_diff_lag_4` | Veränderung des DGORDER vor 4 Monaten |
| `us_durable_goods_orders_musd_diff_lag_5` | Veränderung des DGORDER vor 5 Monaten |
| `us_durable_goods_orders_musd_diff_lag_6` | Veränderung des DGORDER vor 6 Monaten |

---

### Makro-Treiber: US Industrial Production Index (INDPRO)

**Was ist das?** Misst die monatliche Produktionsleistung der US-Industrie. Basisjahr = 2017 (Index = 100). Veröffentlicht von der US-Notenbank (Federal Reserve via FRED).

**Warum ist das relevant?** Wenn die US-Industrie mehr produziert, braucht sie mehr Kompressoren und Werkzeuge. INDPRO gibt an, ob die Fabriken auf Hochtouren laufen oder gedrosselt sind.

| Feature | Bedeutung |
|---------|-----------|
| `us_production_index_diff_lag_1` | Veränderung der Industrieproduktion vor 1 Monat |
| `us_production_index_diff_lag_2` | Veränderung der Industrieproduktion vor 2 Monaten |
| `us_production_index_diff_lag_3` | Veränderung der Industrieproduktion vor 3 Monaten |
| `us_production_index_diff_lag_4` | Veränderung der Industrieproduktion vor 4 Monaten |
| `us_production_index_diff_lag_5` | Veränderung der Industrieproduktion vor 5 Monaten |
| `us_production_index_diff_lag_6` | Veränderung der Industrieproduktion vor 6 Monaten |

---

### Kalender-Treiber

| Feature | Bedeutung | Praktisches Beispiel |
|---------|-----------|----------------------|
| `month` | Monat 1–12 | Januar typisch schwächer als Oktober |
| `quarter` | Quartal 1–4 | Q2 und Q4 oft stärker im B2B |
| `year` | Jahreszahl 2023–2025 | Erfasst langfristigen Wachstumstrend |
| `is_q4` | 1 wenn Q4, sonst 0 | Jahresendgeschäft: Kunden geben Budget aus |

---

### Historische Umsatz-Treiber (Autoregression)

| Feature | Bedeutung | Praktisches Beispiel |
|---------|-----------|----------------------|
| `revenue_lag_1` | Umsatz Vormonat in USD | Oktober-Forecast nutzt September-Umsatz |
| `revenue_lag_2` | Umsatz vor 2 Monaten | Oktober nutzt August-Umsatz |
| `revenue_lag_3` | Umsatz vor 3 Monaten | Oktober nutzt Juli-Umsatz |

---

### Rolling Window Treiber

| Feature | Bedeutung | Praktisches Beispiel |
|---------|-----------|----------------------|
| `revenue_rolling_3m_mean` | Ø-Umsatz der letzten 3 Monate | Zeigt kurzfristiges Momentum |
| `revenue_rolling_3m_std` | Schwankung der letzten 3 Monate | Hoch = volatil, niedrig = stabil |
| `revenue_rolling_6m_mean` | Ø-Umsatz der letzten 6 Monate | Zeigt mittelfristigen Trend |
| `revenue_rolling_6m_std` | Schwankung der letzten 6 Monate | Zeigt strukturelle Stabilität |

---

## 5. Modelltraining: Wie lernt XGBoost?

### Was ist XGBoost?

XGBoost ist ein **Entscheidungsbaum-Ensemble**. Vereinfacht erklärt:

1. Das Modell baut viele einfache Entscheidungsbäume nacheinander auf.
2. Jeder neue Baum lernt aus den Fehlern des vorherigen.
3. Am Ende werden alle Bäume zu einer gemeinsamen Vorhersage kombiniert.

**Analogie:** Stellen Sie sich vor, 200 Kollegen schauen sich unabhängig voneinander die Daten an und machen eine Prognose. Die Prognosen werden gemittelt. Das Ergebnis ist stabiler als die Meinung eines Einzelnen.

### Warum TimeSeriesSplit statt normalem Test/Train?

Bei Zeitreihendaten darf man **nicht** zufällig in Training und Test aufteilen – dann würde man z. B. den Dezember 2024 vorhersagen, obwohl man den Januar 2025 schon „gesehen" hat. Das wäre Schummeln.

**TimeSeriesSplit** macht es richtig: Immer werden ältere Daten für das Training genommen, neuere für den Test.

```
Fold 1: Train [Apr'23–Nov'23]  →  Test [Dez'23–Apr'24]
Fold 2: Train [Apr'23–Apr'24]  →  Test [Mai'24–Sep'24]
Fold 3: Train [Apr'23–Sep'24]  →  Test [Okt'24–Feb'25]
Fold 4: Train [Apr'23–Feb'25]  →  Test [Mär'25–Jul'25]
Fold 5: Train [Apr'23–Jul'25]  →  Test [Aug'25–Dez'25]
```

### Die Modellgüte (Testergebnisse)

| Kennzahl | Bedeutung | Ergebnis (Ø über 5 Folds) |
|----------|-----------|--------------------------|
| **MAE** | Mittlerer absoluter Fehler in USD | 387.640 USD |
| **RMSE** | Wurzel des mittl. quadr. Fehlers | 455.925 USD |
| **sMAPE** | Symmetrischer prozentualer Fehler | 17,2 % |
| **WMAPE** | Gewichteter prozentualer Fehler | 16,6 % |

**Was bedeutet 17% sMAPE?** Im Durchschnitt liegt die Vorhersage ca. 17% daneben. Bei einem durchschnittlichen Monatsumsatz von ~2,3 Mio. USD sind das ca. ±390.000 USD Abweichung – für einen ML-Prototyp auf 33 Trainingsmonaten ein akzeptables Ergebnis.

---

## 6. SHAP – Wie wird der Forecast erklärbar?

### Das Kernproblem mit ML

Ein trainiertes Modell ist eine „Black Box": Es nimmt 23 Zahlen rein und gibt eine Zahl raus. Aber **warum** gibt es genau diese Zahl aus? Das kann man ohne Weiteres nicht sehen.

Das ist das Problem für Planungsentscheidungen: Ein Chef kann einen Forecast nicht akzeptieren, wenn er nicht versteht, worauf er basiert.

### SHAP löst dieses Problem

**SHAP** (SHapley Additive exPlanations) ist eine mathematische Methode, die für jede einzelne Vorhersage erklärt, **welcher Treiber wie viel beigetragen hat**.

**Die Grundidee:**
Jede Vorhersage wird zerlegt in:
- Den **Basiswert** (Erwartungswert des Modells ohne jede Information) = 2.325.974 USD
- Die **SHAP-Werte** der einzelnen Features = positive oder negative Abweichungen vom Basiswert

> **Formel:**
> Vorhersage = Basiswert + SHAP(revenue_lag_1) + SHAP(revenue_lag_2) + SHAP(month) + ... + SHAP(DGORDER_lag_3)

### Die drei SHAP-Visualisierungen

---

#### 6a – SHAP Summary Plot (Beeswarm-Diagramm)

**Was zeigt es?** Alle 33 Beobachtungen für alle Features gleichzeitig. Jeder Punkt ist ein Monat.

- **X-Achse:** Wie stark hat dieses Feature die Vorhersage verändert? (positiv = nach oben, negativ = nach unten)
- **Farbe:** Rot = hoher Feature-Wert, Blau = niedriger Feature-Wert
- **Y-Achse:** Features sortiert nach Gesamtwichtigkeit (oben = wichtigster Treiber)

**Was die Analyse zeigt:**
- `revenue_lag_1` ist der stärkste Treiber: War der Vormonat gut (rot), prognostiziert das Modell wieder einen hohen Umsatz
- `revenue_rolling_3m_mean` bestätigt das Momentum: Stabile hohe Vergangenheit → hohe Prognose
- `month` und `quarter` zeigen die Saisonalität
- Makro-Features (DGORDER, INDPRO) liefern ergänzende Signale

---

#### 6b – SHAP Importance Bar Chart

**Was zeigt es?** Die Top-20-Features nach durchschnittlichem absoluten SHAP-Wert – ein einfaches Ranking: Welcher Treiber ist insgesamt am wichtigsten?

**Typische Rangfolge:**
1. Revenue Lags (Umsatz-Vergangenheit) – stärkstes Signal
2. Rolling Window Features (Momentum und Volatilität)
3. Kalender-Features (Saisonalität)
4. Makro-Features (externer Kontext)

---

#### 6c – SHAP Waterfall Plot (Einzelne Vorhersage aufgedröselt)

**Was zeigt es?** Für einen **einzelnen Monat** (z. B. Dezember 2025 oder Januar 2026) sieht man Schritt für Schritt, wie das Modell zur Vorhersage kommt.

**Aufbau:**
```
Basiswert:              2.325.974 USD
+ revenue_lag_1:        +420.000 USD   (Vormonat war stark)
+ rolling_3m_mean:      +180.000 USD   (Quartal lief gut)
+ month (Dez):          +95.000 USD    (Dezember = Jahresendgeschäft)
+ DGORDER_diff_lag_2:   -35.000 USD    (Bestellrückgang vor 2 Monaten)
...
= Vorhersage:           2.950.000 USD
```

**Das ist das wichtigste Chart für die Präsentation:** Es zeigt dem Chef, dass das Modell nicht „rät", sondern konkrete, nachvollziehbare Gründe für seine Zahlen hat.

---

### Warum SHAP die Kernthese unterstützt

> SHAP beweist, dass der Forecast auf **beobachtbaren Daten** basiert, nicht auf Top-Down-Wunschdenken.
> Wenn ein Manager sagt „Wir planen 30% Wachstum", kann man mit dem SHAP Waterfall zeigen:
> „Das Modell sieht auf Basis der aktuellen Auftragslagen und Makrodaten +8% – woher kommen die restlichen 22%?"

---

## 7. Der 2026-Forecast: Wie entstehen die Zahlen?

Das Modell wurde auf Daten bis Dezember 2025 trainiert. Für 2026 gibt es keine echten Umsatzdaten, auf die es zurückgreifen kann. Deshalb wird ein **Rolling Forecast** verwendet:

### Schritt-für-Schritt: Wie wird Januar 2026 prognostiziert?

1. **Makro-Features** für Januar 2026: Nutze die DGORDER/INDPRO-Werte aus Juli–Dezember 2025 (Lags 1–6)
2. **Kalender-Features**: `month=1`, `quarter=1`, `year=2026`, `is_q4=0`
3. **Revenue Lags**: Nutze die echten Dezember/November/Oktober 2025-Umsätze
4. **Rolling Features**: Berechne Ø und Std aus den letzten echten Monaten
5. → Modell gibt Prognose für Januar 2026 aus

### Schritt-für-Schritt: Wie wird Februar 2026 prognostiziert?

1. Makro-Features: Nutze Daten aus Aug–Jan (letzter Monat = Carry-Forward)
2. **Revenue Lags**: `revenue_lag_1` = **die soeben prognostizierte Januar-Prognose**
3. → Die Prognose „füttert sich selbst"

Dieses Verfahren heißt **Rolling One-Step-Ahead Forecast**. Fehler akkumulieren sich über den Zeithorizont – die Unsicherheit wächst mit jedem Monat.

### Makro-Daten für 2026

Echte Makrodaten für 2026 lagen bei Erstellung nicht vor. Annahme: **Carry-Forward** – der letzte bekannte Wert wird für alle Monate bis Dezember 2026 eingefroren. Das ist ein konservatives Baseline-Szenario und eine Modell-Limitierung.

---

## 8. Wichtige Einschränkungen (Ehrlichkeit ist Pflicht)

| Einschränkung | Bedeutung |
|---------------|-----------|
| **Synthetische Daten** | Die Umsatzdaten wurden für die Masterarbeit simuliert – alle Kennzahlen (MAE, sMAPE) zeigen die Methodik, nicht echte Forecast-Qualität |
| **33 Trainingsbeobachtungen** | Sehr kleiner Datensatz für ML. Auf echten Produktionsdaten kann das Modell besser oder schlechter sein |
| **Carry-Forward Makro 2026** | Wirtschaftliche Veränderungen in 2026 sind nicht berücksichtigt |
| **Keine Hyperparameter-Optimierung** | Zu kleiner Datensatz für zuverlässiges Parameter-Tuning |
| **B1/B2 nicht enthalten** | Der 2026-Forecast ist das rohe B3-Signal. Finale Planung = B3_gesamt − (B1 + B2) |

---

## 9. Kernaussagen für den Chef in 3 Minuten

### Slide 1: Das Problem
> Unternehmen planen Umsatzziele oft top-down ohne Datenbasis. Das führt zu Overplanning.

### Slide 2: Die Lösung
> Wir nutzen historische SAP-Daten + US-Wirtschaftsindikatoren, um einen datenbasierten Forecast für das B3-Geschäft zu erstellen. Das Modell ersetzt keine Planung – es liefert eine **Benchmark**, mit der Ziele auf Plausibilität geprüft werden können.

### Slide 3: Die Treiber
> Das Modell lernt aus 23 Variablen in 4 Gruppen:
> 1. **Eigene Vergangenheit** (Was haben wir die letzten 3 Monate gemacht?)
> 2. **Saisonalität** (Ist es Q4? Welcher Monat?)
> 3. **Wirtschaftslage** (Wie entwickeln sich US-Industriebestellungen und -produktion?)
> 4. **Stabilität** (War das Geschäft volatil oder stabil?)

### Slide 4: Warum kann ich dem Modell vertrauen? (SHAP)
> Mit SHAP kann ich für jeden Forecast-Monat zeigen, warum das Modell diesen Wert prognostiziert. Das ist kein Raten – jede Zahl hat eine nachvollziehbare Begründung.
>
> **Beispiel Waterfall Plot:** „Das Modell prognostiziert 2,95 Mio. USD für Januar 2026, weil der Dezember 2025 stark war (+420k), das Quartal gut lief (+180k) und Januar traditionell positiv ist (+95k), aber die DGORDER leicht gesunken sind (−35k)."

### Slide 5: Das Ergebnis
> Der 2026-Forecast auf Basis der aktuell verfügbaren Daten zeigt [Wert aus Notebook 06 eintragen]. Das ist die datenbasierte Erwartung. Managementziele sollten in diesem Korridor liegen oder explizit begründen, warum sie davon abweichen.

---

*Erstellt auf Basis der Notebooks 03–06 des XGBoost B3 Forecasting-Projekts (Masterarbeit TU Berlin, Simulated date: 31.12.2025)*
