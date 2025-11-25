Project TODO & Technical Plan  
Python eBilanz with ERiC (Linux, ERiC 41.6.2.0)

This document is the working plan for the Python port of `taxel`, using the ERiC C toolkit as backend. It targets a developer team that knows Python, basic FFI and CLI/web apps, but may not yet know ERiC or eBilanz.

Vision & target users
---------------------
- Vision: Provide a lean, understandable toolchain that makes ERiC-based eBilanz submission accessible to small businesses without requiring large, complex tax software.
- Primary users:
  - small companies and freelancers in Germany who keep their own books and want to submit an eBilanz without a Steuerberater,
  - technically inclined users (or their developers) who prefer a transparent, scriptable workflow over opaque commercial software.
- Usage model:
  - users export accounting data from their bookkeeping software,
  - transform that export into a CSV (or similar structured format),
  - use `pytaxel` to:
    - validate their numbers and structure,
    - generate a valid XBRL/eBilanz XML,
    - preview the submission,
    - send it to the tax authorities via ERiC using their ELSTER certificate.

High‑level goals
----------------
- Provide a Python library that can:
  - generate eBilanz XML/XBRL from structured input (initially CSV + templates, aligned with Rust `taxel`),
  - validate eBilanz XML with ERiC,
  - send eBilanz XML to ELSTER via ERiC and optionally generate a PDF/print confirmation.
- Build a CLI that mirrors the behavior of `taxel` as closely as possible (commands, parameters, exit codes).
- Later: Provide a web GUI (web app) on top of this library, reusing as much logic as possible.
- Target platform: Linux, using the ERiC version included in this repo (`ERiC/Linux-x86_64`).

Key constraints
---------------
- ERiC header files must **not** be redistributed:
  - We may read them locally during development, but must not commit them.
  - All types and function signatures are defined manually in Python based on the official documentation.
- ERiC versions: `eric-rs` bindings cover older versions (up to 40.x); our target is 41.6.2.0, so type definitions, struct version fields, and error codes must be refreshed from the current docs.
- FFI strategy:
  - Use Python’s standard library `ctypes` (no extra FFI dependencies).
  - Handwrite `ctypes.Structure` types and `IntEnum`s for error codes and enums.
- Certificates and PINs:
  - Must never be stored in the repository; they are passed via CLI parameters or environment variables.
  - `_NULL` should be supported as a special value for demo/tests, matching `taxel` behavior.
- Manufacturer ID:
  - The placeholder `74931` is only allowed in test/sample data; for real submissions the user must provide their own ID.
- Usability and diagnostics:
  - Favor readability/maintainability over brevity in code; clear names and small functions.
  - Provide upfront CSV schema checks with clear errors (missing/extra columns, type mismatches).
  - Support template/taxonomy version auto-detection and a command to list available tax types/versions/templates.
  - Map ERiC errors to short, human-readable summaries with pointers to detailed output.
  - Offer safe logging/diagnostics with `--debug` that shows resolved paths, selected template/mapping, ERiC version, while never logging secrets.
  - Allow optional config file/env-based defaults for CLI (certificate paths, PIN env var, template root).

Requirements & scope
--------------------
- Functional scope (initial focus):
  - tax domain: eBilanz only (balance sheet + P&L) for German corporate tax submission; future tax types can be added later.
  - workflows:
    - validate: run ERiC validation on an existing eBilanz XML and present errors/hints clearly,
    - generate: create a valid eBilanz XBRL/XML from CSV + template/mapping,
    - preview: generate a human-readable preview (PDF or similar) via ERiC print functions,
    - send: submit the validated XML to the tax authorities via ERiC using an ELSTER certificate.
  - data input:
    - primary: CSV export derived from bookkeeping software,
    - intermediate/internal: Python data model representing eBilanz concepts,
    - output: XBRL/XML, optional PDF, and machine-readable validation/send results.
