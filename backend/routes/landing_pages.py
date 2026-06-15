"""HawkPhish - Landing Page Routes (Multi-file support)"""
import os
import re
import shutil
import zipfile
import io
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import LandingPage
from pydantic import BaseModel
from typing import Optional, List
from services.landing_templates import get_all_templates, get_template

router = APIRouter(prefix="/api/landing-pages", tags=["Landing Pages"])

# Base directory for landing page files
LP_BASE_DIR = Path(os.path.dirname(__file__)).parent / "landing_pages"
LP_BASE_DIR.mkdir(exist_ok=True)


class LandingPageCreate(BaseModel):
    name: str
    url: Optional[str] = ""
    html_content: Optional[str] = ""
    root_file: Optional[str] = "index.html"
    capture_credentials: bool = True
    capture_fields: list = ["email", "password"]
    redirect_url: Optional[str] = ""


def _lp_dir(page_id: int) -> Path:
    return LP_BASE_DIR / str(page_id)


def _inject_tracking(html: str, page_id: int, tracking_id: str) -> str:
    """Inject tracking_id into all forms and rewrite relative links."""
    # Add hidden tracking_id to all forms
    def _form_replacer(match):
        form_tag = match.group(0)
        # Don't double-inject
        if 'name="tracking_id"' in form_tag:
            return form_tag
        # Rewrite action to our submit endpoint
        action_match = re.search(r'action=["\']([^"\']*)["\']', form_tag, re.IGNORECASE)
        action = action_match.group(1) if action_match else ""
        # If action is relative or empty, set to our submit endpoint
        if not action or action.startswith(".") or action.startswith("/lp/") or not action.startswith("http"):
            form_tag = re.sub(
                r'action=["\'][^"\']*["\']',
                f'action="/lp/{page_id}/submit"',
                form_tag,
                flags=re.IGNORECASE,
                count=1
            )
        return form_tag + f'<input type="hidden" name="tracking_id" value="{tracking_id}">'

    html = re.sub(r'<form\b[^>]*>', _form_replacer, html, flags=re.IGNORECASE)

    # Inject tracking_id into all relative links to preserve it across pages
    def _link_replacer(match):
        href = match.group(1)
        if href.startswith("http") or href.startswith("#") or href.startswith("javascript:"):
            return match.group(0)
        # Append tracking_id to relative links
        separator = "&" if "?" in href else "?"
        return f'href="{href}{separator}tracking_id={tracking_id}"'

    html = re.sub(r'href=["\']([^"\']*)["\']', _link_replacer, html)

    # Also inject a script to set tracking_id globally for JS-based forms
    script = f"""<script>
    window.__hawkphish_tracking_id = '{tracking_id}';
    window.__hawkphish_page_id = {page_id};
    // Intercept fetch/XHR to include tracking_id
    (function() {{
        var origFetch = window.fetch;
        window.fetch = function(url, opts) {{
            if (typeof url === 'string' && !url.includes('tracking_id')) {{
                var sep = url.includes('?') ? '&' : '?';
                url = url + sep + 'tracking_id=' + window.__hawkphish_tracking_id;
            }}
            return origFetch.apply(this, arguments);
        }};
    }})();
</script>"""
    # Insert before closing </head> or before </body>
    if "</head>" in html:
        html = html.replace("</head>", script + "</head>", 1)
    elif "</body>" in html:
        html = html.replace("</body>", script + "</body>", 1)
    else:
        html = html + script

    return html


@router.get("")
async def list_landing_pages(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LandingPage).order_by(LandingPage.created_at.desc()))
    pages = result.scalars().all()
    return [{
        "id": p.id, "name": p.name, "url": p.url,
        "root_file": p.root_file,
        "files": p.files or [],
        "capture_credentials": p.capture_credentials,
        "capture_fields": p.capture_fields or [],
        "redirect_url": p.redirect_url,
        "created_at": p.created_at.isoformat(),
    } for p in pages]


@router.post("")
async def create_landing_page(data: LandingPageCreate, db: AsyncSession = Depends(get_db)):
    page = LandingPage(**data.model_dump())
    db.add(page)
    await db.commit()
    await db.refresh(page)

    # If html_content provided, save it to disk
    if page.html_content:
        lp_dir = _lp_dir(page.id)
        lp_dir.mkdir(exist_ok=True)
        (lp_dir / page.root_file).write_text(page.html_content, encoding="utf-8")
        page.files = [page.root_file]
        await db.commit()

    return {"id": page.id, "message": "Landing page created"}


@router.get("/{page_id}")
async def get_landing_page(page_id: int, db: AsyncSession = Depends(get_db)):
    page = await db.get(LandingPage, page_id)
    if not page:
        raise HTTPException(404, "Landing page not found")
    return {
        "id": page.id, "name": page.name, "url": page.url,
        "html_content": page.html_content,
        "root_file": page.root_file,
        "files": page.files or [],
        "capture_credentials": page.capture_credentials,
        "capture_fields": page.capture_fields or [],
        "redirect_url": page.redirect_url,
        "created_at": page.created_at.isoformat(),
    }


