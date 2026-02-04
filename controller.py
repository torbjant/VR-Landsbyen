import pygame
import asyncio
from bleak import BleakClient
from mock_controller import MockController

DEVICE_ADDRESS_BASE_HUB = "XX:XX:XX:XX:XX:XX"
DEVICE_ADDRESS_CRANE_HUB = "XX:XX:XX:XX:XX:XX"
CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # UART TX

pygame.init()
screen = pygame.display.set_mode((100, 100))  # tiny window for events

# pygame.joystick.init()
# js = pygame.joystick.Joystick(0)
# js.init()

js = MockController()

def poll_keyboard(mock_joystick):
    keys = pygame.key.get_pressed()

    mock_joystick.axes[0] = -1.0 if keys[pygame.K_a] else (1.0 if keys[pygame.K_d] else 0.0)
    mock_joystick.axes[1] = 1.0 if keys[pygame.K_w] else (-1.0 if keys[pygame.K_s] else 0.0)

    mock_joystick.axes[2] = -1.0 if keys[pygame.K_j] else (1.0 if keys[pygame.K_l] else 0.0)
    mock_joystick.axes[3] = 1.0 if keys[pygame.K_i] else (-1.0 if keys[pygame.K_k] else 0.0)

    mock_joystick.buttons[0] = 1 if keys[pygame.K_q] else 0
    mock_joystick.buttons[1] = 1 if keys[pygame.K_e] else 0
    mock_joystick.buttons[2] = 1 if keys[pygame.K_u] else 0
    mock_joystick.buttons[3] = 1 if keys[pygame.K_o] else 0
    mock_joystick.buttons[4] = 1 if keys[pygame.K_SPACE] else 0


async def main():
    async with BleakClient(DEVICE_ADDRESS_BASE_HUB) as base_hub, BleakClient(DEVICE_ADDRESS_CRANE_HUB) as crane_hub:
        while True:
            pygame.event.pump()
            poll_keyboard(js)

            y_left = js.get_axis(0)
            x_left = js.get_axis(1)
            y_right = js.get_axis(2)
            x_right = js.get_axis(3)

            if js.get_button(4):
                data_base = bytes([
                    int((x_right + 1) * 127),  # Rotation
                    int((y_right + 1) * 127),  # Drive right
                    int((y_left + 1) * 127)    # Drive left
                ])

                data_crane = bytes([
                    127,                       # Boom
                    127,                       # Jib
                    js.get_button(1),          # Hoist up
                    js.get_button(0)           # Hoist down
                ])
            else:
                data_base = bytes([
                    int((y_right + 1) * 127),  # Rotation
                    127,                       # Drive right
                    127                        # Drive left
                ])

                data_crane = bytes([
                    int((y_right + 1) * 127),  # Boom
                    int((y_left + 1) * 127),   # Jib
                    js.get_button(1),          # Hoist up
                    js.get_button(0)           # Hoist down
                ])


            # Send data to base hub
            await base_hub.write_gatt_char(CHAR_UUID, data_base)
            # Send data to crane hub
            await crane_hub.write_gatt_char(CHAR_UUID, data_crane)

asyncio.run(main())
