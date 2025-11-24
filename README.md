# pytaxel

## Vision, Architecture & Data Flow
- CSV export from bookkeeping → internal eBilanz domain model → populate XBRL/XML via templates/mappings (reusing `taxel/templates`, `taxel/mappings`, `taxel/test_data`) → validate → optional send/print.
- ERiC path: load `libericapi.so` and plugins from `ERiC/Linux-x86_64` (configurable later via env like `ERIC_HOME`/`PLUGIN_PATH`), call `EricBearbeiteVorgang` through `pytaxel.eric` to validate/send, with printable PDF via ERiC’s druck parameters.
- Python layout: `pytaxel/eric` (ctypes loader/types/errors/facade for ERiC), `pytaxel/ebilanz` (CSV→model→XBRL logic mirroring Rust taxel), `pytaxel/cli` (commands matching taxel CLI for generate/validate/send/preview).
- Workflow alignment: mirror Rust `taxel` commands and data expectations so fixtures/templates stay shared; keep raw ctypes isolated inside `pytaxel.eric` and surface high-level helpers to CLI/web layers.
- Security/paths: certificates and PINs supplied via CLI/env (no repo storage), manufacturer ID placeholder only for tests; logging directed to user-specified directory alongside ERiC log output.