- Non-functional requirements (guiding):
  - transparency: users should be able to understand what is sent; configuration and logs must be inspectable,
  - simplicity: installation and usage should be as simple as possible for Linux users with basic CLI knowledge,
  - security: certificates/PINs never persisted in code or logs; temporary files cleaned up; clear instructions for secure usage,
  - performance: validating and sending a single eBilanz should complete interactively (seconds, not minutes) on typical hardware; bulk processing is a stretch goal,
  - portability: target Linux first; keep abstractions clean enough that other platforms could be added later if ERiC supports them.

Phases & milestones (overview)
------------------------------
- M0 – Orientation, vision & architecture: Understand ERiC, `taxel`, and the target architecture; capture vision and requirements.
- M1 – Foundations & data flow: Lock FFI strategy, package layout, and end‑to‑end data flow.
- M2 – Python ERiC wrapper: Stable Python abstraction over ERiC for the eBilanz workflow.
- M2a – Walking skeleton: From Python, validate and send a hard-coded demo XML via ERiC and receive a positive response.
- M3 – eBilanz data & templates: Port `taxel` logic (CSV → XML/XBRL) with templates/mappings.
- M4 – CLI: Python CLI with `taxel`‑like UX, focused on the small-business CSV→eBilanz workflow.
- M5 – Web app: Simple web UI for the same workflows, backed by the Python library.
- M6 – Quality & release: Tests, documentation, packaging, and a realistic release candidate.

M0 – Orientation & architecture
----------------------------------------------------------------------

Goal  
Everyone involved understands ERiC’s architecture, the role of `taxel`, the target users, and the planned Python structure.

Tasks
- Read ERiC documentation:
  - `eric-doc/ERiC-API-Referenz.md`: function signatures, structs, error codes, buffer handling.
  - `eric-doc/ERiC-Entwicklerhandbuch.md`: integration patterns, configuration, deployment.
  - `eric-doc/ERiC-Tutorial.md`: concrete examples for validation and sending (including parameters).
- Inspect ERiC runtime:
  - `ERiC/Linux-x86_64/bin`: list the `*.so` libraries (e.g., `libericapi.so`, `liberictoolkit.so`).
  - `ERiC/Linux-x86_64/include`: headers as reference only (local use, never committed).
  - `ERiC/Linux-x86_64/Beispiel/ericdemo-python/ericdemo`: study the Python demo (parameter setup, calls).
- Understand Rust `taxel` (under `taxel/`):
  - `taxel-cli`: commands `generate`, `validate`, `send`, `extract`, `print`.
  - `taxel-xml`: XML generation, XBRL handling, template integration.
  - `taxel-py`: existing Python integration (inspiration; not a 1:1 port).
  - `templates/`, `mappings/`, `test_data/`: reusable resources (templates, mappings, test cases).
- External reference:
  - `eric-rs` (external repo): inspiration for FFI, error mapping, resource handling.

Deliverable (M0)
- Short architecture and requirements description (e.g., `docs/architecture.md` or a section in this file) that covers:
  - which ERiC libraries we load and how (paths, env vars),
  - which functions we need for validate/preview/send,
  - how error codes are mapped to Python concepts and user-facing messages,
  - which parts of `taxel` we port (logic) vs. reuse (templates, mappings, test data),
  - initial user journeys for small businesses (CSV export → validate → preview → send).

Agent checklist (M0 – Orientation & architecture)
- Before you start:
  - Do not create or modify code (other than `docs/architecture.md` or this plan).
  - Create (or append to) `agents_log.md` to record what you read, key findings, and open questions.
  - Make sure ERiC documentation files and the `taxel/` and `eric-rs/` repos are present.
- While working:
  - Read the three ERiC docs listed above and skim the ERiC Python demo.
  - Skim `taxel-cli`, `taxel-xml`, and `taxel-py` to understand commands and data flow.
  - Skim `eric-rs/eric-sdk` to understand how ERiC init/terminate, error codes, and certificates are handled.
  - Write down, in `docs/architecture.md` (or a dedicated section here):
    - high-level component diagram (pytaxel.eric, pytaxel.ebilanz, CLI, Web),
    - which ERiC libraries and functions are needed for validate/preview/send,
    - the user journey for a small business from CSV export to send.
