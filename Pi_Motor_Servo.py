import asyncio
import websockets
import serial
import time

class Serial_Wrapper:
    def __init__(self, device='/dev/serial0', baud=115200):
        self.ser = serial.Serial(device, baud)
        self.ser.flush()  # Flush the serial buffer

    def send_data(self, data, expect_confirmation=False, print_confirmation=True):
        self.ser.write(data)
        if print_confirmation:
            print(f"\n!!! Sent {str(data)} over serial.")
        if expect_confirmation:
            rec = self.ser.readline()
            if print_confirmation:
                print(f"\n!!! Received {str(rec)} over serial.")
            return rec

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

def format_motor_data(axis_label, input):
    if axis_label == "ML":
        formatted_value = f"{-abs(input):.2f}" if input > 0 else f"{abs(input):.2f}"
    else:
        formatted_value = f"{-abs(input):.2f}" if input < 0 else f"{abs(input):.2f}"   
    return f"({axis_label},{formatted_value})"


def format_servo_data(input):
    byte_value = int(input * 10)  # Multiply by 10 and convert to int
    return byte_value.to_bytes(1, 'big', signed=True)  # Convert to signed byte

async def receive_data():
    uri = 'ws://172.20.10.9:5678'  # Replace with the server's IP address
    serial_wrapper = Serial_Wrapper(device='/dev/serial0', baud=115200)
    
    # Define labels for servo and motor control
    servo_label = [b'X']
    motor_labels = ["ML", "MR"]
    current_values = [0, 0]

    control_mode = 'motor'  # Initial control mode
    toggle = 0

    try:
        async with websockets.connect(uri, timeout=20) as websocket:
            while True:
                try:
                    data = await websocket.recv()
                    print(f"Received data: {data}")
                    
                    parsed_data = eval(data)
                    print(parsed_data)

                    # Check for Y button press to toggle control mode
                    if parsed_data[6] == 1:
                        toggle = 1
                    if toggle == 1 and parsed_data[6] == 0:
                        toggle = 0
                        control_mode = 'motor' if control_mode == 'servo' else 'servo'
                        print(f"Toggled control mode to {control_mode}")

                    # Servo control
                    if control_mode == 'servo':

                        # Create the list with 'X' and the formatted inputs
                        formatted_data_list = servo_label + [format_servo_data(value) 
                                                             for value in parsed_data]

                        # Convert the list to bytes
                        formatted_data_bytes = b''.join(formatted_data_list) + b'\n'
                        print(formatted_data_bytes)
                        serial_wrapper.send_data(formatted_data) 

                    # Motor control
                    else:  
                        for i in range(len(motor_labels)):
                            label = motor_labels[i]
                            input = parsed_data[i]
                            for new_value in gradualIncrease(current_values[i], input):
                                formatted_data = format_motor_data(label, new_value).encode() + b'\n'
                                print(f"Formatted {label} value: {formatted_data}")
                                serial_wrapper.send_data(formatted_data)
                                current_values[i] = new_value
                    
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"WebSocket connection closed: {e}")
                    break
                except Exception as e:
                    print(f"Error processing data: {e}")
    except Exception as e:
        print(f"Error connecting to WebSocket: {e}")

asyncio.get_event_loop().run_until_complete(receive_data())