"""FastAPI application exposing pytaxel workflows."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from pytaxel.ebilanz import generate_xml_from_csv
from pytaxel.eric.errors import EricError
from pytaxel.eric.facade import EricClient

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


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """
    <h1>pytaxel API</h1>
    <h2>Generate</h2>
    <form action="/generate" method="post" enctype="multipart/form-data">
      CSV: <input type="file" name="csv_file"/><br/>
      Template (optional): <input type="text" name="template_path" value=""/> (defaults bundled)<br/>
      <button type="submit">Generate</button>
    </form>
    <h2>Validate</h2>
    <form action="/validate" method="post" enctype="multipart/form-data">
      XML: <input type="file" name="xml_file"/><br/>
      Tax type: <input type="text" name="tax_type" value="Bilanz"/><br/>
      Tax version: <input type="text" name="tax_version" value="6.5"/><br/>
      <button type="submit">Validate</button>
    </form>
    <h2>Send</h2>
    <form action="/send" method="post" enctype="multipart/form-data">
      XML: <input type="file" name="xml_file"/><br/>
      Certificate: <input type="file" name="certificate"/><br/>
      PIN: <input type="password" name="pin"/><br/>
      <button type="submit">Send</button>
    </form>
    """


@app.post("/generate")
def generate_endpoint(
    csv_file: UploadFile = File(...),
    template_path: Optional[str] = Form(None),
):
    tmp_csv = None
    tmp_xml = None
    try:
        tmp_csv = _temp_file_from_upload(csv_file, suffix=".csv")
        template = Path(template_path) if template_path else DEFAULT_TEMPLATE
        if not template.exists():
            raise HTTPException(status_code=400, detail="Template file not found")
        tmp_xml = Path(tempfile.mkstemp(suffix=".xml")[1])
        generate_xml_from_csv(tmp_csv, template, tmp_xml)
        xml_bytes = tmp_xml.read_bytes()
        headers = {"Content-Disposition": 'attachment; filename="ebilanz.xml"'}
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
):
    tmp_xml = None
    tmp_log_dir = None
    try:
        tmp_xml = _temp_file_from_upload(xml_file, suffix=".xml")
        tmp_log_dir = Path(tempfile.mkdtemp(prefix="eric-log-"))
        xml_text = tmp_xml.read_text(encoding="utf-8")
        dav = f"{tax_type}_{tax_version}"
        with EricClient(eric_home=eric_home, log_dir=tmp_log_dir) as client:
            result = client.validate_xml(xml_text, dav)
        return JSONResponse(
            {
                "code": result.code,
                "validation_response": result.validation_response,
                "server_response": result.server_response,
            }
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
        if tmp_log_dir and tmp_log_dir.exists():
            shutil.rmtree(tmp_log_dir, ignore_errors=True)


@app.post("/send")
def send_endpoint(
    xml_file: UploadFile = File(...),
    certificate: UploadFile = File(...),
    pin: str = Form(...),
    tax_type: str = Form("Bilanz"),
    tax_version: str = Form("6.5"),
    eric_home: Optional[str] = Form(None),
    pdf_name: Optional[str] = Form(None),
):
    tmp_xml = None
    tmp_cert = None
    tmp_log_dir = None
    tmp_pdf = None
    try:
        tmp_xml = _temp_file_from_upload(xml_file, suffix=".xml")
        tmp_cert = _temp_file_from_upload(certificate, suffix=".pfx")
        tmp_log_dir = Path(tempfile.mkdtemp(prefix="eric-log-"))
        xml_text = tmp_xml.read_text(encoding="utf-8")
        dav = f"{tax_type}_{tax_version}"
        pdf_path = None
        if pdf_name:
            tmp_pdf = Path(tempfile.mkstemp(suffix=".pdf")[1])
            pdf_path = tmp_pdf
        with EricClient(eric_home=eric_home, log_dir=tmp_log_dir) as client:
            result = client.send_xml(
                xml_text,
                datenart_version=dav,
                certificate_path=tmp_cert,
                pin=pin,
                pdf_path=pdf_path,
            )
        response_payload = {
            "code": result.code,
            "validation_response": result.validation_response,
            "server_response": result.server_response,
            "transfer_handle": result.transfer_handle,
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
    except EricError as exc:
        return JSONResponse({"code": exc.code, "error": str(exc)}, status_code=400)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        for path in (tmp_xml, tmp_cert, tmp_pdf):
            if path and Path(path).exists():
                Path(path).unlink()
        if tmp_log_dir and tmp_log_dir.exists():
            shutil.rmtree(tmp_log_dir, ignore_errors=True)


if __name__ == "__main__":  # pragma: no cover
    try:
        import uvicorn
    except ImportError:
        raise SystemExit("uvicorn is required to run the dev server")
    uvicorn.run("pytaxel.web.app:app", host="0.0.0.0", port=8000, reload=False)
