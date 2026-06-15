"""HawkPhish - Built-in SMTP Server Routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.smtp_server import HawkPhishSMTPServer

router = APIRouter(prefix="/api/smtp-server", tags=["SMTP Server"])

# Global server instance
_server_instance: HawkPhishSMTPServer | None = None


@router.get("/status")
async def get_status():
    global _server_instance
    if _server_instance:
        return _server_instance.status()
    return {"running": False, "host": None, "port": None, "connections": 0, "emails_processed": 0}


@router.post("/start")
async def start_server(data: dict = None):
    global _server_instance
    if _server_instance and _server_instance.running:
        return {"message": "Server already running", "status": _server_instance.status()}
    
    host = (data or {}).get("host", "0.0.0.0")
    port = (data or {}).get("port", 2525)
    
    _server_instance = HawkPhishSMTPServer(host, port)
    try:
        result = _server_instance.start()
        return {"message": "SMTP server started", **result}
    except Exception as e:
        _server_instance = None
        raise HTTPException(500, f"Failed to start server: {str(e)}")


@router.post("/stop")
async def stop_server():
    global _server_instance
    if not _server_instance:
        return {"message": "Server not running"}
    result = _server_instance.stop()
    _server_instance = None
    return {"message": "SMTP server stopped", **result}
