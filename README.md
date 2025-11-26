# pytaxel

pytaxel is a Python port of the Rust eBilanz toolkit
[`taxel`](https://github.com/quambene/taxel). It aims to bring the same
CSV-driven workflows to Python, reusing `taxel`’s templates, mappings and
test data, and adding a web UI on top of a CLI.

- Reuses templates, mappings, and test data from `taxel` (vendored in this repo
  under `taxel/`),
- uses the external ERiC binding library [`eric-py`](https://github.com/Uli-Z/eric-py)
  (`eric_py`) to talk to the official ERiC C API, and
- exposes CLI and web entry points for CSV→eBilanz→ERiC workflows.

The Rust project `taxel` has already done a lot of groundwork by providing a
CSV-based workflow: users can interact with eBilanz data via relatively simple
CSV files instead of editing XBRL/XML directly. `pytaxel` is a Python port of
these ideas, with an additional web UI on top of the CLI. The implementation is
still under active development.

A substantial portion of this repository was created using agentic-coding
workflows with OpenAI GPT 5.1, guided by the plans in `agents_plan.md` and the
prompt structures in `prompts.md`, and then iterated with manual review.

This setup is currently tested primarily with ERiC 41.6.2.0 on Linux
(`ERiC-41.6.2.0/Linux-x86_64`). Other ERiC versions may work but should be
verified carefully in your own environment.

## What is eBilanz and why is it hard?

eBilanz is the electronic balance sheet format used in Germany to submit
annual financial statements to the tax authorities. Technically it is a large
XBRL taxonomy (with GCD and GAAP/CI parts) with strict rules about:

- which fields are required in which situations,
- how contexts (periods, instants) and units (currencies) must be modeled,
- how signs, aggregations, and consistency checks work, and
- how the XML must be packaged, validated, and transmitted via ERiC.

For most users this is complex and tedious: you need to map local charts of
accounts (e.g. SKR03) to taxonomy positions, generate valid XBRL with all
contexts/units, and then pass it through ERiC for validation and submission.
`pytaxel` aims to hide most of that complexity behind reusable templates,
mappings, and a small set of CLI/web commands.

## Vision, Architecture & Data Flow
- CSV export from bookkeeping → internal eBilanz domain model → populate XBRL/XML via templates/mappings (reusing `taxel/templates`, `taxel/mappings`, `taxel/test_data`) → validate → optional send/print.
- ERiC path: load `libericapi.so` and plugins from `ERiC/Linux-x86_64` (configurable via env like `ERIC_HOME`), and use the external `eric-py` (`eric_py`) library to call `EricBearbeiteVorgang` for validate/send, with printable PDF via ERiC’s druck parameters.
- Python layout: `pytaxel/ebilanz` (CSV→model→XBRL logic mirroring Rust taxel), `pytaxel/cli` (commands matching taxel CLI for generate/validate/send/preview), `pytaxel/web` (web API), plus the separate `eric-py` project providing the ERiC bindings.
- Workflow alignment: mirror Rust `taxel` commands and data expectations so fixtures/templates stay shared; keep raw ctypes isolated inside `eric-py` and surface high-level helpers to CLI/web layers.
- Security/paths: certificates and PINs supplied via CLI/env (no repo storage), manufacturer ID placeholder only for tests; logging directed to user-specified directory alongside ERiC log output.

## CLI Usage
- Extract CSV from XML: `pytaxel extract --xml-file taxel/test_data/taxonomy/v6.5/sample_expected.xml --output-file /tmp/out.csv` (defaults to current dir if not given).
- Generate XML: `pytaxel generate --csv-file taxel/test_data/taxonomy/v6.5/sample.csv --template-file taxel/templates/elster_v11/taxonomy_v6.5/ebilanz.xml --output-file /tmp/ebilanz.xml` (`--csv-file` optional; defaults to current dir for output).
- Validate XML: `pytaxel validate --xml-file /tmp/ebilanz.xml --tax-type Bilanz --tax-version 6.5 --log-dir /tmp/eric-logs [--print /tmp/preview.pdf]` (writes `validation_response.xml` / `server_response.xml` to log dir; default log dir is CWD).
- Send XML: `pytaxel send --xml-file /tmp/ebilanz.xml --tax-type Bilanz --tax-version 6.5 --certificate /path/to/cert.pfx --pin 123456 [--print /tmp/confirmation.pdf] [--log-dir /tmp/eric-logs]`.
- Add `--verbose`/`--debug` to any command to log resolved paths and ERiC responses; response code is printed like the Rust CLI. You can also invoke the CLI via `python -m pytaxel.cli.main ...` if you prefer.

## Web API (dev)
- Start dev server (needs `fastapi` + `uvicorn` installed): `uvicorn pytaxel.web.app:app --reload`
- Simple forms at `http://localhost:8000/` allow manual uploads for:
  - `POST /generate` (CSV upload → XML download),
  - `POST /validate` (XML upload → JSON result),
  - `POST /send` (XML + certificate + PIN → JSON or PDF confirmation).

## Testing

Tests are organized in layers; you can run as much as your environment
supports:

- eBilanz core (no ERiC required):
  - `pytest tests/test_ebilanz_generation.py`
  - exercises CSV→model→XML rendering against `taxel/test_data` fixtures.
- ERiC error handling (requires `eric-py` importable but no ERiC libs):
  - `PYTHONPATH=../eric-py:. pytest tests/test_eric_errors.py`
  - checks `eric_py`-based error and enum handling used by pytaxel.
- CLI e2e with ERiC (requires ERiC + `ERIC_HOME` + `eric-py`):
  - `PYTHONPATH=../eric-py:. pytest tests/test_cli_integration.py`
  - runs `generate`, `extract` and `validate` through the CLI using `taxel`
    fixtures and the ERiC backend from `eric-py`.
- Web API (optional, needs `fastapi`, `uvicorn`):
  - install extras: `pip install -e .[web,dev]`
  - run: `PYTHONPATH=../eric-py:. pytest tests/test_web_api.py`

In CI or a fully provisioned dev environment, you can simply run `pytest`
from the repository root to execute all tests for which the dependencies
are available.
