from yolo_uno import *
from pins import *
from lcd1602 import *
from dht20 import *
import asyncio

class Semaphore:
    def __init__(self, value=1):
        if value < 0:
            raise ValueError("ValueError")
        self.value = value
        self.waiting = [] # List of tokens

    async def acquire(self):
        if self.value > 0:
            self.value -= 1
            return True
        
       
        curr_task = asyncio.current_task() if hasattr(asyncio, 'current_task') else None
        self.waiting.append(curr_task)
        
        # Create an event for waiting
        ev = asyncio.Event()
        async def wait_placeholder():
            await ev.wait()
            
        # Pending loop
        while self.value <= 0:
            await asleep_ms(10) # Wait until token is released
            if curr_task not in self.waiting: 
                break
                
        self.value -= 1
        return True

    def release(self):
        self.value += 1
        if self.waiting:
            task = self.waiting.pop(0)

led_D13        = Pins(D13_PIN)
heater_led     = RGBLed(D3_PIN, 4)  
cooler_led     = RGBLed(D5_PIN, 4)  
humidifier_led = RGBLed(D7_PIN, 4)  
lcd1602        = LCD1602()
dht20          = DHT20()

MAX_ITEMS = 5
heater_queue = []
cooler_queue = []
humi_queue   = []
lcd_queue    = []

heater_sem = Semaphore(0)   # signal: new data for heater
cooler_sem = Semaphore(0)   # signal: new data for cooler
humi_sem   = Semaphore(0)   # signal: new data for humidifier
lcd_sem    = Semaphore(0)   # signal: new data for LCD

HEATER_COLD   = 20    # T < 20 → RED
HEATER_HOT    = 28    # T >= 28 → ORANGE
COOLER_THRESH = 28    # T > 28 → activate cooler
HUMI_THRESH   = 50    # H < 50% → activate humidifier

# Colors (hex)
COLOR_OFF    = '#000000'
COLOR_RED    = '#ff0000'
COLOR_GREEN  = '#00ff00'
COLOR_ORANGE = '#ff8c00'
COLOR_YELLOW = '#ffff00'

def make_sensor_data(temp, humi):
    return {'temperature': temp, 'humidity': humi}

def enqueue(queue, sem, data):
    if len(queue) < MAX_ITEMS:
        queue.append(data)
        sem.release()

# Task 1: Blinky — LED13 toggle every 1 second (independent)
async def task_blinky(): ...

# Task 2: Read Sensor — DHT20 every 5s, enqueue to all consumers
async def task_read_sensor(): ...

# Task 3: LCD Display — show temp & humidity
async def task_lcd(): ...

# Task 4: Heater — 3-color threshold indicator
async def task_heater(): ...

# Task 5: Cooler — GREEN 5s if temp > threshold
async def task_cooler(): ...

# Task 6: Humidifier — state machine GREEN→YELLOW→RED
async def task_humidifier(): ...

async def setup():
    create_task(task_blinky())
    create_task(task_read_sensor())
    create_task(task_lcd())
    create_task(task_heater())
    create_task(task_cooler())
    create_task(task_humidifier())
