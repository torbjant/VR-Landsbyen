import sys
if sys.platform == "win32":
    import ctypes
    ctypes.windll.ole32.CoInitializeEx(None, 0x0)

import asyncio
from contextlib import suppress
from bleak import BleakScanner, BleakClient
import pygame

PYBRICKS_COMMAND_EVENT_CHAR_UUID = "c5f50002-8280-46da-89f4-6d8051e4aeef"

BASE_HUB = "Base_hub"
CRANE_HUB = "Crane_hub"


def get_input_state(joysticks):
    pygame.event.pump()

    if not joysticks:
        keys = pygame.key.get_pressed()
        return {
            "type": "keyboard",
            "keys": keys
        }

    state = {
        "type": "joystick"
    }

    # LEFT joystick (index 0)
    if len(joysticks) > 0:
        js_left = joysticks[0]
        state.update({
            "x_left": js_left.get_axis(0),
            "y_left": js_left.get_axis(1),
            "throttle_left": js_left.get_axis(2),
            "rotation_left": js_left.get_axis(3),
            "hat_left": js_left.get_hat(0),
            "button_1_left": js_left.get_button(0),
            "button_2_left": js_left.get_button(1),
            "button_3_left": js_left.get_button(2),
        })

    # RIGHT joystick (index 1)
    if len(joysticks) > 1:
        js_right = joysticks[1]
        state.update({
            "x_right": js_right.get_axis(0),
            "y_right": js_right.get_axis(1),
            "throttle_right": js_right.get_axis(2),
            "rotation_right": js_right.get_axis(3),
            "hat_right": js_right.get_hat(0),
            "button_1_right": js_right.get_button(0),
            "button_2_right": js_right.get_button(1),
            "button_3_right": js_right.get_button(2),
        })

    return state


def map_value(value):
    return int((value + 1) * 127)

def map_controls(state):

    global right, left, rotate, boom, jib, hoist
    right = left = rotate = boom = jib = hoist = 127
    base = [127, 127, 127, 0]
    crane = [127, 127, 127, 0]
    running = True

    if state["type"] == "keyboard":
        keys = state["keys"]

        if keys[pygame.K_ESCAPE]:
            base[3] = 1
            crane[3] = 1
            running = False

        # --- BASE HUB ---
        if keys[pygame.K_w]:
            base[0] = base[1] = 100
        if keys[pygame.K_s]:
            base[0] = base[1] = -100
        if keys[pygame.K_a]:
            base[2] = 100
        if keys[pygame.K_d]:
            base[2] = -100

        # --- CRANE HUB ---
        if keys[pygame.K_UP]:
            crane[0] = 100
        if keys[pygame.K_DOWN]:
            crane[0] = -100

        if keys[pygame.K_LEFT]:
            crane[1] = 100
        if keys[pygame.K_RIGHT]:
            crane[1] = -100

        if keys[pygame.K_COMMA]:
            crane[2] = 100
        if keys[pygame.K_PERIOD]:
            crane[2] = -100

    else:
        # Joystick mode
        hat = state["hat_right"]
        toggle = state["button_2_right"]

        rotate = map_value(state["x_right"])

        if toggle:
            left = right = map_value(state["y_right"])

        else:
            boom = map_value(state["y_right"])
            jib = map_value(state["y_left"])

            if hat == (0, 1):
                hoist = 200
            elif hat == (0, -1):
                hoist = 50
            else:
                hoist = 127



    base[0] = left
    base[1] = right
    base[2] = rotate

    crane[0] = boom
    crane[1] = jib
    crane[2] = hoist
    return base, crane, running



class HubController:
    def __init__(self, name):
        self.name = name
        self.device = None
        self.client = None
        self.ready_event = asyncio.Event()

    async def connect(self):
        print(f"Scanning for {self.name}...")
        self.device = await BleakScanner.find_device_by_name(self.name)

        if self.device is None:
            raise Exception(f"Could not find {self.name}")

        self.client = BleakClient(self.device, self.handle_disconnect)
        await self.client.connect()
        await self.client.start_notify(
            PYBRICKS_COMMAND_EVENT_CHAR_UUID,
            self.handle_rx
        )
        print(f"Connected to {self.name}")

    def handle_disconnect(self, _):
        print(f"{self.name} disconnected.")

    def handle_rx(self, _, data: bytearray):
        if data[0] == 0x01:
            payload = data[1:]
            if payload == b"rdy":
                self.ready_event.set()

    async def send(self, data):
        await self.ready_event.wait()
        self.ready_event.clear()
        await self.client.write_gatt_char(
            PYBRICKS_COMMAND_EVENT_CHAR_UUID,
            b"\x06" + bytes(data),
            response=True
        )

    async def disconnect(self):
        await self.client.disconnect()


async def main():

    base = HubController(BASE_HUB)
    crane = HubController(CRANE_HUB)

    await base.connect()
    await crane.connect()

    print("Start both hub programs now.")

    pygame.init()
    pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Dual Hub Controller")

    pygame.joystick.init()

    joysticks = []

    for i in range(pygame.joystick.get_count()):
        js = pygame.joystick.Joystick(i)
        js.init()
        joysticks.append(js)


    running = True

    while running:
        state = get_input_state(joysticks)
        base_data, crane_data, running = map_controls(state)

        await base.send(base_data)
        await crane.send(crane_data)

        await asyncio.sleep(0.02)


    pygame.quit()

    await base.disconnect()
    await crane.disconnect()

    print("Done.")


if __name__ == "__main__":
    with suppress(asyncio.CancelledError):
        asyncio.run(main())
