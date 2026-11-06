from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws")
async def ws_endpoint(websocket : WebSocket):
    await websocket.accept()
    print("client connected.: ", websocket.client)
    try:
        await websocket.send_text("Hello World")
        while True:
            msg = await websocket.receive_text()
            print("got: ", msg)
            await websocket.send_text(f"echo: {msg}")
    except WebSocketDisconnect:
        print("client disconnected.")


