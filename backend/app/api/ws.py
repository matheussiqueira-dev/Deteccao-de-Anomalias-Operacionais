from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.core.security import decode_access_token
from app.database.session import SessionLocal
from app.schemas import MetricIn

router = APIRouter()


@router.websocket("/ws/alerts")
async def alerts_socket(websocket: WebSocket) -> None:
    if not await _validate_token(websocket):
        return
    manager = websocket.app.state.ws_manager
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


@router.websocket("/ws/ingest")
async def ingest_socket(websocket: WebSocket) -> None:
    if not await _validate_token(websocket):
        return
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            metric = MetricIn(
                timestamp=_parse_timestamp(payload.get("timestamp")),
                source=payload["source"],
                metric_name=payload["metric_name"],
                value=float(payload["value"]),
                unit=payload.get("unit"),
                tags=payload.get("tags") or [],
            )
            service = websocket.app.state.ingestion_service
            db = SessionLocal()
            try:
                anomalies = service.ingest_metrics(db, [metric])
                if anomalies:
                    await service.broadcast_anomalies(anomalies)
            finally:
                db.close()
    except WebSocketDisconnect:
        return
    except Exception:
        await websocket.close(code=1011)


@router.websocket("/ws/health")
async def health_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            await websocket.receive_text()
            await websocket.send_json({"status": "ok"})
    except WebSocketDisconnect:
        return


def _parse_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime.now(tz=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


async def _validate_token(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    if not token:
        return True
    try:
        decode_access_token(token)
    except JWTError:
        await websocket.accept()
        await websocket.close(code=1008)
        return False
    return True
