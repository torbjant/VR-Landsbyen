import asyncio
import numpy as np
import cv2
import websockets


def decode_payload(message: bytes):
    # message format: b"A|<jpeg bytes>"
    sep = message.find(b"|")
    if sep == -1:
        return None, None
    cam_id = message[:sep].decode("ascii", errors="ignore")
    jpg = message[sep + 1 :]
    arr = np.frombuffer(jpg, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return cam_id, frame


async def handler(ws):
    async for message in ws:
        if not isinstance(message, (bytes)):
            continue

        cam_id, frame = decode_payload(message)
        if frame is None:
            continue

        cv2.imshow(f"Camera {cam_id}", frame)
        # quit program
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765, max_size=None):
        print(f"Starting server on ???")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        cv2.destroyAllWindows()