- You are done with M0 when:
  - there is a short but concrete architecture/requirements document,
  - ERiC, `taxel`, and `eric-rs` roles are clearly described,
  - open questions (if any) are listed explicitly for a human to answer.

----------------------------------------------------------------------
M1 – Foundations & data flow
----------------------------------------------------------------------

Goal  
Define project structure, FFI strategy, and a clear end‑to‑end data flow.

1. Lock FFI strategy (ctypes, no headers in repo)
- Module `pytaxel/eric/loader.py`:
  - Responsible for loading ERiC shared libraries (`ctypes.CDLL`).
  - Default path: `ERiC/Linux-x86_64` relative to the repo root.
  - Configurable via environment variables (e.g., `ERIC_HOME`).
  - Should produce clear error messages when libraries are missing (hinting at `LD_LIBRARY_PATH` and expected paths).
- Type definitions:
  - `pytaxel/eric/types.py`:
    - `ctypes.Structure` for relevant structs (print, encryption, certificate parameters, etc.).
    - `enum.IntEnum` for ERiC error codes and status enums.
  - In comments: reference to ERiC documentation (e.g., “see `eric_druck_parameter_t` in `ericapi.h` / API reference page xx”).

2. Define data flow (as close to `taxel` as possible)
- Target data flow:
  - CSV with accounting/tax data exported from bookkeeping software,
  - → internal Python data model (domain objects for eBilanz),
  - → XML/XBRL via templates/mappings,
  - → ERiC validation,
  - → optional sending + PDF confirmation.
- Reuse:
  - `taxel/templates`: XBRL/eBilanz templates.
  - `taxel/mappings`: mapping from CSV columns to XBRL positions.
  - `taxel/test_data`: example CSV/XML for tests and manual validation.
- Python package layout (proposed):
  - `pytaxel/eric/` – FFI bindings, error handling, high‑level ERiC API.
  - `pytaxel/ebilanz/` – CSV/XBRL logic (port of `taxel-xml`).
  - `pytaxel/cli/` – CLI commands.
  - `pytaxel/web/` – web API and UI (later phase).

Deliverable (M1)
- Directory structure in place, modules with docstrings and TODO markers.
- README section: “Vision, architecture & data flow” explaining the ERiC path, CSV→eBilanz workflow, and reused `taxel` resources.

Agent checklist (M1 – Foundations & data flow)
- Before you start:
  - Read `docs/architecture.md` (or the M0 section) so you follow the agreed structure.
  - Update `agents_log.md` with what you plan to scaffold and any questions to carry forward.
- While working:
  - Create the `pytaxel/` package and the subpackages `eric/`, `ebilanz/`, `cli/`, `web/`.
  - In each package, create minimal `__init__.py` and stub modules (`loader.py`, `types.py`, `facade.py`, etc.) with docstrings and TODOs.
  - Document the end-to-end CSV→data model→XML→ERiC flow in the README section.
  - Do not implement ERiC calls or XML generation yet; only structure and documentation.
- You are done with M1 when:
  - all planned modules exist (even if mostly empty) and import cleanly,
  - the README contains a clear description of the data flow and where ERiC fits,
  - no business logic has been implemented prematurely.

M2 – Python ERiC wrapper
----------------------------------------------------------------------

Goal  
Provide a stable Python interface to ERiC for eBilanz use cases: validate, send, print/PDF.

1. Library loading & configuration
- Implement `pytaxel/eric/loader.py`:
  - Functions such as:
    - `load_ericapi() -> ctypes.CDLL`
    - `load_erictoolkit() -> ctypes.CDLL`
    - `check_eric_available() -> None` (raises a clear exception if something is missing).
  - Configuration:
    - Environment variable `ERIC_HOME` for the base directory,
    - support `PLUGIN_PATH`-style overrides (as used in `eric-rs`) for plugin loading/log paths,
    - optional explicit path parameters (e.g., for tests).

