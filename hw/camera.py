from picamera2 import Picamera2
from websockets.asyncio.client import connect
import RPi.GPIO as gp
import asyncio
import cv2
import time
import os

width = 320
height = 240

adapter_info = {
    "A": {
        "i2c_cmd": "i2cset -y 10 0x70 0x00 0x04",
        "gpio_sta": [0, 0, 1],
    },
    "B": {
        "i2c_cmd": "i2cset -y 10 0x70 0x00 0x05",
        "gpio_sta": [1, 0, 1],
    },
    "C": {
        "i2c_cmd": "i2cset -y 10 0x70 0x00 0x06",
        "gpio_sta": [0, 1, 0],
    },
    "D": {
        "i2c_cmd": "i2cset -y 10 0x70 0x00 0x07",
        "gpio_sta": [1, 1, 0],
    },
}


class Camera:
    camera_ids = ["A", "B", "C", "D"]

    def __init__(self, address):
        global picam2
        self.ws_addr = address
        gp.setwarnings(False)
        gp.setmode(gp.BOARD)
        gp.setup(7, gp.OUT)
        gp.setup(11, gp.OUT)
        gp.setup(12, gp.OUT)

        # Init MUX board
        for item in self.camera_ids:
            try:
                self.select_channel(item)
                self.init_i2c(item)
                time.sleep(0.5)
            except Exception as e:
                print(f"except on {item}: {str(e)}")

        # Init camera
        try:
            picam2 = Picamera2()
            picam2.configure(
                picam2.create_still_configuration(
                    main={"size": (320, 240), "format": "BGR888"}, buffer_count=2
                )
            )
            picam2.start()
            time.sleep(2)
            picam2.capture_array(wait=False)
            time.sleep(0.1)
        except Exception as e:
            print(f"except: {str(e)}")

    def select_channel(self, index):
        channel_info = adapter_info.get(index)
        if channel_info == None:
            print("Can't get this info")
        gpio_sta = channel_info["gpio_sta"]  # gpio write
        gp.output(7, gpio_sta[0])
        gp.output(11, gpio_sta[1])
        gp.output(12, gpio_sta[2])

    def init_i2c(self, index):
        channel_info = adapter_info.get(index)
        os.system(channel_info["i2c_cmd"])  # i2c write

    async def stream(self):
        async with connect(self.ws_addr) as ws:
            print("Connected to websocket")

            while True:
                for id in self.camera_ids:
                    self.select_channel(id)
                    await asyncio.sleep(0.1)
                    try:
                        buf = picam2.capture_array()
                        buf = picam2.capture_array()
                        ok, img = cv2.imencode(".jpg", buf)

                        if ok:
                            await ws.send((id + "|").encode("ascii") + img.tobytes())

                    except Exception as e:
                        print("capture_buffer: " + str(e))
                        await asyncio.sleep(0.1)


if __name__ == "__main__":
    camera = Camera("fill-inn-addr")
    asyncio.run(camera.stream())
