# Prompts for Pytaxel AI Agents

This document contains the high-level instructions (prompts) for AI agents to implement the `pytaxel` project. Each prompt corresponds to a milestone from `agents_plan.md` and should be considered a standalone work instruction.

---

## Prompt for Milestone M0: Orientation & Architecture

**Instruction to the Agent:**

Your task is to complete Milestone M0.

1.  **Read and analyze the following documents** from the `eric-doc/` directory to understand the functionality of the ERiC API:
    *   `ERiC-API-Referenz.md` (focus on function signatures, structs, error codes)
    *   `ERiC-Entwicklerhandbuch.md` (focus on integration patterns, configuration)
    *   `ERiC-Tutorial.md` (focus on concrete application examples)

2.  **Inspect the code and structure** of the following projects to understand existing implementations:
    *   The Rust project `taxel` (under `taxel/`): Understand the CLI commands, XML generation, and existing Python integration.
    *   The ERiC Python example under `ERiC/Linux-x86_64/Beispiel/ericdemo-python/`.
    *   The `eric-rs` project as a reference for an FFI implementation.

**Your deliverable for this milestone is no code.** Instead, at the end of your analysis, confirm that you have read and understood all specified materials. List any potential ambiguities or technical hurdles you have identified. Provide a final confirmation that you are ready to proceed with Milestone M1.

---

## Prompt for Milestone M1: Foundations & Data Flow

**Instruction to the Agent:**

Your task is to implement Milestone M1.

1.  **Create the Python package directory structure** as defined in `agents_plan.md` under M1. This includes the directories `pytaxel/eric/`, `pytaxel/ebilanz/`, and `pytaxel/cli/`.
2.  **Create the initial Python files** (`__init__.py`, `loader.py`, `types.py`, etc.) within these respective directories.
3.  **Populate each newly created file with a basic docstring** describing its purpose, and add `# TODO: Implement in M2/M3` as a placeholder in the body.
4.  **Update the `README.md` file** of the project. Add a section titled "Vision, Architecture & Data Flow" summarizing the workflow described in M1 (CSV → eBilanz), the ERiC path, and the reuse of `taxel` resources.

**Committing Your Work:**
Once you have successfully completed this milestone, create one or more Git commits.
- Use the Conventional Commits format (e.g., `feat(eric): ...`, `docs(readme): ...`).
- If the milestone involved multiple distinct changes, consider creating separate, logical commits.
- Your commit message(s) should clearly describe the work you have done for this milestone.

---

## Prompt for Milestone M2 & M2a: Python ERiC Wrapper & Walking Skeleton

**Instruction to the Agent:**

Your task is to implement Milestones M2 and M2a to create a functional interface to the ERiC library.

1.  **Implement the ERiC wrapper** in the `pytaxel/eric/` module.
    *   **`loader.py`**: Implement a function that loads the `libericapi.so` and `liberictoolkit.so` using `ctypes.CDLL`. The path should be configurable via the `ERIC_HOME` environment variable.
    *   **`types.py`**: Define the necessary `ctypes.Structure` types and `enum.IntEnum` error codes for ERiC version 41.6.2.0, based on the documentation. Pay special attention to correct `version` fields in the structs.
    *   **`errors.py`**: Create an `EricError` exception and a `check_eric_result` function that checks an ERiC return code and raises the exception on failure.
    *   **`api.py`**: Bind the C functions from the ERiC API (e.g., for validation, sending, printing) with correct `argtypes` and `restype`.
    *   **`facade.py`**: Create a clean, high-level Python facade with functions like `validate_xml(...)` and `send_xml(...)` that encapsulate the details of the FFI calls.

2.  **Implement the "Walking Skeleton" (M2a)**:
    *   Create an executable script (e.g., `examples/m2a_walking_skeleton.py`).
    *   This script must perform a complete, end-to-end validation of a hard-coded test XML file (e.g., from `taxel/test_data/`) using your new wrapper and print the result. This serves as proof that the integration works.