2. Types & error handling
- `pytaxel/eric/types.py`:
  - Structs, for example:
    - print parameters (`eric_druck_parameter_t`),
    - encryption parameters (`eric_verschluesselungs_parameter_t`),
    - certificate parameters (`eric_zertifikat_parameter_t`) including paths, PIN, etc.
  - Buffer types for return values:
    - pointers to `c_char` / `c_void_p`,
    - helper functions to allocate/free via ERiC functions where required.
- Ensure struct `version` fields and layout match ERiC 41.6.2.0 docs (values differ across releases; do not assume the older `eric-rs` defaults).
- Keep owning Python objects alive while passing pointers into ERiC (mirror the lifetime safety notes from `eric-rs`/Rust wrappers).
- `pytaxel/eric/errors.py`:
  - `EricError(Exception)` with:
    - error code,
    - source (API/toolkit),
    - human‑readable description.
  - Mapping functions:
    - `error_code_to_message(code: int) -> str`
    - seed mappings from `eric-rs` error code lists but update/extend for 41.6.2.0 using current ERiC docs.
  - Helper:
    - `check_eric_result(code: int, context: str = "") -> None` (raises `EricError` on failure).

3. ERiC function bindings
- `pytaxel/eric/api.py`:
  - Bind, based on `ericapi.h` and the API reference, the functions that `taxel` uses for eBilanz:
    - version info (e.g., `eric_get_version` or equivalent) to verify runtime,
    - initialization/shutdown (if required, e.g., `eric_init`, `eric_terminate`),
    - XML validation (appropriate ERiC function for eBilanz),
    - sending XML to ELSTER,
    - generating/printing a PDF confirmation document.
  - For each function:
    - set `restype` and `argtypes`,
    - provide a Python wrapper that:
      - converts strings to UTF‑8 bytes,
      - fills parameter structs,
      - allocates buffers,
      - calls `check_eric_result`,
      - converts results back to Python objects (e.g., `Path`, `str`).

4. High‑level facade
- `pytaxel/eric/facade.py`:
  - High‑level functions used by the rest of the code, for example:
    - `validate_xml(xml_path: Path, tax_type: str, tax_version: str, ...) -> ValidationResult`
    - `send_xml(xml_path: Path, certificate: Optional[Path], pin: Optional[str], ...) -> SendResult`
    - `print_confirmation(xml_path: Path, output_pdf: Path, ...) -> None`
  - `ValidationResult` / `SendResult` as small data classes with:
    - success/failure flag,
    - list of errors/warnings,
    - optional raw ERiC response for debugging.
  - Provide an idiomatic context manager (e.g., `eric_session()` or an `EricSession` class) that wraps ERiC initialization and teardown so callers can use `with eric_session() as eric:` to ensure clean setup and cleanup even on errors.

Deliverable (M2)
- Small example script in the repo (e.g., `examples/validate_with_eric.py`) that:
  - validates a test XML with ERiC (without sending),
  - prints status and any errors to stdout.
- Pytest tests for:
  - version query,
  - error mapping,
  - at least one successful and one failing validation (using demo XMLs).

Agent checklist (M2 – Python ERiC wrapper)
- Before you start:
  - Confirm that M1 structure exists and imports without errors.
  - Note in `agents_log.md` the test XMLs and ERiC paths you will use.
- While working:
  - Implement `pytaxel/eric/loader.py` to locate and load ERiC libraries using `ERIC_HOME`/`PLUGIN_PATH`.
  - Implement `pytaxel/eric/types.py` with only the structs/enums needed for validate/preview/send.
  - Implement `pytaxel/eric/errors.py` with error code mapping and an `EricError` exception.
  - Implement `pytaxel/eric/api.py` bindings and `pytaxel/eric/facade.py` high-level functions.
  - Add an `eric_session()` (or `EricSession`) context manager that calls init/terminate correctly and is used inside the example script and tests.
  - Add basic pytest tests for version, simple validate success, and a failing validate.
  - Do not touch CSV/XML generation or CLI/web code in this milestone.
