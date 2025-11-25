# pytaxel

## Vision, Architecture & Data Flow
- CSV export from bookkeeping → internal eBilanz domain model → populate XBRL/XML via templates/mappings (reusing `taxel/templates`, `taxel/mappings`, `taxel/test_data`) → validate → optional send/print.
- ERiC path: load `libericapi.so` and plugins from `ERiC/Linux-x86_64` (configurable later via env like `ERIC_HOME`/`PLUGIN_PATH`), call `EricBearbeiteVorgang` through `pytaxel.eric` to validate/send, with printable PDF via ERiC’s druck parameters.
- Python layout: `pytaxel/eric` (ctypes loader/types/errors/facade for ERiC), `pytaxel/ebilanz` (CSV→model→XBRL logic mirroring Rust taxel), `pytaxel/cli` (commands matching taxel CLI for generate/validate/send/preview).
- Workflow alignment: mirror Rust `taxel` commands and data expectations so fixtures/templates stay shared; keep raw ctypes isolated inside `pytaxel.eric` and surface high-level helpers to CLI/web layers.
- Security/paths: certificates and PINs supplied via CLI/env (no repo storage), manufacturer ID placeholder only for tests; logging directed to user-specified directory alongside ERiC log output.

## CLI Usage
- Extract CSV from XML: `python -m pytaxel.cli.main extract --xml-file taxel/test_data/taxonomy/v6.5/sample_expected.xml --output-file /tmp/out.csv` (defaults to current dir if not given).
- Generate XML: `python -m pytaxel.cli.main generate --csv-file taxel/test_data/taxonomy/v6.5/sample.csv --template-file taxel/templates/elster_v11/taxonomy_v6.5/ebilanz.xml --output-file /tmp/ebilanz.xml` (`--csv-file` optional; defaults to current dir for output).
- Validate XML: `python -m pytaxel.cli.main validate --xml-file /tmp/ebilanz.xml --tax-type Bilanz --tax-version 6.5 --log-dir /tmp/eric-logs [--print /tmp/preview.pdf]` (writes `validation_response.xml` / `server_response.xml` to log dir; default log dir is CWD).
- Send XML: `python -m pytaxel.cli.main send --xml-file /tmp/ebilanz.xml --tax-type Bilanz --tax-version 6.5 --certificate /path/to/cert.pfx --pin 123456 [--print /tmp/confirmation.pdf] [--log-dir /tmp/eric-logs]`.
- Add `--verbose`/`--debug` to any command to log resolved paths and ERiC responses; response code is printed like the Rust CLI.

## Web API (dev)
- Start dev server (needs `fastapi` + `uvicorn` installed): `uvicorn pytaxel.web.app:app --reload`
- Simple forms at `http://localhost:8000/` allow manual uploads for:
  - `POST /generate` (CSV upload → XML download),
  - `POST /validate` (XML upload → JSON result),
  - `POST /send` (XML + certificate + PIN → JSON or PDF confirmation).
