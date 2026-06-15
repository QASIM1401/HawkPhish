"""HawkPhish - Main Application"""
import uvicorn
from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from contextlib import asynccontextmanager
from database import init_db, get_db
from routes import smtp, campaigns, templates, groups, tracking, landing_pages, proxies, smtp_server, audit_logs, external, analytics, validation, webhooks, payloads, screenshots
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="HawkPhish",
    description="Advanced Phishing Simulation Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(smtp.router)
app.include_router(campaigns.router)
app.include_router(templates.router)
app.include_router(groups.router)
app.include_router(tracking.router)
app.include_router(landing_pages.router)
app.include_router(proxies.router)
app.include_router(smtp_server.router)
app.include_router(audit_logs.router)
app.include_router(external.router)
app.include_router(analytics.router)
app.include_router(validation.router)
app.include_router(webhooks.router)
app.include_router(payloads.router)
app.include_router(screenshots.router)


@app.get("/payloads/{token}/download")
async def payload_download_alias(token: str):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/api/payloads/{token}/download")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    assets_path = os.path.join(frontend_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_path, "index.html"))


if __name__ == "__main__":
    import ssl
    import sys
    import asyncio

    # Playwright (and other subprocess-based tools) require ProactorEventLoop on Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Check for HTTPS configuration
    cert_file = os.getenv("SSL_CERT_FILE")
    key_file = os.getenv("SSL_KEY_FILE")
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    ssl_context = None
    if cert_file and key_file:
        if os.path.exists(cert_file) and os.path.exists(key_file):
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(cert_file, key_file)
            print(f"[HTTPS] enabled on {host}:{port}")
        else:
            print(f"[WARN] SSL cert/key not found: {cert_file}, {key_file}")
            print("   Starting in HTTP mode")
    else:
        print(f"[HTTP] mode on {host}:{port}")
        print("   Set SSL_CERT_FILE and SSL_KEY_FILE env vars for HTTPS")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        ssl_keyfile=key_file if ssl_context else None,
        ssl_certfile=cert_file if ssl_context else None,
    )
