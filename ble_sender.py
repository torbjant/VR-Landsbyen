import asyncio
from bleak import BleakClient
import sys

DEVICE_ADDRESS_BASE_HUB = sys.argv[1]
DEVICE_ADDRESS_CRANE_HUB = sys.argv[2]
CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

async def main():
    async with BleakClient(DEVICE_ADDRESS_BASE_HUB) as base_hub, \
               BleakClient(DEVICE_ADDRESS_CRANE_HUB) as crane_hub:

        while True:
            line = sys.stdin.readline().strip()
            if not line:
                break

            parts = line.split(",")
            data_base = bytes(map(int, parts[:3]))
            data_crane = bytes(map(int, parts[3:]))

            await base_hub.write_gatt_char(CHAR_UUID, data_base)
            await crane_hub.write_gatt_char(CHAR_UUID, data_crane)

asyncio.run(main())
