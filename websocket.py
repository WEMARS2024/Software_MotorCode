import asyncio
import websockets
import serial
import time
import os
marker_file_path = '/home/wemars/firstRun'

if not os.path.exists(marker_file_path):
    with open(marker_file_path,'w') as marker_file:
        marker_file.write('this prevents pi from repeated reboot')
    os.system('sudo reboot')
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
    return f"(ML,{formatted_value})"

async def receive_data():
    current_LX = 0
    uri = "ws://192.168.1.15:5678"  # Replace with the server's IP address
    serial_wrapper = Serial_Wrapper(device='/dev/ttyUSB0', baud=921600)
    async with websockets.connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            print(f"Received data: {data}")
            parsed_data = eval(data)
            print(parsed_data)
            target_LX = parsed_data[2]

            print(f"Target LX value: {target_LX}")

            for new_LX in gradualIncrease(current_LX, target_LX):
                formatted_LX = format_joystick_data('ML', new_LX).encode()
                print(f"Formatted LX value: {formatted_LX}")
                serial_wrapper.send_data(formatted_LX)
                current_LX = new_LX  # Update the current_LX to the new value

asyncio.get_event_loop().run_until_complete(receive_data())
