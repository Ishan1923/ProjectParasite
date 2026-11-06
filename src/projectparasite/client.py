import asyncio, sys
import websockets

from projectparasite import protocol

async def init(ip):
    async with websockets.connect(f"ws://{ip}:8000/ws") as ws:
        await ws.send(protocol.encode(protocol.Hello(name="popos", token=protocol.TOKEN)))
        reply = protocol.decode(await ws.recv())
        if isinstance(reply, protocol.Accepted):
            print("Connection accepted by server.")
            async for raw in ws:
                msg = protocol.decode(raw)
                print("Received message from server:", msg)
        else:
            print(f"Connection rejected by server: {reply.reason}")

def main():
    asyncio.run(init(sys.argv[1]))

if __name__ == "__main__":
    main()