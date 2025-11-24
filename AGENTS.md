# Repository Guidelines

## Project Structure & Module Organization
- `ERiC-41.6.2.0/Dokumentation` hosts PDF guides, schemas, and tutorial chapters that describe each ERiC interface and expected payloads.
- `ERiC-41.6.2.0/Linux-x86_64` contains runtime assets: `bin`, `include`, and `lib` for the native toolkit plus the `Beispiel` tree with language-specific demos.
- Demos are organized by language under `Beispiel/<language>`; e.g., `Beispiel/ericdemo-python/ericdemo` bundles the runnable Python sample, argument parser, and utility modules.
- The Rust reference implementation lives in `taxel/` (vendored copy of https://github.com/quambene/taxel) and provides the baseline for features, templates, mappings, and tests.
- The new Python implementation will live under a `pytaxel/` package (library + CLI + later web app) and should mirror the structure and behavior of `taxel` where reasonable.

## Build, Test, and Development Commands
- There is no automated build in this repo; the ERiC binaries arrive prebuilt in `Linux-x86_64`. For manual verification of the upstream ERiC demo run the script after installing Python ≥3.7:
  ```sh
  sh ERiC-41.6.2.0/Linux-x86_64/Beispiel/ericdemo-python/startedemo.sh -v ESt_2020 -x ESt_2020.xml
  ```
  Add `-c test-softidnr-pse.pfx -p 123456` to exercise certificate-backed transport.
- Use `sh .../startedemo.sh -n` to validate XML without sending, and `-e -s <output>` to test decryption flows.
- For the Python library and CLI (`pytaxel`), use a standard virtual environment, run unit tests with `pytest`, and invoke the CLI via `python -m pytaxel.cli` or an installed entry point (to be defined as the project evolves).

## Coding Style & Naming Conventions
- Use English for all code, comments, and documentation in this repo; German domain terms (e.g., eBilanz, ELSTER, Hersteller-ID) are fine as technical vocabulary.
- Follow the existing Python style: 4-space indents, descriptive functions (`ericdemo.py` and helpers) and docstrings that explain purpose.
- Keep module names lowercase with underscores (e.g., `ericutilities.py`, `eric_loader.py`), while classes use PascalCase (`EricCertificate`, `EricError`).
- Preserve the German/English naming mix for domain terms inside demos and business logic to stay consistent with the upstream examples and ERiC documentation.
- Prefer readability and maintainability over brevity: clearer names, small functions, and explicit code even if it adds lines. Avoid over-clever one-liners; favor code that future contributors can scan quickly.

## Testing Guidelines
- Testing is primarily manual for ERiC itself; run the starter scripts above and inspect console output for a message equivalent to "processing successful" (`Verarbeitung fehlerfrei.`) or for certificate errors.
- For the Python library/CLI, add `pytest`-based tests where practical:
  - unit tests for the ERiC wrapper (type mapping, error handling),
  - integration tests around the CLI that use the existing `taxel/test_data` fixtures where possible.
- When you add supporting scripts, keep filenames meaningful (e.g., `fileio.py` covers disk I/O) and document how to trigger them in `AGENTS.md` or the same directory’s readme.
- Include any test resources (XML/CSV samples) alongside the executable script or module that consumes them.

## Commit & Pull Request Guidelines
- Use clear, present-tense messages in the form `type(scope): short description` (e.g., `docs: document demo execution`).
- Pull requests should describe what changed, reference related issues if any, and summarize how the demo or toolkit was exercised.
- Attach screenshots or logs only when the change affects the UI or introduces new runtime output that needs review.

## Security & Configuration Tips
- Never leave the placeholder manufacturer ID (`Hersteller-ID`) `74931` in XML that will actually be sent; replace it with your own before sending to ERiC or ELSTER (errors produce code `610301202`).
- Store PINs and certificates outside the repo; demos and the Python CLI should accept `_NULL` or equivalent options so you can run without credentials during development and reviews.
- Do not commit ERiC header files or additional binaries beyond what is already provided under `ERiC/`. Use the headers only locally as reference when defining `ctypes` structures and function signatures.
- Be explicit about how paths to certificates, keys, and PINs are supplied (CLI flags and/or environment variables) and avoid logging sensitive values.

## Project Plan
- **Discovery and Architecture**: Review ERiC docs (`eric-doc`, `ERiC/Dokumentation`), the vendored Rust `taxel` implementation and `eric-rs` bindings, and define the scope for eBilanz workflows (generate, validate, send) plus required ERiC interfaces; target Linux first.
- **Python ERiC Wrapper Library**: Design an FFI layer (prefer `ctypes` with handwritten structs/enums to avoid shipping headers) targeting the current ERiC release, cover certificate handling and error mapping, and ship a minimal API for eBilanz creation/validation with basic sample XMLs.
- **CLI Tooling**: Build a Python CLI mirroring `taxel` flows (e.g., `generate`, `validate`, `send`, `extract`/`print`), wire it to the wrapper, and document usage patterns with example commands.
- **Leverage Existing Assets**: Reuse `taxel/templates`, `taxel/mappings`, and `taxel/test_data` as much as possible for templates, mappings, and validation flows to accelerate parity with the Rust tool.
- **Web Application**: Expose core flows via a web backend and frontend (API + UI), reusing the Python library/CLI logic, and plan authentication plus storage strategy for certificates and documents.
- **Quality, Packaging, and Releases**: Add manual test recipes against ERiC demos, maintain a `pytest` test suite for the Python layers, and prepare packaging for a PyPI-ready library and CLI; see `agents_plan.md` for a detailed milestone breakdown (M0–M6).
