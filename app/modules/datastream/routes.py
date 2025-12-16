from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from app.modules.datastream.services import WebsocketManager, SubscribeRequest

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    manager: WebsocketManager = ws.app.state.datastream_ws_mgr
    await manager.connect(ws)
    try:
        while True:
            msg = await ws.receive_json()
            req = SubscribeRequest(**msg)
            await manager.handle_subscribe(ws, req)
    except WebSocketDisconnect:
        await manager.disconnect(ws)
