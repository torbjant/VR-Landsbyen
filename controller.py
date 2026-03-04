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

def apply_deadband(value, threshold=0.05):
    if abs(value) < threshold:
        return 0
    return value

def get_input_state(joysticks):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return {"type": "quit"}

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
        hat_right = state["hat_right"]
        hat_left = state["hat_left"]
        rotate = map_value(state["rotation_left"])

        if state["rotation_right"] > 0.1 or state["rotation_right"] < -0.1:
            left = -state["rotation_right"]
            right = state["rotation_right"]

        else:
            y = state["y_right"]  # forward/back
            x = state["x_right"]  # turn

            if abs(y) < 0.05:
                y = 0
            if abs(x) < 0.05:
                x = 0

            left = y - x
            right = y + x

        left = max(-1, min(1, left))
        right = max(-1, min(1, right))

        left = map_value(left)
        right = map_value(right)
        boom = map_value(state["y_left"])

        jib = state["hat_left"]

        if hat_right == (0, 1):
            hoist = 255

        elif hat_right == (0, -1):
            hoist = 0

        else:
            hoist = 127

        if hat_left == (0, -1):
            jib = 255

        elif hat_left == (0, 1):
            jib = 0

        else:
            jib = 127

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
        if not self.client or not self.client.is_connected:
            return

        if not self.ready_event.is_set():
            return  # skip if not ready

        self.ready_event.clear()

        try:
            await self.client.write_gatt_char(
                PYBRICKS_COMMAND_EVENT_CHAR_UUID,
                b"\x06" + bytes(data),
                response=False
            )
        except Exception as e:
            print(f"{self.name} write error:", e)

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

    last_base = None
    last_crane = None

    while running:
        state = get_input_state(joysticks)
        if state["type"] == "quit":
            running = False
            break
        base_data, crane_data, running = map_controls(state)


        if base_data != last_base:
            await base.send(base_data)
            last_base = base_data.copy()

        if crane_data != last_crane:
            await crane.send(crane_data)
            last_crane = crane_data.copy()

        await asyncio.sleep(0.03)  # slower

        if not running:
            base_data[3] = 0x01
            await base.send(base_data)
            crane_data[3] = 0x01
            await crane.send(crane_data)

    pygame.quit()

    await base.disconnect()
    await crane.disconnect()

    print("Done.")


if __name__ == "__main__":
    with suppress(asyncio.CancelledError):
        asyncio.run(main())
