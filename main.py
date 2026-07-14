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
            # Release a token
            task = self.waiting.pop(0)
# =====================================================================

queue = []
MAX_ITEMS = 5

# Create semaphore
item_ready = Semaphore(0)

led_D13 = Pins(D13_PIN)
rgb_led_D3 = RGBLed(D3_PIN, 4)
rgb_led_D5 = RGBLed(D5_PIN, 4)
rgb_led_D7 = RGBLed(D7_PIN, 4)

lcd1602 = LCD1602()
dht20 = DHT20()

async def task_LED_Blinky():
  while True:
    await asleep_ms(1000)
    led_D13.toggle()

async def task_1():
  while True:
    rgb_led_D3.show(0, hex_to_rgb('#ff0000'))
    await asleep_ms(1000)
    rgb_led_D3.show(0, hex_to_rgb('#000000'))
    await asleep_ms(1000)

async def task_2():
  while True:
    rgb_led_D5.show(0, hex_to_rgb('#00ff00'))
    await asleep_ms(1000)
    rgb_led_D5.show(0, hex_to_rgb('#000000'))
    await asleep_ms(1000)
    
    
async def task_3():
  while True:
    rgb_led_D7.show(0, hex_to_rgb('#0000ff'))
    await asleep_ms(1000)
    rgb_led_D7.show(0, hex_to_rgb('#000000'))
    await asleep_ms(1000)
   
async def task_LCD_DHT():
  while True:
    await asleep_ms(5000)
    lcd1602.clear()
    lcd1602.show(str((await dht20.atemperature())), 0, 0)
    lcd1602.show(str((await dht20.ahumidity())), 1, 0)

async def setup():

  print('App started')

  create_task(task_LED_Blinky())
  create_task(task_1())
  create_task(task_2())
  create_task(task_3())
  create_task(task_LCD_DHT())

async def main():
  await setup()
  while True:
    await asleep_ms(100)

run_loop(main())
