
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

def gradualIncrease(current_value, target_value, step=0.01):
    while abs(current_value - target_value) > step:
        if current_value < target_value:
            current_value += step
        else:
            current_value -= step
        yield current_value
    yield target_value
   

def format_joystick_data(axis_label, input):
    if axis_label == "ML":
        formatted_value = f"{-abs(input):.2f}" if input > 0 else f"{abs(input):.2f}" # Invert left side inputs
    else:
        formatted_value = f"{-abs(input):.2f}" if input < 0 else f"{abs(input):.2f}"
    return f"({axis_label}, {formatted_value})"


async def receive_data():
    
    uri = "ws://192.168.1.15:5678"  # Replace with the server's IP address
    serial_wrapper = Serial_Wrapper(device='/dev/ttyUSB0', baud=921600)
    labels = ["MR", "ML"]
    current_values = [0, 0]

    try:
        async with websockets.connect(uri, timeout=20) as websocket:
            while True:
                try:
                    data = await websocket.recv()
                    print(f"Received data: {data}")

                    parsed_data = eval(data)
                    print(parsed_data)

                    for i in range(len(labels)):
                        label = label[i]
                        input = parsed_data[i]

                        for new_value in gradualIncrease(current_values[i], input):
                            formatted_data = format_joystick_data(label, new_value).encode() + b'\n'
                            print(f"Formatted {label} value: {formatted_data}")
                            serial_wrapper.send_data(formatted_data)
                            current_values[i] = new_value

                except websockets.exceptions.ConnectionClosed as e:
                    print(f"Websocket connection closed: {e}")
                    break
                except Exception as e:
                    print(f"Error processing data: {e}")
    except Exception as e:
        print(f"Error connecting to WebSocket: {e}")

asyncio.get_event_loop().run_until_complete(receive_data())