- You are done with M2 when:
  - you can run the example script to validate a demo XML,
  - tests for version/error/validate pass,
  - ERiC initialization/teardown is always done via the context manager.

M2a – Walking skeleton (end-to-end ERiC call)
----------------------------------------------------------------------

Goal  
Prove that Python can drive a full ERiC validation and (test) send round-trip using a hard-coded XML, without yet integrating CSV or the full data model.

Tasks
- Use the M2 wrapper and facade to:
  - validate a known-good demo XML (e.g., from ERiC docs) and capture the response,
  - send the same XML to the ERiC test endpoint using a test certificate (if available) and print the confirmation or send result.
- Implement a tiny CLI command or script (e.g., `python -m pytaxel.eric.walking_skeleton`) that:
  - initializes ERiC,
  - runs validate + optional send,
  - prints a concise summary (success/failure, key error codes, location of log files).
- Document any quirks in paths, environment variables, or ERiC configuration discovered during this step.

Deliverable (M2a)
- A reproducible “walking skeleton” demo documented in README, proving the Python→ERiC integration works end-to-end for validate/send on a single hard-coded XML.

Agent checklist (M2a – Walking skeleton)
- Before you start:
  - Ensure M2 example and tests are passing.
  - Note in `agents_log.md` which demo XML and cert (if any) you will use.
- While working:
  - Choose one known-good demo XML (from ERiC docs or test data) and hard-code its path in a small script/command.
  - Use `eric_session()` to:
    - validate this XML,
    - optionally send it using a test certificate (if configured),
    - print a concise summary (success/failure, key codes, log file location).
  - Add README instructions explaining how to run this walking skeleton and which env vars/cert files are needed.
  - Do not introduce CSV parsing or template logic here; focus only on a single end-to-end ERiC call.
- You are done with M2a when:
  - a developer (or agent) can follow the README to validate (and optionally send) the hard-coded XML via Python,
  - any ERiC configuration quirks are documented.

M3 – eBilanz data model & template port
----------------------------------------------------------------------

Goal  
Port the CSV→XML/XBRL logic from `taxel` to Python, reusing templates and mappings.

Tasks
- Analyze `taxel-xml`:
  - how templates are loaded,
  - how mappings are defined (CSV column → XBRL field),
  - how different eBilanz schema versions are handled (e.g., 6.4 vs. 6.5).
- Python data model in `pytaxel/ebilanz/`:
  - Data classes for:
    - master data (company, tax ID, period),
    - balance sheet and P&L positions,
    - metadata (schema version, reporting type).
  - CSV loader:
    - robust to missing/additional columns,
    - clear error messages.
  - Renderer:
    - builds an internal XML tree (e.g., `xml.etree.ElementTree` or similar),
    - fills it using mappings,
    - writes XML/XBRL to disk.
- Reuse:
  - Read templates and mappings directly from the Rust `taxel` folder initially.
  - Later, consider copying them into a dedicated Python data directory if packaging requires it.
- Tests:
  - For selected test cases:
    - generate XML with Rust `taxel`,
    - process the same CSV with Python,
    - compare the resulting XMLs (ignoring expected differences such as timestamps).

Deliverable (M3)
- Python function:
  - `generate_xml_from_csv(csv_path, template_path, mapping_path, output_xml_path, ...)`
  - plus tests with reference output from Rust `taxel`.

Agent checklist (M3 – eBilanz data & template port)
- Before you start:
  - Confirm M2/M2a wrapper and walking skeleton work and are not being changed in this step.
  - Log in `agents_log.md` which templates/mappings and fixtures you will compare against.
- While working:
  - Analyze `taxel-xml` and document the mapping rules and template usage for eBilanz.
  - Design and implement a Python data model in `pytaxel/ebilanz/` that can represent the required eBilanz structures.
  - Implement CSV loading and mapping into this data model, with upfront schema validation and clear error messages.
  - Implement XML/XBRL generation using the existing `taxel` templates/mappings.
  - Write pytest tests that compare a small set of Python-generated XMLs with Rust `taxel` outputs for the same inputs.
  - Do not modify ERiC wrapper behavior here; only call it if needed for verification.
