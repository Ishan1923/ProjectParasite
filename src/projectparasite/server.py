import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from . import protocol 

import os, secrets

TOKEN = os.environ["PARASITE_TOKEN"]  # must be set in the environment

app = FastAPI()

@app.websocket("/ws")
async def ws_endpoint(websocket : WebSocket):
    await websocket.accept()
    print("client connected.: ", websocket.client)
    try:

        #initial hello for setting up the connection
        msg = protocol.decode(await websocket.receive_text())
        
        if not isinstance(msg, protocol.Hello):
            await websocket.close()
            return
        
        if not secrets.compare_digest(msg.token.encode(), TOKEN.encode()):
            await websocket.send_text(protocol.encode(protocol.Rejected(reason="bad token")))
            await websocket.close()
            return
        
        answer = await asyncio.to_thread(input, f"Accept connection from {msg.name}? (y/n): ")
        
        if answer.lower() == "y":
            await websocket.send_text(protocol.encode(protocol.Accepted()))
        else:
            await websocket.send_text(protocol.encode(protocol.Rejected(reason="denied by user")))
            await websocket.close()
            return




        # loop for receiving messages from the client
        while True:

            msg = protocol.decode(await websocket.receive_text())   

            print("got: ", msg)

    except WebSocketDisconnect:
        print("client disconnected.: ", websocket.client)
    except Exception as e:
        print(f"Error: {e}")
