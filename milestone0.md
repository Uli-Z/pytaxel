# Milestone M0 Summary

## ERiC documentation
- **API reference**: Singlethread (`EricInitialisiere`/`EricBeende`) and multithread (`EricMtInstanzErzeugen`/`Freigeben`) flows; core entry `EricBearbeiteVorgang` with flags (`ERIC_VALIDIERE`, `ERIC_SENDE`, `ERIC_DRUCKE`, `ERIC_PRUEFE_HINWEISE`, `ERIC_VALIDIERE_OHNE_FREIGABEDATUM`); structs `eric_druck_parameter_t` (version 4, pdf path/callback, duplex, preview), `eric_verschluesselungs_parameter_t` (version 3, cert handle, PIN, optional abrufCode), `eric_zertifikat_parameter_t`; handle types for buffers/certificates/transfer; buffer lifecycle via `EricRueckgabepufferErzeugen/Inhalt/Laenge/Freigeben`; certificate calls `EricGetHandleToCertificate` + `EricCloseHandleToCertificate`; utilities `EricCheckXML`, `EricCreateTH`, `EricGetErrormessagesFromXMLAnswer`, `EricHoleFehlerText`; UTF-8 (no BOM) for payloads, `byteChar` for OS-encoded paths; progress/log/pdf callbacks available.
- **Entwicklerhandbuch**: Recommended Linux init is dynamic `dlopen` with `RTLD_GLOBAL`, then `EricInitialisiere(pluginPfad, logPfad)` before any call, `EricBeende`/`EricEntladePlugins` when done; plugin search is recursive under `pluginPfad`, logging to `eric.log`; path encoding per OS (Linux locale/FS encoding, Windows ANSI CP, macOS decomposed UTF-8); `EricSystemCheck` logs environment; runpath and LD_LIBRARY_PATH cautions for static linking scenarios; return codes resolved via `EricHoleFehlerText`.
- **Tutorial**: Walkthrough of ESt example; sets library search path, dynamically loads ERiC, calls `EricInitialisiere`, processes via `EricBearbeiteVorgang` with correct flags and buffers, optional PDF creation, transfer-handle handling for send; shows decrypt flow via `EricDekodiereDaten`; references ericdemo implementation.

## Existing implementations reviewed
- **taxel (Rust workspace)**: CLI commands `generate`, `extract`, `validate`, `send`; XML generation merges CSV into templates via `taxel-xml`; ERiC usage via `eric_sdk::Eric` (env vars `PLUGIN_PATH`, `CERTIFICATE_PATH`, `CERTIFICATE_PASSWORD`, optional print path, log dir param). Responses captured in ERiC buffers and logged; assets under `templates/`, `mappings/`, `test_data/`.
- **ericdemo-python**: `PyEric` ctypes wrapper loads ERiC from given home/log dirs; exposes `PyEricBearbeiteVorgang`, `PyEricDekodiereDaten`, buffer helpers, progress/log callbacks, certificate lifecycle (`PyEricGetHandleToCertificate`, `PyEricHoleZertifikatEigenschaften`). `EricProcess` builds flags (adds print when sending without transfer handle), manages return/server buffers; `EricDecode` wraps decryption; CLI args cover validate/send/decrypt with optional cert.
- **eric-rs**: Bindgen-based FFI (`eric-bindings`) and higher-level SDK: `Eric::new` uses `EricInitialisiere`, `validate`/`send` map to `EricBearbeiteVorgang` with `ProcessingFlag`; `PrintConfig` and `CertificateConfig` wrap ERiC structs and lifetimes; `ResponseBuffer` RAII for `EricRueckgabepuffer*`; error codes enumerated; tests use taxonomy fixtures.

## Ambiguities / hurdles to watch
- Align struct versions and ABI (druck_param v4, verschluesselungs_param v3) across wrappers to avoid drift with future ERiC drops.
- Clarify return-buffer interpretation: validation vs. server response; when to parse `EricGetErrormessagesFromXMLAnswer` for transfer results.
- Environment/layout conventions for `PLUGIN_PATH`, plugin discovery, and log directory permissions; avoid reliance on `LD_LIBRARY_PATH`.
- Certificate handling nuances: portal cert vs. other types, optional `Abrufcode`, PIN status; ensure proper handle lifetime across threads.
- Mapping `datenartVersion` strings to ERiC expectations and templates (eBilanz versions) plus replacing placeholder Hersteller-ID for real sends.
- Multithreading API needs future decision; current examples are singlethreaded.

Ready to proceed with Milestone M1 based on the reviewed materials.