- You are done with M3 when:
  - CSV→data model→XML conversion works for at least the agreed reference fixtures,
  - tests comparing against Rust `taxel` pass for those fixtures.

M4 – CLI (Python)
----------------------------------------------------------------------

Goal  
Provide a Linux CLI that feels like `taxel` to end users, but runs on the Python library.

Tasks
- Choose CLI framework:
  - Start with `argparse` (no extra dependency),
  - optionally move to `typer` if developer ergonomics justify the dependency.
- Implement commands:
  - `generate`:
    - `--csv-file`, `--template-file`, `--output-file`, optional mapping configuration.
  - `extract`:
    - extract values from an existing XML into a CSV (to the extent supported by `taxel`).
  - `validate`:
    - `--xml-file`, `--tax-type`, `--tax-version`,
    - options for test vs. production mode (if ERiC APIs distinguish these).
  - `send`:
    - same as `validate` plus:
      - `--certificate`, `--pin`, `--pin-env`, `_NULL` support as in `taxel`,
      - optional `--print` with PDF file path.
- Error/logging behavior:
  - Translate ERiC error codes and internal errors into clear CLI messages.
  - Align process exit codes with Rust `taxel` (e.g., 0 = success, >0 = error).
  - `--verbose`/`--debug`:
    - additional logs (e.g., paths in use, chosen templates/versions).
  - Configuration convenience:
    - support configuration via env vars (e.g., `ERIC_HOME`, `CERTIFICATE_PATH`, `CERTIFICATE_PASSWORD`, PIN env var),
    - optionally support a simple `.env` file (e.g., using `python-dotenv`) for local development so users can avoid long command lines while keeping secrets out of the codebase.
- Documentation:
  - README examples:
    - `generate`, `validate`, `send` in common combinations.

Deliverable (M4)
- Installable CLI (e.g., via `pip install .`), providing a `taxel-py` (or similar) command.
- Short usage section mirroring the Rust `taxel` examples in Python syntax.

Agent checklist (M4 – CLI)
- Before you start:
  - Ensure M2/M2a (ERiC wrapper) and M3 (CSV/XML generation) are stable.
  - Record in `agents_log.md` the CLI commands and fixtures you will test.
- While working:
  - Design the CLI commands and options to mirror `taxel` (at least: `generate`, `validate`, `send`, optionally `extract`).
  - Implement the CLI using the existing library functions from `pytaxel/eric` and `pytaxel/ebilanz` (no duplicated logic in the CLI layer).
  - Add support for environment-based configuration and, optionally, `.env`-based configuration for local development.
  - Implement structured error handling so that ERiC and validation errors are printed clearly and exit codes match expectations.
  - Add pytest-based CLI integration tests using `taxel/test_data` fixtures.
  - Do not implement web endpoints or UI here.
- You are done with M4 when:
  - the CLI can generate, validate, and (test-)send eBilanz XMLs via ERiC for the reference fixtures,
  - CLI tests and wrapper tests pass.

M4a – CLI parity with Rust taxel
----------------------------------------------------------------------

Goal  
Align the Python CLI behavior to ≥99% functional parity with the Rust `taxel` CLI (commands, flags, defaults, outputs).

Tasks
- Command coverage:
  - add `extract` (XML → CSV) with the same defaults as Rust,
  - ensure `generate` supports optional CSV input and default output directory like Rust,
  - mirror `--verbose/--debug` flag semantics to provide comparable diagnostics.
- Arguments & defaults:
  - replicate tax-type/version defaults and allowed values,
  - keep `--print` behavior (preview for validate, confirmation for send) consistent,
  - confirm env var/config shortcuts don’t break Rust-compatible invocations.
- Outputs and exit codes:
  - write validation and server responses to files (same filenames) in the chosen log dir,
  - print ERiC return codes to stdout/stderr in line with Rust,
  - harmonize exit codes for success/error paths.