**Committing Your Work:**
Once you have successfully completed this milestone, create one or more Git commits.
- Use the Conventional Commits format (e.g., `feat(eric): ...`, `docs(readme): ...`).
- If the milestone involved multiple distinct changes (e.g., the wrapper and the skeleton script), consider creating separate, logical commits.
- Your commit message(s) should clearly describe the work you have done for this milestone.

---

## Prompt for Milestone M3: eBilanz Data Model & Template Port

**Instruction to the Agent:**

Your task is to implement Milestone M3 and port the core XML generation logic from the Rust `taxel` project to Python.

1.  **Analyze the logic in `taxel-xml`** to understand how CSV data, mappings, and templates interact.
2.  **Implement the Python data model** in `pytaxel/ebilanz/`:
    *   Define Python `dataclasses` for master data and balance sheet positions.
    *   Implement a robust CSV parser that reads a CSV file and populates an instance of your data model.
    *   Implement an XML renderer that takes the data model and, using the templates from `taxel/templates` and mappings from `taxel/mappings`, generates a valid eBilanz XBRL file. Use `xml.etree.ElementTree`.
3.  **Write a test**: Create a Pytest test that processes a sample CSV from `taxel/test_data` and compares the generated XML file with a reference XML file previously generated by the Rust `taxel` tool.

**Committing Your Work:**
Once you have successfully completed this milestone, create one or more Git commits.
- Use the Conventional Commits format (e.g., `feat(ebilanz): ...`, `test(ebilanz): ...`).
- If the milestone involved multiple distinct changes, consider creating separate, logical commits.
- Your commit message(s) should clearly describe the work you have done for this milestone.

---

## Prompt for Milestone M4: CLI (Python)

**Instruction to the Agent:**

Your task is to build the CLI for the project as described in Milestone M4.

1.  **Use the `argparse` module** from the Python standard library.
2.  **Implement the CLI framework** in the `pytaxel/cli/` module.
3.  **Create the sub-commands `generate`, `validate`, and `send`**. The command-line arguments (`--csv-file`, `--certificate`, etc.) should closely mirror those of the Rust `taxel` CLI.
4.  **Connect the CLI commands** to the facade functions you created in M2 (`validate_xml`, `send_xml`) and M3 (`generate_xml_from_csv`).
5.  **Ensure the CLI returns correct exit codes** (0 for success, >0 for error) and that additional log outputs can be enabled with `--debug`.
6.  **Add a section with usage examples** for the new Python CLI to the `README.md`.

**Committing Your Work:**
Once you have successfully completed this milestone, create one or more Git commits.
- Use the Conventional Commits format (e.g., `feat(cli): ...`, `docs(readme): ...`).
- If the milestone involved multiple distinct changes, consider creating separate, logical commits.
- Your commit message(s) should clearly describe the work you have done for this milestone.

---

## Prompt for Milestone M4a: CLI Parity with Rust taxel

**Instruction to the Agent:**

Your task is to align the Python CLI with the Rust `taxel` CLI to at least 99% functional parity.

1. Add the `extract` command (XML → CSV) with the same arguments and defaults as the Rust CLI.
2. Ensure `generate` honors the Rust defaults (optional CSV, default output directory when none is provided).
3. Mirror flags and args: `--verbose/--debug`, `--tax-type`, `--tax-version`, `--print`, log directory handling, allowed values/defaults.
4. Replicate outputs and exit codes:
   - write validation and server responses to files with the same filenames in the chosen log directory,
   - print ERiC return codes in the same places/format as Rust taxel,
   - align process exit codes for success and failure.
5. Keep improvements allowed (e.g., env var support), but do not break Rust-compatible invocations.
6. Add or adjust CLI integration tests that compare behavior/output (CSV/XML/log files) against the Rust CLI fixtures.
7. Update README/help snippets if flags/defaults or new commands are added.

**Committing Your Work:**
Once you have successfully completed this milestone, create one or more Git commits.
- Use the Conventional Commits format (e.g., `feat(cli): ...`, `test(cli): ...`, `docs(readme): ...`).
- If the milestone involved multiple distinct changes, consider creating separate, logical commits.
- Your commit message(s) should clearly describe the work you have done for this milestone.