@router.put("/{page_id}")
async def update_landing_page(page_id: int, data: LandingPageCreate, db: AsyncSession = Depends(get_db)):
    page = await db.get(LandingPage, page_id)
    if not page:
        raise HTTPException(404, "Landing page not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(page, k, v)
    await db.commit()
    return {"message": "Landing page updated"}


@router.delete("/{page_id}")
async def delete_landing_page(page_id: int, db: AsyncSession = Depends(get_db)):
    page = await db.get(LandingPage, page_id)
    if not page:
        raise HTTPException(404, "Landing page not found")
    # Delete files from disk
    lp_dir = _lp_dir(page_id)
    if lp_dir.exists():
        shutil.rmtree(lp_dir)
    await db.delete(page)
    await db.commit()
    return {"message": "Landing page deleted"}


@router.post("/{page_id}/upload-zip")
async def upload_landing_page_zip(
    page_id: int,
    file: UploadFile = File(...),
    root_file: Optional[str] = Query("index.html"),
    db: AsyncSession = Depends(get_db),
):
    """Upload a ZIP file containing a complete landing page (HTML, CSS, JS, images)."""
    page = await db.get(LandingPage, page_id)
    if not page:
        raise HTTPException(404, "Landing page not found")

    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(400, "Only ZIP files are allowed")

    # Clean old files
    lp_dir = _lp_dir(page_id)
    if lp_dir.exists():
        shutil.rmtree(lp_dir)
    lp_dir.mkdir(parents=True, exist_ok=True)

    # Extract ZIP
    content = await file.read()
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            # Security: prevent path traversal
            for member in z.namelist():
                if member.startswith("/") or ".." in member:
                    continue
                z.extract(member, lp_dir)
    except zipfile.BadZipFile:
        raise HTTPException(400, "Invalid ZIP file")

    # Detect files
    files = []
    for f in lp_dir.rglob("*"):
        if f.is_file():
            rel = f.relative_to(lp_dir).as_posix()
            files.append(rel)

    # Auto-detect root file if not found
    if root_file not in files:
        html_files = [f for f in files if f.lower().endswith(".html") or f.lower().endswith(".htm")]
        root_file = html_files[0] if html_files else (files[0] if files else "index.html")

    page.root_file = root_file
    page.files = files
    await db.commit()

    return {
        "message": f"Uploaded {len(files)} files",
        "root_file": root_file,
        "files": files,
    }


@router.post("/{page_id}/upload-file")
async def upload_single_file(
    page_id: int,
    filename: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a single file (CSS, JS, image, etc.) to a landing page."""
    page = await db.get(LandingPage, page_id)
    if not page:
        raise HTTPException(404, "Landing page not found")

    lp_dir = _lp_dir(page_id)
    lp_dir.mkdir(parents=True, exist_ok=True)

    # Security: prevent path traversal
    safe_name = filename.replace("..", "_").replace("/", "_").replace("\\", "_")
    dest = lp_dir / safe_name
    content = await file.read()
    dest.write_bytes(content)

    files = page.files or []
    if safe_name not in files:
        files.append(safe_name)
    page.files = files
    await db.commit()

    return {"message": f"File {safe_name} uploaded", "filename": safe_name}


@router.get("/{page_id}/files")
async def list_landing_page_files(page_id: int, db: AsyncSession = Depends(get_db)):
    page = await db.get(LandingPage, page_id)
    if not page:
        raise HTTPException(404, "Landing page not found")
    lp_dir = _lp_dir(page_id)
    if not lp_dir.exists():
        return {"files": []}
    files = [f.relative_to(lp_dir).as_posix() for f in lp_dir.rglob("*") if f.is_file()]
    return {"files": files}


@router.delete("/{page_id}/files/{filename:path}")
async def delete_landing_page_file(page_id: int, filename: str, db: AsyncSession = Depends(get_db)):
    page = await db.get(LandingPage, page_id)
    if not page:
        raise HTTPException(404, "Landing page not found")
    lp_dir = _lp_dir(page_id)
    dest = lp_dir / filename
    # Security check
    try:
        dest.relative_to(lp_dir)
    except ValueError:
        raise HTTPException(400, "Invalid filename")
    if dest.exists():
        dest.unlink()
    files = page.files or []
    if filename in files:
        files.remove(filename)
    page.files = files
    await db.commit()
    return {"message": f"File {filename} deleted"}


@router.get("/templates/list")
async def list_prebuilt_templates():
    return get_all_templates()


@router.get("/templates/{template_name}")
async def get_prebuilt_template(template_name: str):
    t = get_template(template_name)
    if not t:
        raise HTTPException(404, "Template not found")
    return t


@router.post("/templates/{template_name}/use")
async def use_prebuilt_template(template_name: str, data: LandingPageCreate, db: AsyncSession = Depends(get_db)):
    t = get_template(template_name)
    if not t:
        raise HTTPException(404, "Template not found")
    page = LandingPage(
        name=data.name or t["name"],
        html_content=t["html"],
        capture_fields=t["capture_fields"],
        **{k: v for k, v in data.model_dump().items() if k not in ("name", "html_content", "capture_fields")}
    )
    db.add(page)
    await db.commit()
    await db.refresh(page)

    # Save to disk
    lp_dir = _lp_dir(page.id)
    lp_dir.mkdir(exist_ok=True)
    (lp_dir / page.root_file).write_text(page.html_content, encoding="utf-8")
    page.files = [page.root_file]
    await db.commit()

    return {"id": page.id, "message": f"Landing page created from {t['name']} template"}


@router.post("/import-url")
async def import_from_url(data: dict):
    import httpx
    url = data.get("url", "")
    if not url:
        raise HTTPException(400, "URL required")
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            r = await client.get(url)
            return {"html_content": r.text, "status_code": r.status_code}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch: {str(e)}")
