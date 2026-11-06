import asyncio, sys
import websockets

async def main(ip):

    async with websockets.connect(f"ws://{ip}:8000/ws") as ws:
        print(await ws.recv())
        await ws.send("Hello Server")
        print(await ws.recv())

asyncio.run(main(sys.argv[1]))