- Tests:
  - CLI integration tests that compare behavior/outputs (CSV/XML, log files) against the Rust CLI for shared fixtures.

Deliverable (M4a)
- Python CLI that produces the same observable behavior (commands, flags, defaults, outputs, exit codes) as Rust `taxel` for the covered flows.

Agent checklist (M4a – CLI parity)
- Before you start:
  - Note the current deltas vs. Rust CLI in `agents_log.md`.
- While working:
  - Implement `extract` and align all command defaults/args to Rust.
  - Add response logging and ERiC code printing to match Rust outputs.
  - Update help/README snippets if flags/defaults changed.
  - Add/adjust CLI tests that assert parity with Rust outputs for reference fixtures.
- You are done with M4a when:
  - generate/validate/send/extract behave the same as Rust taxel for the tested cases, and tests reflect this.

M5 – Web app
----------------------------------------------------------------------

Goal  
Provide a web interface that offers the same core functionality as the CLI, but via HTTP and a browser UI.

Tasks
- Backend (e.g., FastAPI) in `pytaxel/web/`:
  - Endpoints:
    - `POST /generate`
      - upload CSV + parameters → returns XML file or download link.
    - `POST /validate`
      - upload XML → returns JSON validation result (error list, OK/not OK).
    - `POST /send`
      - upload XML + certificate/PIN details → returns send result and PDF link.
  - Security:
    - handle certificate/PIN only in memory for the duration of the request; do not persist.
    - ensure each HTTP request runs in a clean ERiC context (e.g., by using the `eric_session()` context manager per request) so that log handles and other ERiC state are not shared across requests.
    - delete temporary files after processing.
  - Logging:
    - technical logs without sensitive content.
- Frontend:
  - Simple HTML forms or a SPA:
    - upload CSV/XML,
    - choose tax type/version,
    - input certificate path/PIN,
    - show results/errors and provide download links.
- Deployment:
  - basic instructions for local development (e.g., `uvicorn`),
  - optional Dockerfile that bundles Python + ERiC runtime.

Deliverable (M5)
- A running development server that can:
  - generate XML from CSV,
  - validate XML,
  - later: send XML (initially using a test certificate).

Agent checklist (M5 – Web app)
- Before you start:
  - Verify that CLI/library flows from M4 are stable and documented.
  - Note in `agents_log.md` the planned endpoints and e2e flows to cover.
- While working:
  - Implement backend endpoints that call into the same library functions used by the CLI (no duplicated business logic).
  - Ensure each HTTP request uses a fresh `eric_session()` so ERiC state (including logs) is isolated per request.
  - Implement minimal UI to cover the key flows: CSV upload→generate, XML upload→validate, XML send.
  - Ensure secrets (cert paths, PINs) are only handled in memory and never logged.
  - Add at least basic automated e2e tests (headless) for the main flows.
  - Do not change library behavior in a web-specific way; the web layer should stay thin.
- You are done with M5 when:
  - a developer can run the dev server, complete the core workflows via browser/API, and e2e tests pass for those flows.

M6 – Quality, tests & release
----------------------------------------------------------------------

Goal  
High reliability and clear documentation; prepare a release candidate.

Tasks
- Test strategy (four tracks):
  1) ERiC runtime validation (per ERiC handbook):
     - run the upstream demo scripts (`startedemo.sh -n` etc.) for a small matrix of tax types/versions;
       confirm "Verarbeitung fehlerfrei." and expected log output; include a cert-backed variant if available.
  2) Python FFI (wrapper) tests (pytest, modeled after `eric-rs`):
     - init/terminate, version call;
     - validate a known-good XML (demo), validate a known-bad XML, and assert ERiC error codes/messages;
     - buffer ownership/lifetime checks (ensure owning Python objects outlive pointers);
     - environment resolution tests (`ERIC_HOME`, `PLUGIN_PATH`).
  3) CLI integration tests (pytest invoking CLI) using `taxel/test_data` fixtures:
     - `generate` produces XML matching golden outputs (ignoring timestamps where needed);
     - `validate` returns ERiC OK or mapped errors/hints, exit codes align with taxel;
     - `send` dry-run/test-cert flow respects `_NULL`/env options; no secrets in output; exit codes align.
  4) GUI end-to-end tests (headless, e.g., Playwright/Selenium):
     - upload CSV → generate XML → download;
     - upload XML → validate → display errors/hints;
     - send flow with test cert/PIN handling (mock if real send not allowed);
     - assert no secrets in logs and temp files are cleaned.
  - Define a minimal matrix of tax types/versions (e.g., Bilanz 6.4/6.5) across validate/send, with and without certificate.
  - Comparison with Rust `taxel`: for selected scenarios, compare generated XML and CLI exit behavior.
