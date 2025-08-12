from kasa import SmartBulb
import asyncio

async def run():
    bulb = SmartBulb("192.168.1.193")  # Replace with YOUR IP
    await bulb.update()
    print("Current state:", "ON" if bulb.is_on else "OFF")
    await bulb.turn_on()

asyncio.run(run())
