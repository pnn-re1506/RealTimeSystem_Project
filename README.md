# YoloUNO Smart Climate Controller (RTOS)

The Smart Climate Control System project uses the YoloUNO microcontroller platform (MicroPython). The project implements a Real-Time Operating System (RTOS) architecture featuring Inter-task Communication mechanisms via Queues, Semaphores, and Mutexes.

## Key Features

- **Real-time Sensor Reading:** Collects temperature and humidity data from the DHT20 sensor.
- **Visual Display:** Continuously displays environmental parameters on an LCD1602 screen.
- **Multi-device Control (Simulated via RGB LEDs):**
  - **Heater:** Turns Red (< 20°C), Green (20°C - 28°C), or Orange (> 28°C).
  - **Cooler:** Turns Green (temperature > 28°C) for 5 seconds, then turns off.
  - **Humidifier:** Activates when humidity < 50%, running on a State Machine cycle: Green (5s) -> Yellow (3s) -> Red (2s) -> Off.
- **System Heartbeat:** The D13 LED blinks every second to indicate the system is operating normally.

## Software Architecture (RTOS)

The project applies the **Producer - Consumer** pattern:
- **Producer (Task Read Sensor):** Reads the DHT20 sensor, utilizing a `Mutex` to protect the I2C hardware resource. It packages the data and pushes it into 4 independent `Queues`.
- **Consumers (LCD, Heater, Cooler, Humidifier):** These tasks wait in an `IDLE` state and are awakened by a `Semaphore` whenever the Producer enqueues new data.
- **State Machine Integration:** For tasks requiring delays (like the Cooler and Humidifier cycles), a State Machine mechanism combined with non-blocking delays (`await asleep_ms`) is used. This optimizes CPU resources and ensures the system remains responsive without blocking other tasks.