- Code quality:
  - Optional tools (if the team agrees): `flake8`/`ruff`, `black`.
  - Keep the style consistent with existing Python demos (4 spaces, descriptive names).
- Packaging:
  - `pyproject.toml`/`setup.cfg` for a PyPI‑ready distribution.
  - CLI entry point (e.g., `pytaxel.cli:main`).
  - Long‑term optional: standalone binary artifacts (zipapp/pex/pyinstaller).
- Documentation:
  - Extend `AGENTS.md` and potentially a `docs/` directory with:
    - setup instructions for ERiC on Linux,
    - instructions for running demos/tests,
    - security notes about certificates, PINs, and manufacturer ID.

Deliverable (M6)
- Tagged release candidate in the repo,
- up‑to‑date documentation for developers and technical users,
- agreed follow‑up roadmap (e.g., platform extensions, additional tax types).

M7 – Web UI parity & CLI alignment
----------------------------------------------------------------------

Goal  
Adapt the web UI/backend so that it mirrors the updated CLI behavior (including M4a parity changes) with ≥99% functional match to Rust `taxel`.

Tasks
- API/behavior alignment:
  - expose `extract`, `generate`, `validate`, `send` endpoints with the same defaults/flags as the CLI,
  - propagate tax-type/version defaults and allowed values,
  - support `--print` equivalents (preview for validate, confirmation for send) and log-dir handling consistent with CLI.
- Output/log parity:
  - persist validation/server responses to the same filenames/locations used by CLI (per-request temp/log dir),
  - return ERiC codes and messages in responses mirroring CLI output semantics.
- Config & security:
  - honor the same env/config options (e.g., ERIC_HOME override, certificate/PIN env vars) without leaking secrets,
  - ensure request isolation for ERiC state and temp files.
- Tests:
  - add e2e/API tests comparing outputs/log artifacts against CLI behavior for shared fixtures,
  - cover the new `extract` flow and print/preview options.
- UX updates:
  - update UI labels/help to reflect new commands/flags/defaults.

Deliverable (M7)
- Web UI and API that behave like the parity-updated CLI for the core flows, with tests demonstrating matching outputs/logs.

Agent checklist (M7 – Web UI parity)
- Before you start:
  - Record current web vs. CLI deltas in `agents_log.md`.
- While working:
  - Align endpoints/params/defaults with the CLI parity spec.
  - Ensure response/log file handling matches CLI conventions.
  - Update UI/help text accordingly.
  - Add e2e/API tests covering extract/generate/validate/send with print/preview variants.
- You are done with M7 when:
  - web interactions produce the same observable results (including log files and ERiC codes) as the parity CLI for reference fixtures/tests.

Notes for contributors
----------------------
- Never commit ERiC headers or binaries beyond what already exists under `ERiC/`.
- Keep the FFI layer thin:
  - raw `ctypes` usage should live only in the `pytaxel/eric` namespace,
  - the rest of the application should work with clean Python types and exceptions.
- Favor readability and maintainability over brevity:
  - prefer clear names, small functions, and explicit code to clever one-liners,
  - keep code paths easy to scan for future contributors.
- Align behavior with Rust `taxel` where possible:
  - same or very similar CLI options,
  - reuse of templates/mappings/test data,
  - comparable error messages and exit codes.
- Pull requests should be scoped around the milestones M0–M6 and keep changes focused on one step at a time.
