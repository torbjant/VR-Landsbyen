import asyncio
from bleak import BleakClient
import sys

DEVICE_ADDRESS_BASE_HUB = sys.argv[1]
DEVICE_ADDRESS_CRANE_HUB = sys.argv[2]
UUID = "c5f50002-8280-46da-89f4-6d8051e4aeef"

async def main():
    async with BleakClient(DEVICE_ADDRESS_BASE_HUB) as base, BleakClient(DEVICE_ADDRESS_CRANE_HUB) as crane:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            # Expect line like: 255,128,64,200,100,50
            parts = list(map(int, line.strip().split(",")))
            base_data = bytes(parts[:3])
            crane_data = bytes(parts[3:])
            await asyncio.gather(
                base.write_gatt_char(UUID, b"\x06" + base_data, response=True),
                crane.write_gatt_char(UUID, b"\x06" + crane_data, response=True)
            )

asyncio.run(main())
