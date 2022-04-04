from cProfile import run
from types import coroutine
import websockets
import json
from time import sleep
import asyncio
import RPi.GPIO as GPIO
import logging

# TODO Re-engineer so that we can control the yagi with parallel executors.

DIR = 17
STEP = 27
CW =1
CCW =0
SPR = 200 #steps per revolution (360/1.8)

delay = .108
step_count = SPR

status = {'status':"inactive"}
state_loop = asyncio.new_event_loop()

status_lock = asyncio.Lock()
message_queue = asyncio.Queue()

def setup_yagi():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR, GPIO.OUT)
    GPIO.setup(STEP, GPIO.OUT)
    GPIO.output(DIR, CW)

@asyncio.coroutine
def rotate_yagi():
    """Rotate the yagi two rotations"""
    for i in range(step_count*2):
        GPIO.output(STEP, GPIO.HIGH)
        asyncio.sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        asyncio.sleep(delay)

async def state_processor(socket):
    """Handles the state being received."""
    logging.info("Listening for messages.")
    message = await socket.recv()
    try:
        logging.info("Aquiring status lock")
        await status_lock.acquire()
        logging.info("Aquired Lock, Loading Message")
        status = json.loads(message)
    except ValueError:
        pass
    finally:
        logging.info("Releasing lock")
        status_lock.release()
    await asyncio.sleep(0)

async def state_listener():
    """Event Handles the socket for the status manager."""
    async for systemctl_sock in (websockets.connect("ws://localhost:8000/ws/peripheral/usli_yagi_0/controller")):
        try:
            state_processor(systemctl_sock)
        except websockets.ConnectionClosed:
            logging.warn("Connection to peripheral system closed.")
            continue

async def wait_for_activation():
    await status_lock.acquire()
    if status["status"] == "active": 
        status_lock.release()
        asyncio.get_running_loop().stop()

    status_lock.release()
    await asyncio.sleep(0)
    
    
async def listen_for_landing():
    # Listen to the payload's packets for until the status says landed
    # TODO
    async for socket in websockets.connect("ws://localhost:8000/ws/telemetry/PiLoad/receive"):
        try:
            packet_json = await socket.recv()
            packet = json.loads(packet_json)
            if packet["status"] == "landed":
                await status_lock.acquire;
                status["status"] = "rotating"
                status_lock.release()
        except websockets.ConnectionClosed:
            pass

async def main():    
    
    states = {
        'inactive':wait_for_activation,
        'listen': listen_for_landing,
        'rotating': rotate_yagi,
    }   
    runing_state = states.get(status["status"], wait_for_activation)
    state_loop.create_task(runing_state)
    state_loop.run_forever()

#Main Program
if __name__ == "__main__":
    setup_yagi()
    main_loop = asyncio.new_event_loop()
    main_loop.create_task(main())
    main_loop.create_task(state_listener())
    main_loop.run_forever()