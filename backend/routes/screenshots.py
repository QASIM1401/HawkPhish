"""HawkPhish - Screenshot & Preview Routes"""
import os
import io
import sys
import asyncio
import threading
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import LandingPage
import base64

router = APIRouter(prefix="/api/screenshots", tags=["Screenshots"])

SCREENSHOT_DIR = Path(os.path.dirname(__file__)).parent / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)


def _render_landing_page_html(page: LandingPage) -> str:
    """Build renderable HTML from landing page."""
    lp_dir = Path(os.path.dirname(__file__)).parent / "landing_pages" / str(page.id)
    root_file = page.root_file or "index.html"
    root_path = lp_dir / root_file
    if root_path.exists():
        return root_path.read_text(encoding="utf-8")
    return page.html_content or "<html><body><h1>Empty Page</h1></body></html>"


def _screenshot_in_thread(html: str, screenshot_path: Path):
    """Run Playwright in a dedicated thread with its own event loop.

    This avoids subprocess/loop conflicts on Windows when the app runs under
    uvicorn's SelectorEventLoop.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _run():
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page_obj = await browser.new_page(viewport={"width": 1280, "height": 900})
            await page_obj.set_content(html, wait_until="networkidle")
            await page_obj.wait_for_timeout(1500)
            await page_obj.screenshot(path=str(screenshot_path), full_page=True)
            await browser.close()

    try:
        loop.run_until_complete(_run())
    finally:
        loop.close()


@router.get("/landing-page/{page_id}")
async def screenshot_landing_page(page_id: int, db: AsyncSession = Depends(get_db)):
    """Take a screenshot of a landing page using Playwright."""
    page = await db.get(LandingPage, page_id)
    if not page:
        raise HTTPException(404, "Landing page not found")

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise HTTPException(500, "Playwright not installed. Run: playwright install chromium")

    html = _render_landing_page_html(page)
    screenshot_path = SCREENSHOT_DIR / f"lp_{page_id}.png"

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _screenshot_in_thread, html, screenshot_path)
    except Exception as e:
        import traceback
        log_path = SCREENSHOT_DIR / "error.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"Screenshot error for LP {page_id}: {e}\n{traceback.format_exc()}\n")
        raise HTTPException(500, f"Screenshot failed: {str(e)}")

    return FileResponse(str(screenshot_path), media_type="image/png", filename=f"landing_page_{page_id}.png")




@router.post("/email-preview")
async def email_client_preview(html: str = Form(...)):
    """Return HTML wrapped for email client preview (accepts form data)."""
    # Wrap in a basic email client preview container
    preview = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>Email Preview</title></head>
    <body style="margin:0;padding:20px;background:#f0f0f0;font-family:Arial,sans-serif;">
        <div style="max-width:600px;margin:0 auto;background:#fff;border:1px solid #ddd;box-shadow:0 2px 10px rgba(0,0,0,0.1);">
            <div style="background:#f8f8f8;padding:10px 15px;border-bottom:1px solid #ddd;font-size:12px;color:#666;">
                📧 Email Client Preview — 600px width
            </div>
            <div style="padding:20px;">
                {html}
            </div>
        </div>
    </body>
    </html>
    """
    return StreamingResponse(io.BytesIO(preview.encode()), media_type="text/html")
