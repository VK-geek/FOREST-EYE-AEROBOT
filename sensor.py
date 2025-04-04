import time
import board
import adafruit_dht
import Adafruit_BMP.BMP085 as BMP085
import smbus
import lgpio

# Initialize MQ-2 (GPIO17)
MQ2_PIN = 17
h = lgpio.gpiochip_open(0)  # Open GPIO chip
lgpio.gpio_claim_input(h, MQ2_PIN)  # Set GPIO17 as input

# Initialize DHT11 sensor
DHT_SENSOR = adafruit_dht.DHT11(board.D4)  # Ensure this is the correct GPIO pin

# Initialize BMP180 sensor
bus = smbus.SMBus(1)  # I2C bus number for Raspberry Pi
bmp_sensor = BMP085.BMP085(busnum=1)  # Specify I2C bus number

while True:
    try:
        # Read temperature and humidity from DHT11
        dht_temperature = DHT_SENSOR.temperature
        dht_humidity = DHT_SENSOR.humidity

        # Read from BMP180
        bmp_temperature = bmp_sensor.read_temperature()  # °C
        bmp_pressure = bmp_sensor.read_pressure()  # Pascals
        bmp_altitude = bmp_sensor.read_altitude()  # Meters

        # Read MQ-2 sensor
        mq2_value = lgpio.gpio_read(h, MQ2_PIN)

        # Print sensor data
        print("\n--- Sensor Readings ---")
        print(f"DHT11 - Temperature: {dht_temperature:.1f}°C, Humidity: {dht_humidity:.1f}%")
        print(f"BMP180 - Temperature: {bmp_temperature:.2f}°C")
        print(f"BMP180 - Pressure: {bmp_pressure / 100:.2f} hPa")  # Convert Pascals to hPa
        print(f"BMP180 - Altitude: {bmp_altitude:.2f} m")
        print(f"MQ-2 - Gas Detected: {'Yes' if mq2_value == 0 else 'No'}")

    except RuntimeError as error:
        print(f"Error reading sensors: {error}")

    except KeyboardInterrupt:
        print("\nExiting program...")
        lgpio.gpiochip_close(h)  # Close GPIO chip
        break

    time.sleep(2)  # Wait before next reading
