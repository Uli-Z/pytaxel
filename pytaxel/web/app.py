"""FastAPI application exposing pytaxel workflows."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from pytaxel.ebilanz import extract_to_csv, generate_xml_from_csv
from eric_py.errors import EricError
from eric_py.loader import EricLibraryLoadError

DEFAULT_TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "taxel"
    / "templates"
    / "elster_v11"
    / "taxonomy_v6.5"
    / "ebilanz.xml"
)

app = FastAPI(title="pytaxel API", version="0.1.0")


def _temp_file_from_upload(upload: UploadFile, suffix: str) -> Path:
    """Persist an UploadFile to a temp file and return the path."""
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    path = Path(tmp_path)
    with path.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    return path


def _env_or(value: Optional[str], env_key: str) -> Optional[str]:
    return value or os.environ.get(env_key)


def _log_response(log_dir: Path, validation_response: str, server_response: str) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    val_path = log_dir / "validation_response.xml"
    srv_path = log_dir / "server_response.xml"
    val_path.write_text(validation_response, encoding="utf-8")
    srv_path.write_text(server_response, encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """
    <h1>pytaxel API</h1>
    <h2>Extract</h2>
    <form action="/extract" method="post" enctype="multipart/form-data">
      XML: <input type="file" name="xml_file"/><br/>
      Output CSV (optional): <input type="text" name="output_path" value=""/><br/>
      <button type="submit">Extract</button>
    </form>
    <h2>Generate</h2>
    <form action="/generate" method="post" enctype="multipart/form-data">
      CSV: <input type="file" name="csv_file"/><br/>
      Template (optional): <input type="text" name="template_path" value=""/> (defaults bundled)<br/>
      Output XML (optional): <input type="text" name="output_path" value=""/><br/>
      <button type="submit">Generate</button>
    </form>
    <h2>Validate</h2>
    <form action="/validate" method="post" enctype="multipart/form-data">
      XML: <input type="file" name="xml_file"/><br/>
      Tax type: <input type="text" name="tax_type" value="Bilanz"/><br/>
      Tax version: <input type="text" name="tax_version" value="6.5"/><br/>
      Log dir (optional): <input type="text" name="log_dir" value=""/><br/>
      Print PDF path (optional): <input type="text" name="pdf_name" value=""/><br/>
      <button type="submit">Validate</button>
    </form>
    <h2>Send</h2>
    <form action="/send" method="post" enctype="multipart/form-data">
      XML: <input type="file" name="xml_file"/><br/>
      Certificate: <input type="file" name="certificate"/><br/>
      PIN: <input type="password" name="pin"/><br/>
      Log dir (optional): <input type="text" name="log_dir" value=""/><br/>
      Print PDF path (optional): <input type="text" name="pdf_name" value=""/><br/>
      <button type="submit">Send</button>
    </form>
    """


@app.post("/extract")
def extract_endpoint(
    xml_file: UploadFile = File(...),
    output_path: Optional[str] = Form(None),
):
    tmp_xml = None
    tmp_csv = None
    try:
        tmp_xml = _temp_file_from_upload(xml_file, suffix=".xml")
        out = Path(output_path) if output_path else Path.cwd() / "output.csv"
        extract_to_csv(tmp_xml, out)
        csv_bytes = out.read_bytes()
        headers = {"Content-Disposition": f'attachment; filename="{out.name}"'}
        return StreamingResponse(iter([csv_bytes]), media_type="text/csv", headers=headers)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        for path in (tmp_xml, tmp_csv):
            if path and path.exists():
                path.unlink()


@app.post("/generate")
def generate_endpoint(
    csv_file: UploadFile | None = File(None),
    template_path: Optional[str] = Form(None),
    output_path: Optional[str] = Form(None),
):
    tmp_csv = None
    tmp_xml = None
    try:
        if csv_file is not None:
            tmp_csv = _temp_file_from_upload(csv_file, suffix=".csv")
        template = Path(template_path) if template_path else DEFAULT_TEMPLATE
        if not template.exists():
            raise HTTPException(status_code=400, detail="Template file not found")
        tmp_xml = Path(output_path) if output_path else Path.cwd() / "output.xml"
        generate_xml_from_csv(tmp_csv, template, tmp_xml)
        xml_bytes = tmp_xml.read_bytes()
        headers = {"Content-Disposition": f'attachment; filename="{tmp_xml.name}"'}
        return StreamingResponse(
            iter([xml_bytes]), media_type="application/xml", headers=headers
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if tmp_csv and tmp_csv.exists():
            tmp_csv.unlink()
        if tmp_xml and tmp_xml.exists():
            tmp_xml.unlink()


@app.post("/validate")
def validate_endpoint(
    xml_file: UploadFile = File(...),
    tax_type: str = Form("Bilanz"),
    tax_version: str = Form("6.5"),
    eric_home: Optional[str] = Form(None),
    log_dir: Optional[str] = Form(None),
    pdf_name: Optional[str] = Form(None),
):
    tmp_xml = None
    tmp_log_dir = None
    pdf_path = None
    try:
        tmp_xml = _temp_file_from_upload(xml_file, suffix=".xml")
        tmp_log_dir = Path(log_dir) if log_dir else Path(tempfile.mkdtemp(prefix="eric-log-"))
        if pdf_name:
            pdf_path = Path(pdf_name)
        xml_text = tmp_xml.read_text(encoding="utf-8")
        dav = f"{tax_type}_{tax_version}"
        
        # Configure ERIC_HOME for this request if provided
        if eric_home:
            os.environ["ERIC_HOME"] = eric_home
            
        from eric_py.facade import EricClient

        with EricClient(eric_home=_env_or(eric_home, "ERIC_HOME"), log_dir=tmp_log_dir) as client:
            result = client.validate_xml(xml_text, dav, pdf_path=pdf_path)
        _log_response(tmp_log_dir, result.validation_response, result.server_response)
        payload = {
            "code": result.code,
            "validation_response": result.validation_response,
            "server_response": result.server_response,
            "log_dir": str(tmp_log_dir),
        }
        if pdf_path and pdf_path.exists():
            pdf_bytes = pdf_path.read_bytes()
            headers = {"Content-Disposition": f'attachment; filename="{pdf_path.name}"'}
            return StreamingResponse(iter([pdf_bytes]), media_type="application/pdf", headers=headers)
        return JSONResponse(payload)
    except (ImportError, EricLibraryLoadError) as exc:
        return JSONResponse(
            {
                "code": 500,
                "error": f"ERiC could not be initialized: {exc}. Check ERIC_HOME configuration.",
            },
            status_code=500,
        )
    except EricError as exc:
        return JSONResponse(
            {"code": exc.code, "error": str(exc)}, status_code=400
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if tmp_xml and tmp_xml.exists():
            tmp_xml.unlink()
        if tmp_log_dir and tmp_log_dir.exists() and not log_dir:
            shutil.rmtree(tmp_log_dir, ignore_errors=True)


@app.post("/send")
def send_endpoint(
    xml_file: UploadFile = File(...),
    certificate: UploadFile | None = File(None),
    pin: Optional[str] = Form(None),
    tax_type: str = Form("Bilanz"),
    tax_version: str = Form("6.5"),
    eric_home: Optional[str] = Form(None),
    pdf_name: Optional[str] = Form(None),
    log_dir: Optional[str] = Form(None),
):
    tmp_xml = None
    tmp_cert = None
    tmp_log_dir = None
    tmp_pdf = None
    try:
        tmp_xml = _temp_file_from_upload(xml_file, suffix=".xml")
        cert_path = None
        if certificate is not None:
            tmp_cert = _temp_file_from_upload(certificate, suffix=".pfx")
            cert_path = tmp_cert
        else:
            env_cert = os.environ.get("CERTIFICATE_PATH")
            if env_cert:
                cert_path = Path(env_cert)
        pin_value = _env_or(pin, "CERTIFICATE_PASSWORD")
        if cert_path is None or pin_value is None:
            raise HTTPException(status_code=400, detail="Certificate and PIN are required")

        tmp_log_dir = Path(log_dir) if log_dir else Path(tempfile.mkdtemp(prefix="eric-log-"))
        xml_text = tmp_xml.read_text(encoding="utf-8")
        dav = f"{tax_type}_{tax_version}"
        pdf_path = None
        if pdf_name:
            tmp_pdf = Path(tempfile.mkstemp(suffix=".pdf")[1])
            pdf_path = tmp_pdf

        # Configure ERIC_HOME for this request if provided
        if eric_home:
            os.environ["ERIC_HOME"] = eric_home

        from eric_py.facade import EricClient

        with EricClient(eric_home=_env_or(eric_home, "ERIC_HOME"), log_dir=tmp_log_dir) as client:
            result = client.send_xml(
                xml_text,
                datenart_version=dav,
                certificate_path=cert_path,
                pin=pin_value,
                pdf_path=pdf_path,
            )
        _log_response(tmp_log_dir, result.validation_response, result.server_response)
        response_payload = {
            "code": result.code,
            "validation_response": result.validation_response,
            "server_response": result.server_response,
            "transfer_handle": result.transfer_handle,
            "log_dir": str(tmp_log_dir),
        }
        if pdf_path and pdf_path.exists():
            pdf_bytes = pdf_path.read_bytes()
            headers = {"Content-Disposition": 'attachment; filename="confirmation.pdf"'}
            return StreamingResponse(
                iter([pdf_bytes]),
                media_type="application/pdf",
                headers=headers,
            )
        return JSONResponse(response_payload)
    except (ImportError, EricLibraryLoadError) as exc:
        return JSONResponse(
            {
                "code": 500,
                "error": f"ERiC could not be initialized: {exc}. Check ERIC_HOME configuration.",
            },
            status_code=500,
        )
    except EricError as exc:
        return JSONResponse({"code": exc.code, "error": str(exc)}, status_code=400)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        for path in (tmp_xml, tmp_cert, tmp_pdf):
            if path and Path(path).exists():
                Path(path).unlink()
        if tmp_log_dir and tmp_log_dir.exists() and not log_dir:
            shutil.rmtree(tmp_log_dir, ignore_errors=True)


if __name__ == "__main__":  # pragma: no cover
    try:
        import uvicorn
    except ImportError:
        raise SystemExit("uvicorn is required to run the dev server")
    uvicorn.run("pytaxel.web.app:app", host="0.0.0.0", port=8000, reload=False)
