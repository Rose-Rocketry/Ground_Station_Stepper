from cProfile import run
from multiprocessing.dummy import active_children
from types import coroutine
import websockets
import json
from time import sleep
import asyncio
import RPi.GPIO as GPIO
import logging

# TODO Re-engineer so that we can control the yagi with parallel executors.
logging.basicConfig(level=logging.INFO)
DIR = 17
STEP = 27
CW =1
CCW =0
SPR = 200 #steps per revolution (360/1.8)

delay = .018
step_count = SPR*5

status = {'status':"inactive"}
state_loop = asyncio.new_event_loop()

status_lock = asyncio.Lock()
message_queue = asyncio.Queue()

main_loop = asyncio.new_event_loop()

def setup_yagi():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR, GPIO.OUT)
    GPIO.setup(STEP, GPIO.OUT)
    GPIO.output(DIR, CW)

async def rotate_yagi():
    """Rotate the yagi two rotations"""
    for i in range(step_count*2):
        GPIO.output(STEP, GPIO.HIGH)
        await asyncio.sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        await asyncio.sleep(delay)
        
    logging.info("Done")
    await status_lock.acquire()
    status["status"] = "inactive"
    status_lock.release()

async def state_processor(socket):
    """Handles the state being received."""
    global status
    locked = False
    try:
        await socket.send(json.dumps(status))
        message = await asyncio.wait_for(socket.recv(), 0.1)
        logging.info(f"Received message: {message}")
        logging.info("Acquiring status lock")
        locked = True
        await status_lock.acquire()
        logging.info("Acquired Lock, Loading Message")
        status = json.loads(message)
    except ValueError:
        logging.warn("Issue when reading message")
    except asyncio.TimeoutError:
        pass
    finally:
        if locked:
            logging.info("Releasing lock")
            status_lock.release()
            locked = False
    await asyncio.sleep(0)

async def state_listener():
    """Event Handles the socket for the status manager."""
    logging.info("Trying to connect")
    async for systemctl_sock in (websockets.connect("ws://localhost:8000/ws/peripheral/usli_yagi_0/controller")):
        logging.info("Connected")
        try:            
            logging.info("Listening for messages.")
            while True:
                await state_processor(systemctl_sock)
        except websockets.ConnectionClosed:
            logging.warn("Connection to peripheral system closed.")
            continue

async def wait_for_activation():
    logging.info("Waiting For Activation")
    loop = asyncio.get_running_loop()
    while loop.is_running():
        await status_lock.acquire()
        active = (status["status"] == "active")
        status_lock.release()

        if active:
            break

        await asyncio.sleep(0.001)
    
    await status_lock.acquire()
    status["status"] = "listen"
    status_lock.release()
    logging.info("Activated!")
    
async def listen_for_landing():
    # Listen to the payload's packets for until the status says landed
    # TODO
    async for socket in websockets.connect("ws://localhost:8000/ws/telemetry/PiLoad/receive"):
        logging.info("Listening for landing.")
        try:
            packet_json = await socket.recv()
            packet = json.loads(packet_json)
            logging.info(packet)
            if packet.get("data",{"status":"dead"})["status"] == "landed":
                await status_lock.acquire()
                status["status"] = "rotating"
                status_lock.release()
                logging.info("Rotating")
                break
        except websockets.ConnectionClosed:
            pass

async def main():    
    loop = asyncio.get_running_loop()
    while loop.is_running():
        states = {
            'inactive': wait_for_activation,
            'listen': listen_for_landing,
            'rotating': rotate_yagi,
        }   
        runing_state = states.get(status["status"], wait_for_activation)
        await runing_state()

async def dergather():
    await asyncio.gather(main(), state_listener())

#Main Program
if __name__ == "__main__":
    setup_yagi()
    asyncio.run(dergather())