---

## Prompt for Milestone M5: Web App

**Instruction to the Agent:**

Your task is to sketch out and implement the web application backend based on Milestone M5.

1.  **Use the `FastAPI` framework.**
2.  **Create the basic structure** of the web application in the `pytaxel/web/` directory.
3.  **Implement the following API endpoints:**
    *   `POST /generate`: Accepts a CSV file upload and parameters, calls the `generate` logic, and returns the XML file for download.
    *   `POST /validate`: Accepts an XML file upload, calls the `validate_xml` facade, and returns the result (success/error list) as JSON.
    *   `POST /send`: Combines the above steps and calls the `send_xml` facade.
4.  **Pay attention to security and statelessness:** Sensitive data like PINs must only be held in memory for the duration of the request. Each request must run in a clean, isolated ERiC context. Temporary files must be reliably deleted.
5.  **Deliverable:** A running `uvicorn` development server. A complex UI is not necessary; simple HTML forms for testing the endpoints are sufficient.

**Committing Your Work:**
Once you have successfully completed this milestone, create one or more Git commits.
- Use the Conventional Commits format (e.g., `feat(web): ...`).
- If the milestone involved multiple distinct changes, consider creating separate, logical commits.
- Your commit message(s) should clearly describe the work you have done for this milestone.

---

## Prompt for Milestone M6: Quality, Tests & Release

**Instruction to the Agent:**

Your task is to bring the project to release readiness according to Milestone M6.

1.  **Extend test coverage**: Implement the testing strategy described in `agents_plan.md`. Focus on:
    *   **FFI Tests (pytest)**: Test the `ctypes` wrappers in `pytaxel/eric` for correctness, especially error handling and error code mapping.
    *   **CLI Integration Tests (pytest)**: Write tests that call the CLI as a subprocess and check its behavior (exit codes, STDOUT/STDERR) for typical use cases from `taxel/test_data`.
2.  **Ensure code quality**: Install `ruff` (`pip install ruff`) and run `ruff check . --fix` to automatically format the code and fix linting errors.
3.  **Prepare packaging**: Finalize the `pyproject.toml` so that the package can be correctly installed with `pip install .` and the `pytaxel` CLI command is available.
4.  **Review documentation**: Read the `README.md` and all docstrings, and ensure they are accurate, current, and helpful for a new user.

**Committing Your Work:**
Once you have successfully completed this milestone, create one or more Git commits.
- Use the Conventional Commits format (e.g., `test: ...`, `style: ...`, `chore(release): ...`).
- If the milestone involved multiple distinct changes, consider creating separate, logical commits for tests, linting, and packaging setup.
- Your commit message(s) should clearly describe the work you have done for this milestone.

---

## Prompt for Milestone M7: Web UI Parity with Updated CLI

**Instruction to the Agent:**

Your task is to adapt the web API/UI so it matches the parity-updated CLI (including M4a changes) with at least 99% functional equivalence to Rust `taxel`.

1. Align endpoints/behavior with CLI: expose `extract`, `generate`, `validate`, `send` using the same defaults and allowed values (tax type/version, print options, log-dir handling).
2. Implement print/preview handling analogous to CLI (`validate` preview, `send` confirmation) and persist validation/server responses to the same filenames/locations per request.
3. Honor CLI env/config conventions (e.g., `ERIC_HOME`, certificate/PIN env vars) without leaking secrets; ensure per-request ERiC state isolation and temp/log cleanup.
4. Update UI labels/help to reflect the new commands/flags/defaults.
5. Add/adjust e2e/API tests that compare web responses and log artifacts to the CLI outputs for shared fixtures, covering extract/generate/validate/send with print/preview variants.

**Committing Your Work:**
Once you have successfully completed this milestone, create one or more Git commits.
- Use the Conventional Commits format (e.g., `feat(web): ...`, `test(web): ...`, `docs(web): ...`).
- If the milestone involved multiple distinct changes, consider creating separate, logical commits.
- Your commit message(s) should clearly describe the work you have done for this milestone.

---
