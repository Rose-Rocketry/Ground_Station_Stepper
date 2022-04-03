import websockets
import json
from time import sleep
import asyncio
import RPi.GPIO as GPIO

# TODO Re-engineer so that we can control the yagi with parallel executors.

DIR = 17
STEP = 27
CW =1
CCW =0
SPR = 200 #steps per revolution (360/1.8)


delay = .108
step_count = SPR

def setup_yagi():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR, GPIO.OUT)
    GPIO.setup(STEP, GPIO.OUT)
    GPIO.output(DIR, CW)


status = {'status':"inactive"}

def test_yagi():
    for i in range(step_count*2):
        GPIO.output(STEP, GPIO.HIGH)
        sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        sleep(delay)
    
    status.set("status", "inactive")

async def main():    
    # Listen to the yagi's status:
    async for socket in websockets.connect("ws://localhost:8000/ws/peripheral/usli_yagi_0/controller"):
        try:
            await socket.send(json.dumps(status))
            while not status.get("status") == "ready":
                status_json = await socket.recv()
                if status_json.get("status") == "test":
                    test_yagi()
                try:
                    status = json.loads(status_json)
                except ValueError:
                    print("failed to read new status")
            
            #When yagi is set active end the socket connection
            status.set("status", "ready")
            await socket.send(json.dumps(status))
            break
            
        except websockets.ConnectionClosed:
            continue

    # Listen to the payload's packets for until the status says landed
    async for socket in websockets.connect("ws://localhost:8000/ws/telemetry/PiLoad/receive"):
        try:
            packet_json = await socket.recv()
            packet = json.loads(packet_json)
            if packet.get("status") == "landed":
                break                
        except websockets.ConnectionClosed:
            continue

    # Connect back to set status to rotating.
    async for socket in websockets.connect("ws://localhost:8000/ws/peripheral/usli_yagi_0/controller"):
            try:
                status.set("status","rotating")
                await socket.send(json.dumps(status))
                break
            except websockets.ConnectionClosed:
                continue

    #Rotate the yagi two rotations
    for i in range(step_count*2):
        GPIO.output(STEP, GPIO.HIGH)
        sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        sleep(delay)

    status.set("status","waiting")

    

#Main Program
if __name__ == "__main__":
    setup_yagi()
    loop = asyncio.get_event_loop()
    task = loop.create_task(main)
    loop.run_forever()