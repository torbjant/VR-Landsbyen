# import cv2
import asyncio
from functools import partial
from websockets.asyncio.server import serve, ServerConnection


async def send(websocket, data):
    await ServerConnection.send(websocket, message=data, text=True)


async def main():
    server_handler = partial(send, data="bruh")
    async with serve(server_handler, "localhost", 8765) as server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
