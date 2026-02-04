import asyncio
from bleak import BleakScanner, BleakClient

# --- Hub names ---
HUB_NAME_BASE = "Base_hub"   # Change to the actual name of your base hub
HUB_NAME_CRANE = "Crane_hub" # Change to the actual name of your crane hub

UUID = "c5f50002-8280-46da-89f4-6d8051e4aeef"

async def main():
    # Scan for hubs by name
    base_device = await BleakScanner.find_device_by_name(HUB_NAME_BASE)
    if not base_device:
        print(f"Base hub '{HUB_NAME_BASE}' not found!")
        return

    crane_device = await BleakScanner.find_device_by_name(HUB_NAME_CRANE)
    if not crane_device:
        print(f"Crane hub '{HUB_NAME_CRANE}' not found!")
        return

    # Connect to both hubs
    async with BleakClient(base_device) as base, BleakClient(crane_device) as crane:
        print("Connected to both hubs!")

        # Example commands
        await base.write_gatt_char(UUID, b'\x01' + b'\x01' + b'\x00', response=True)   # Base forward
        #await crane.write_gatt_char(UUID, b'\x02', response=True)  # Crane reverse

        await asyncio.sleep(2)

        await base.write_gatt_char(UUID, b'\x02' + b'\x02' + b'\x00', response=True)   # Stop base
        #await crane.write_gatt_char(UUID, b'\x00', response=True)  # Stop crane

asyncio.run(main())
