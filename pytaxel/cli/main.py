"""Command-line interface for pytaxel."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pytaxel.ebilanz import extract_to_csv, generate_xml_from_csv
from eric_py.errors import EricError
from eric_py.loader import EricLibraryLoadError, eric_plugin_path, load_ericapi, load_erictoolkit

# EricClient imports ERiC and may fail at import time if ERIC_HOME is not set
# or the ERiC libraries are missing. Capture that and report a friendly error.
EricClient = None  # type: ignore[assignment]
ERIC_CLIENT_IMPORT_ERROR: Exception | None = None
try:
    from eric_py.facade import EricClient  # type: ignore[no-redef]
except Exception as exc:  # noqa: BLE001
    ERIC_CLIENT_IMPORT_ERROR = exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pytaxel", description="Python eBilanz tooling using ERiC")
    parser.add_argument("--verbose", "--debug", action="store_true", help="Enable debug output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # extract
    ext = subparsers.add_parser("extract", help="Extract values from XML into CSV")
    ext.add_argument("--xml-file", required=True, help="Path to XML file to extract")
    ext.add_argument(
        "--output-file",
        required=False,
        help="Path for output CSV; defaults to current directory",
    )

    # generate
    gen = subparsers.add_parser("generate", help="Generate eBilanz XML from CSV and template")
    gen.add_argument("--csv-file", required=False, help="Path to input CSV file")
    gen.add_argument("--template-file", required=True, help="Path to eBilanz XML template")
    gen.add_argument(
        "--output-file",
        required=False,
        help="Where to write the generated XML (defaults to current directory)",
    )

    # validate
    val = subparsers.add_parser("validate", help="Validate eBilanz XML with ERiC")
    val.add_argument("--xml-file", required=True, help="Path to XML file to validate")
    val.add_argument("--tax-type", default="Bilanz", help="Tax type (default: Bilanz)")
    val.add_argument("--tax-version", default="6.5", help="Tax version (e.g., 6.5)")
    val.add_argument("--log-dir", help="Directory for ERiC logs", default=None)
    val.add_argument("--eric-home", help="Override ERiC home (default ERiC/Linux-x86_64)")
    val.add_argument("--print", dest="pdf_name", help="Optional PDF output path for print/preview")

    # send
    snd = subparsers.add_parser("send", help="Send eBilanz XML via ERiC with certificate")
    snd.add_argument("--xml-file", required=True, help="Path to XML file to send")
    snd.add_argument("--tax-type", default="Bilanz", help="Tax type (default: Bilanz)")
    snd.add_argument("--tax-version", default="6.5", help="Tax version (e.g., 6.5)")
    snd.add_argument("--certificate", required=True, help="Path to PFX certificate")
    snd.add_argument("--pin", required=True, help="PIN/password for the certificate")
    snd.add_argument("--print", dest="pdf_name", help="Optional PDF output path for confirmation")
    snd.add_argument("--log-dir", help="Directory for ERiC logs", default=None)
    snd.add_argument("--eric-home", help="Override ERiC home (default ERIC_HOME)")

    # eric-check
    chk = subparsers.add_parser("eric-check", help="Check ERiC/ERIC_HOME configuration")
    chk.add_argument("--eric-home", help="Override ERiC home (default ERIC_HOME)")

    return parser


def _taxonomy_version(tax_type: str, tax_version: str) -> str:
    return f"{tax_type}_{tax_version}"


def _default_output_path(path: str | None, suffix: str) -> Path:
    if path:
        return Path(path)
    return Path.cwd() / f"output{suffix}"


def _log_response(log_path: Path, result) -> None:
    log_path.mkdir(parents=True, exist_ok=True)
    val_path = log_path / "validation_response.xml"
    srv_path = log_path / "server_response.xml"
    if result.validation_response:
        print(f"Logging validation result to '{val_path}'")
        val_path.write_text(result.validation_response, encoding="utf-8")
    else:
        val_path.write_text("", encoding="utf-8")
    if result.server_response:
        print(f"Logging server reponse to '{srv_path}'")
        srv_path.write_text(result.server_response, encoding="utf-8")
    else:
        srv_path.write_text("", encoding="utf-8")


def _handle_eric_client_import_error() -> int:
    """Print a clear setup error if EricClient could not be imported."""
    exc = ERIC_CLIENT_IMPORT_ERROR
    if isinstance(exc, EricLibraryLoadError):
        print(
            "ERiC could not be initialized.\n\n"
            f"{exc}\n\n"
            "To fix this:\n"
            "  1. Install the official ERiC distribution from the ELSTER\n"
            "     developer portal (Linux-x86_64).\n"
            "  2. Set the ERIC_HOME environment variable to the ERiC\n"
            "     installation directory, for example:\n"
            "         export ERIC_HOME=/opt/ERiC-41.6.2.0/Linux-x86_64\n"
            "  3. Re-run the pytaxel command.\n",
            file=sys.stderr,
        )
        return 2

    print(
        "Failed to import the ERiC client from eric-py. "
        "Check that eric-py is installed and ERIC_HOME is configured.\n"
        f"Underlying error: {exc}",
        file=sys.stderr,
    )
    return 2


def cmd_eric_check(args: argparse.Namespace) -> int:
    """Check ERiC/ERIC_HOME configuration and report status."""
    try:
        home = eric_plugin_path(args.eric_home)
    except EricLibraryLoadError as exc:
        print(
            "ERiC check failed.\n\n"
            f"{exc}\n\n"
            "To fix this:\n"
            "  1. Install the official ERiC distribution from the ELSTER\n"
            "     developer portal (Linux-x86_64).\n"
            "  2. Set the ERIC_HOME environment variable to the ERiC\n"
            "     installation directory, for example:\n"
            "         export ERIC_HOME=/opt/ERiC-41.6.2.0/Linux-x86_64\n"
            "  3. Re-run `pytaxel eric-check`.\n",
            file=sys.stderr,
        )
        return 2

    print(f"Resolved ERiC home: {home}")

    # Attempt to detect ERiC version from the path.
    try:
        from eric_py.versioning import SUPPORTED_ERIC_VERSIONS, detect_eric_version
    except Exception:  # noqa: BLE001
        detect_eric_version = None  # type: ignore[assignment]
        SUPPORTED_ERIC_VERSIONS = ()  # type: ignore[assignment]

    if detect_eric_version is not None:
        version = detect_eric_version(home)
        if version:
            print(f"Detected ERiC version: {version}")
            if SUPPORTED_ERIC_VERSIONS:
                if version in SUPPORTED_ERIC_VERSIONS:
                    print(f"eric-py supports this ERiC version: {version}")
                else:
                    print(
                        "Warning: detected ERiC version is not in the supported set "
                        f"{SUPPORTED_ERIC_VERSIONS} declared by eric-py."
                    )
        else:
            print("Detected ERiC version: unknown (could not infer from path)")

    # Try loading the shared libraries.
    try:
        load_ericapi(home)
        load_erictoolkit(home)
        print("Successfully loaded libericapi.so and liberictoolkit.so.")
        return 0
    except EricLibraryLoadError as exc:
        print(
            "ERiC libraries could not be loaded:\n"
            f"{exc}\n"
            "Check that the ERiC installation is complete and that all dependent\n"
            "libraries are available on your system (e.g. libericxerces, plugins).",
            file=sys.stderr,
        )
        return 2


def cmd_extract(args: argparse.Namespace) -> int:
    output = _default_output_path(args.output_file, ".csv")
    try:
        extract_to_csv(Path(args.xml_file), output)
        if args.verbose:
            print(f"[debug] wrote {output}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Extract failed: {exc}", file=sys.stderr)
        return 1


def cmd_generate(args: argparse.Namespace) -> int:
    output = _default_output_path(args.output_file, ".xml")
    if args.verbose:
        print(f"[debug] generating XML from {args.csv_file} using template {args.template_file} -> {output}")
    generate_xml_from_csv(args.csv_file, args.template_file, output)
    if args.verbose:
        print(f"[debug] wrote {output}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    xml_path = Path(args.xml_file)
    xml_text = xml_path.read_text(encoding="utf-8")
    dav = _taxonomy_version(args.tax_type, args.tax_version)
    try:
        log_dir = Path(args.log_dir) if args.log_dir else Path.cwd()
        if EricClient is None:
            return _handle_eric_client_import_error()
        with EricClient(eric_home=args.eric_home, log_dir=log_dir) as client:
            result = client.validate_xml(xml_text, dav, pdf_path=args.pdf_name)
        _log_response(log_dir, result)
        print(f"Response code: {result.code}")
        if args.verbose:
            print(f"[debug] ERiC return code: {result.code}")
            print(f"[debug] Validation response:\n{result.validation_response}")
            if result.server_response:
                print(f"[debug] Server response:\n{result.server_response}")
        return 0
    except EricError as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 2


def cmd_send(args: argparse.Namespace) -> int:
    xml_path = Path(args.xml_file)
    xml_text = xml_path.read_text(encoding="utf-8")
    dav = _taxonomy_version(args.tax_type, args.tax_version)
    try:
        log_dir = Path(args.log_dir) if args.log_dir else Path.cwd()
        if EricClient is None:
            return _handle_eric_client_import_error()
        with EricClient(eric_home=args.eric_home, log_dir=log_dir) as client:
            result = client.send_xml(
                xml_text,
                datenart_version=dav,
                certificate_path=args.certificate,
                pin=args.pin,
                pdf_path=args.pdf_name,
            )
        _log_response(log_dir, result)
        print(f"Response code: {result.code}")
        if args.verbose:
            print(f"[debug] ERiC return code: {result.code}")
            print(f"[debug] Validation response:\n{result.validation_response}")
            if result.server_response:
                print(f"[debug] Server response:\n{result.server_response}")
        return 0
    except EricError as exc:
        print(f"Send failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Send failed: {exc}", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "extract":
        return cmd_extract(args)
    if args.command == "generate":
        return cmd_generate(args)
    if args.command == "validate":
        return cmd_validate(args)
    if args.command == "send":
        return cmd_send(args)
    if args.command == "eric-check":
        return cmd_eric_check(args)

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
