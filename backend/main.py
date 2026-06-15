"""HawkPhish - Main Application"""
import uvicorn
from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from contextlib import asynccontextmanager
from database import init_db, get_db
from routes import smtp, campaigns, templates, groups, tracking, landing_pages, proxies, smtp_server, audit_logs, external
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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
