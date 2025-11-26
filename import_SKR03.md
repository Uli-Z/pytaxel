# Import SKR03 → eBilanz plan

## Ausgangslage im Repository
- CSV → rudimentäres eBilanz-XML ist bereits möglich (`pytaxel.ebilanz.parse_csv` + `render_ebilanz`), aber es fehlt jede Geschäftslogik für SKR03, Kontext-/Unit-Handling und echte Taxonomie-Felder.
- ERiC-Anbindung steht (`pytaxel.eric.EricClient`), Validation/Send können bereits ein PDF erzeugen, sobald ein XML vorliegt.
- Wiederverwendbare Assets: `taxel/templates/elster_v11/taxonomy_v6.5/` (XML-Gerüst), `taxel/mappings/skr03.csv` (Kontenstruktur), `taxel/test_data/taxonomy` (Beispiel-XML/CSV), Rust-Referenz `taxel/taxel-xml` (zeigt, wie Tags, Pflichtfelder und Filter funktionieren).
- Offene TODOs: `pytaxel/ebilanz/templates.py` ist leer; `renderer` setzt nur `stichtag` + Positionen ohne GCD/GAAP-Namespaces, Kontexte, Units oder Pflicht-Metadaten.

## Fehlende Funktionen für SKR03-Automatisierung
- SKR03-Import: Parser für SKR03-Exporte (CSV/Excel) mit Beträgen (Soll/Haben/Saldo, Periodenbezug) → internes Ledger-Modell.
- Mapping SKR03 → eBilanz-Taxonomie: Zuordnung der SKR03-Konten zu GAAP/CI- und GCD-Tags (inkl. Vorzeichenlogik, Summenbildung, Pflichtfelder). `taxel/mappings/skr03.csv` deckt nur Kontenbäume, nicht die Ziel-Taxonomie.
- Kontext-/Unit-Building: Generierung von XBRL-Kontexten (Periodenstart/-ende, instant vs. duration) und Währungseinheiten für jede Position.
- Template-/Taxonomie-Auswahl: Lookup-Helfer in `pytaxel/ebilanz/templates.py`, der je nach `tax_type`/`tax_version` das passende Elster-Template und Mapping liefert (mindestens v6.5; später 6.7/6.8).
- XML-Rendering: Erweiterung von `renderer.py`, um vollständige eBilanz-Strukturen (GCD + GAAP) mit Attributen (`contextRef`, `unitRef`, `decimals`, `xsi:nil`) aufzubauen statt nur nackte Tags.
- Validierung/PDF-Preview-Fluss: CLI/Web-Kommando, das nach dem Mapping automatisch `generate → validate --print` durchläuft, damit Anwender das PDF vor dem Senden prüfen können.
- Tests/Fixtures: SKR03-Beispielliste + erwartetes eBilanz-CSV/XML, um Mapping/Rendering stabil zu halten.

## Geplanter Umsetzungsfahrplan
1) **SKR03-Importer definieren**
   - Erwartetes Exportformat dokumentieren (CSV-Spalten wie `konto`, `bezeichnung`, `saldo`, optional Zeitraum).
   - Parser in `pytaxel/ebilanz/parser.py` oder eigenem Modul `skr03_import.py`, der in eine strukturierte Liste von Ledger-Einträgen wandelt.
2) **Mapping-Tabelle ergänzen**
   - Neue Mapping-Datei `taxel/mappings/skr03_to_ebilanz.csv` (oder JSON) mit Spalten `konto`, `tax_tag`, `sign` (+1/-1), `context` (instant/duration), `notes`.
   - Quelle: vorhandene `taxel/mappings/skr03.csv` für Kontenstamm + Rust-Referenz `taxel-xml` für Pflichtfelder und Filter.
3) **Aggregation/Normalisierung**
   - Funktion `map_skr03_to_ebilanz(ledger, mapping)` die Beträge pro eBilanz-Tag summiert, Vorzeichen anpasst, fehlende Pflichtfelder (GCD Stammdaten) mit Defaults/Platzhaltern auffüllt.
   - MasterData um Periodenanfang/-ende und Unit erweitern, damit contexts gebaut werden können.
4) **Template-/Taxonomie-Lookup implementieren**
   - `pytaxel/ebilanz/templates.py`: Pfadfinder für `ebilanz.xml` je Taxonomie (zunächst v6.5, später 6.7/6.8) plus Mapping-Ordner (taxonomy_v6.x).
   - CLI/Web: Standardwerte aus Lookup, Override via Flags/Env ermöglichen.
5) **Renderer auf XBRL anheben**
   - Namespaces/Prefix-Handling robuster machen, Context- und Unit-Knoten erzeugen.
   - Für jede Position: `contextRef`, `unitRef`, `decimals` setzen; fehlende Knoten im Template anlegen.
   - GCD-Bereich (genInfo.*) befüllen, GAAP/CI-Bereich (balanceSheet, incomeStatement) aus Mapping-Daten befüllen.
   - Optionale Textfelder `xsi:nil="true"` setzen, wo kein Wert gemeldet wird, falls Pflicht laut Taxonomie.
6) **End-to-End-Workflow (CLI/Web)**
   - Neues Kommando `import-skr03` o. ä.: Input SKR03-Export → Mapping → eBilanz-XML → `validate --print` → liefert XML + Preview-PDF.
   - Möglichkeit, nur bis zur CSV/XBRL-Erzeugung zu gehen, falls der Nutzer manuell prüfen will.
7) **Tests/Validierung**
   - Pytest-Fälle: SKR03-Mini-Fixture → erwartetes eBilanz-CSV/XML; roundtrip `generate` + `validate` (mit neutraler Hersteller-ID).
   - PDF-Erzeugungstest mit ERiC nur als optionaler/markierter Integrationstest.
8) **Dokumentation**
   - README-Abschnitt „SKR03-Import“ mit Beispiel-Command und Hinweis auf zu liefernde Pflicht-Stammdaten (Firma, Zeitraum, Währung, Testmerker).

## Bibliotheken / Reuse
- **Kein zusätzliches XBRL-Framework nötig**: Das bestehende Template-basierte Rendering reicht, solange wir Context/Unit/Attribute sauber setzen. Optional könnte `lxml` die Namespace-Handhabung vereinfachen, ist aber nicht zwingend.
- **Mapping-Quelle**: Start mit `taxel/mappings/skr03.csv` (Kontenbaum) + eigener SKR03→Taxonomie-Tabelle. Bei Bedarf spätere Automatisierung über Taxonomie-XSDs aus `taxel/test_data/schema`.
- **PDF/Validation**: Bereits über `pytaxel.eric.EricClient` möglich; lediglich neue CLI/Web-Flows verdrahten.
