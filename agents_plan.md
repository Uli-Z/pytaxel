Project TODO & Technical Plan  
Python eBilanz with ERiC (Linux, ERiC 41.6.2.0)

This document is the working plan for the Python port of `taxel`, using the ERiC C toolkit as backend. It targets a developer team that knows Python, basic FFI and CLI/web apps, but may not yet know ERiC or eBilanz.

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

Phases & milestones (overview)
------------------------------
- M0 – Orientation & architecture: Understand ERiC, `taxel`, and the target architecture.
- M1 – Foundations & data flow: Lock FFI strategy, package layout, and data flow.
- M2 – Python ERiC wrapper: Stable Python abstraction over ERiC for the eBilanz workflow.
- M3 – eBilanz data & templates: Port `taxel` logic (CSV → XML/XBRL) with templates/mappings.
- M4 – CLI: Python CLI with `taxel`‑like UX.
- M5 – Web app: Web API + UI on top of the library.
- M6 – Quality & release: Tests, documentation, packaging, release candidate.

M0 – Orientation & architecture
----------------------------------------------------------------------

Goal  
Everyone involved understands ERiC’s architecture, the role of `taxel`, and the planned Python structure.

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
- Short architecture description (e.g., `docs/architecture.md` or a section in this file) that covers:
  - which ERiC libraries we load,
  - which functions we need,
  - how error codes are mapped to Python,
  - which parts of `taxel` we port (logic) vs. reuse (templates, mappings, test data).

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
  - CSV with accounting/tax data,
  - → internal data model,
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
- README section: “Architecture & data flow” explaining the ERiC path and reused `taxel` resources.

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

Deliverable (M2)
- Small example script in the repo (e.g., `examples/validate_with_eric.py`) that:
  - validates a test XML with ERiC (without sending),
  - prints status and any errors to stdout.
- Pytest tests for:
  - version query,
  - error mapping,
  - at least one successful and one failing validation (using demo XMLs).

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
- Documentation:
  - README examples:
    - `generate`, `validate`, `send` in common combinations.

Deliverable (M4)
- Installable CLI (e.g., via `pip install .`), providing a `taxel-py` (or similar) command.
- Short usage section mirroring the Rust `taxel` examples in Python syntax.

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

M6 – Quality, tests & release
----------------------------------------------------------------------

Goal  
High reliability and clear documentation; prepare a release candidate.

Tasks
- Test strategy:
  - Pytest suite:
    - unit tests for the FFI wrapper (no network),
    - integration tests for the CLI using `taxel/test_data`.
  - Manual tests:
    - validate different eBilanz versions,
    - send with a test certificate (if available),
    - error cases (broken XML, wrong certificate/PIN).
  - Comparison with Rust `taxel`:
    - compare generated XMLs for selected scenarios.
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
