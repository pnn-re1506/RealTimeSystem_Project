from yolo_uno import *
from pins import *
from lcd1602 import *
from dht20 import *
import asyncio

class Semaphore:
    def __init__(self, value=1):
        if value < 0:
            raise ValueError("Semaphore initial value cannot be negative")
        self.value = value
        self.waiting = []

    async def acquire(self):
        if self.value > 0:
            self.value -= 1
            return True
        curr_task = asyncio.current_task() if hasattr(asyncio, 'current_task') else id(self)
        self.waiting.append(curr_task)
        while curr_task in self.waiting:
            await asleep_ms(10)
        return True

    def release(self):
        if self.waiting:
            self.waiting.pop(0)
        else:
            self.value += 1

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
data_mutex = Semaphore(1)  # mutex

HEATER_COLD   = 20    # T < 20 → RED
HEATER_HOT    = 28    # T >= 28 → ORANGE
COOLER_THRESH = 28    # T > 28 → activate cooler
HUMI_THRESH   = 50    # H < 50% → activate humidifier

# Timing (ms)
SENSOR_INTERVAL_MS = 5000
BLINKY_INTERVAL_MS = 1000
COOLER_DURATION_MS = 5000
HUMI_GREEN_MS  = 5000
HUMI_YELLOW_MS = 3000
HUMI_RED_MS    = 2000

# Colors (hex)
COLOR_OFF    = '#000000'
COLOR_RED    = '#ff0000'
COLOR_GREEN  = '#00ff00'
COLOR_ORANGE = '#ff0500'
COLOR_YELLOW = '#ffff00'

def make_sensor_data(temp, humi):
    return {'temperature': temp, 'humidity': humi}

def enqueue(queue, sem, data):
    if len(queue) < MAX_ITEMS:
        queue.append(data)
        sem.release()

# Task 1: Blinky — LED13 toggle every 1 second (independent)
async def task_blinky():
    while True:
        await asleep_ms(BLINKY_INTERVAL_MS)
        led_D13.toggle()

# Task 2: Read Sensor — DHT20 every 5s, enqueue to all consumers
async def task_read_sensor():
    await data_mutex.acquire()
    temp = await dht20.atemperature()
    humi = await dht20.ahumidity()
    data_mutex.release()

    print('TEMP:', temp, '°C | HUMI:', humi, '%')

    data = make_sensor_data(temp, humi)
            
    if len(humi_queue) == 0:
        humi_queue.append(data)
        humi_sem.release()

    await asleep_ms(SENSOR_INTERVAL_MS)

# Task 3: LCD Display — show temp & humidity
async def task_lcd():
    lcd1602.clear()
    while True:
        await lcd_sem.acquire()
        data = lcd_queue.pop(0)
        temp = data['temperature']
        humi = data['humidity']

        lcd1602.show('TEMP: ', 0, 0)
        lcd1602.show(str(temp), 0, 6)
        lcd1602.show(chr(0), 0, 11)
        lcd1602.show('C', 0, 12)
        
        lcd1602.show('HUMI: ', 1, 0)
        lcd1602.show(str(humi), 1, 6)
        lcd1602.show('%', 1, 12)

# Task 4: Heater — 3-color threshold indicator
async def task_heater():
    while True:
        await heater_sem.acquire()
        data = heater_queue.pop(0)
        temp = data['temperature']

        if temp < HEATER_COLD:
            heater_led.show(0, hex_to_rgb(COLOR_RED))
        elif temp < HEATER_HOT:
            heater_led.show(0, hex_to_rgb(COLOR_GREEN))
        else:
            heater_led.show(0, hex_to_rgb(COLOR_ORANGE))

# Task 5: Cooler — GREEN 5s if temp > threshold
async def task_cooler():
    state = 'IDLE'
    while True:
        if state == 'IDLE':
            await cooler_sem.acquire()
            data = cooler_queue.pop(0)
            if data['temperature'] > COOLER_THRESH:
                state = 'COOLING'
            else:
                cooler_led.show(0, hex_to_rgb(COLOR_OFF))

        elif state == 'COOLING':
            cooler_led.show(0, hex_to_rgb(COLOR_GREEN))
            await asleep_ms(COOLER_DURATION_MS)
            cooler_led.show(0, hex_to_rgb(COLOR_OFF))
            state = 'IDLE'


# Task 6: Humidifier — state machine GREEN→YELLOW→RED
async def task_humidifier():
    state = 'IDLE'
    while True:
        if state == 'IDLE':
            await humi_sem.acquire()
            data = humi_queue[0]
            if data['humidity'] < HUMI_THRESH:
                state = 'PHASE_GREEN'
            else:
                humidifier_led.show(0, hex_to_rgb(COLOR_OFF))
                humi_queue.pop(0)

        elif state == 'PHASE_GREEN':
            humidifier_led.show(0, hex_to_rgb(COLOR_GREEN))
            await asleep_ms(HUMI_GREEN_MS)
            state = 'PHASE_YELLOW'

        elif state == 'PHASE_YELLOW':
            humidifier_led.show(0, hex_to_rgb(COLOR_YELLOW))
            await asleep_ms(HUMI_YELLOW_MS)
            state = 'PHASE_RED'

        elif state == 'PHASE_RED':
            humidifier_led.show(0, hex_to_rgb(COLOR_RED))
            await asleep_ms(HUMI_RED_MS)
            humidifier_led.show(0, hex_to_rgb(COLOR_OFF))
            humi_queue.pop(0)
            state = 'IDLE'

async def setup():
    create_task(task_blinky())
    create_task(task_read_sensor())
    create_task(task_lcd())
    create_task(task_heater())
    create_task(task_cooler())
    create_task(task_humidifier())

async def main():
    await setup()
    while True:
        await asleep_ms(100)

run_loop(main())
