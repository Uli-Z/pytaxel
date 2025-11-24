"""Command-line interface for pytaxel."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pytaxel.ebilanz import generate_xml_from_csv
from pytaxel.eric.errors import EricError
from pytaxel.eric.facade import EricClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pytaxel", description="Python eBilanz tooling using ERiC")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate
    gen = subparsers.add_parser("generate", help="Generate eBilanz XML from CSV and template")
    gen.add_argument("--csv-file", required=True, help="Path to input CSV file")
    gen.add_argument("--template-file", required=True, help="Path to eBilanz XML template")
    gen.add_argument("--output-file", required=True, help="Where to write the generated XML")

    # validate
    val = subparsers.add_parser("validate", help="Validate eBilanz XML with ERiC")
    val.add_argument("--xml-file", required=True, help="Path to XML file to validate")
    val.add_argument("--tax-type", default="Bilanz", help="Tax type (default: Bilanz)")
    val.add_argument("--tax-version", default="6.5", help="Tax version (e.g., 6.5)")
    val.add_argument("--log-dir", help="Directory for ERiC logs")
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
    snd.add_argument("--log-dir", help="Directory for ERiC logs")
    snd.add_argument("--eric-home", help="Override ERiC home (default ERiC/Linux-x86_64)")

    return parser


def _taxonomy_version(tax_type: str, tax_version: str) -> str:
    return f"{tax_type}_{tax_version}"


def cmd_generate(args: argparse.Namespace) -> int:
    if args.debug:
        print(f"[debug] generating XML from {args.csv_file} using template {args.template_file} -> {args.output_file}")
    generate_xml_from_csv(args.csv_file, args.template_file, args.output_file)
    if args.debug:
        print(f"[debug] wrote {args.output_file}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    xml_path = Path(args.xml_file)
    xml_text = xml_path.read_text(encoding="utf-8")
    dav = _taxonomy_version(args.tax_type, args.tax_version)
    try:
        with EricClient(eric_home=args.eric_home, log_dir=args.log_dir) as client:
            result = client.validate_xml(xml_text, dav, pdf_path=args.pdf_name)
            if args.debug:
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
        with EricClient(eric_home=args.eric_home, log_dir=args.log_dir) as client:
            result = client.send_xml(
                xml_text,
                datenart_version=dav,
                certificate_path=args.certificate,
                pin=args.pin,
                pdf_path=args.pdf_name,
            )
            if args.debug:
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

    if args.command == "generate":
        return cmd_generate(args)
    if args.command == "validate":
        return cmd_validate(args)
    if args.command == "send":
        return cmd_send(args)

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
