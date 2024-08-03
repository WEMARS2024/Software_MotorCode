import asyncio
import websockets
import serial
import time
import os

class Serial_Wrapper:
    def __init__(self, device='/dev/ttyUSB0', baud=921600):
        self.ser = serial.Serial(device, baud)

    def send_data(self, data, expect_confirmation=False, print_confirmation=True):
        self.ser.write(data)
        print('\t|||"{}" over serial.'.format(str(data)))
        if expect_confirmation:
            rec = self.ser.readline()
            if print_confirmation:
                print('\t||| Received "{}" over serial. Which "decode().rstrip()"s to \'{}\''.format(
                    str(rec), rec.decode('ASCII').rstrip()))

    def flush_buffer(self):
        self.ser.flushOutput()

def gradualIncrease(current_value, target_value, step=0.01, delay=0.05):
    if current_value < target_value:
        current_value += step

        yield current_value
        
    if current_value > target_value:
        current_value -= step
        yield current_value
        
    if -0.1<= target_value<=0.1:
        current_value = 0
        yield current_value
   
def format_joystick_data(axis_label, value):
    direction = '+' if value >= 0 else '-'
    formatted_value = f"{-abs(value):.2f}" if value < 0 else f"{abs(value):.2f}"
    return f"({axis_label},{formatted_value})"

async def receive_data():
    labels = ["ML", "MR"]
    current_values = [0, 0]
    uri = "ws://192.168.1.15:5678"  # Replace with the server's IP address
    serial_wrapper = Serial_Wrapper(device='/dev/ttyUSB0', baud=921600)
    async with websockets.connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            print(f"Received data: {data}")
            parsed_data = eval(data)
            print(parsed_data)
            for i in range(len(labels)):
                label2 = labels[i]
                inputval = parsed_data[i]

                for new_value in gradualIncrease(current_values[i], inputval):
                    formatted_data = format_joystick_data(label2, new_value).encode() + b'\n'
                    print(f"Formatted {label2} value: {formatted_data}")
                    serial_wrapper.send_data(formatted_data)
                    current_values[i] = new_value

asyncio.get_event_loop().run_until_complete(receive_data())
