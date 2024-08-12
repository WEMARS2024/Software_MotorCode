import asyncio
import websockets
import serial
import time

class Serial_Wrapper:
    def __init__(self, device='/dev/tty/USB1',device1 = '/dev/tty/USB0',baud=921600):
      self.ser = serial.Serial(device,baud)
      self.ser1 = serial.Serial(device1,baud)
      self.ser.flush()  # Flush the serial buffer
      self.ser1.flush() #flushin serial buffer 2 

    def send_data(self, data,control_mode, expect_confirmation=False, print_confirmation=True):
        if control_mode == 'motor':
            self.ser.write(data)
        elif control_mode == 'servo':
            self.ser1.write(data)
            
            print('hello')
            
        
        
        if print_confirmation:
            print(f"\n!!! Sent {str(data)} over serial.")
        if expect_confirmation:
            rec = ser.readline()
            if print_confirmation:
                print(f"\n!!! Received {str(rec)} over serial.")
            return rec

    def flush_buffer(self,control_mode):
        if control_mode == 'motor':
           self.ser.flushOutput()
        else:
            self.ser1.flushOutpucontrol_modet()

def gradualIncrease(current_value, target_value, step=0.01, delay=0.05):
    if current_value < target_value:
        current_value += step
        yield current_value
        
    if current_value > target_value:
        current_value -= step
        yield current_value
        
    if -0.1 <= target_value <= 0.1:
        current_value = 0
        yield current_value

def format_motor_data(axis_label, input):
    if axis_label == "ML":
        formatted_value = f"{-abs(input):.2f}" if input > 0 else f"{abs(input):.2f}"
    else:
        formatted_value = f"{-abs(input):.2f}" if input < 0 else f"{abs(input):.2f}"   
    return f"({axis_label},{formatted_value})"


def format_servo_data(axis_label,input):
    formatted_value = f"{-abs(input):.2f}" if input < 0 else f"{abs(input):.2f}"   
    return f"({axis_label},{formatted_value})"

async def receive_data():
    uri = 'ws://192.168.1.15:6000'  # Replace with the server's IP address
    serial_wrapper = Serial_Wrapper(device = '/dev/ttyUSB1',device1 ='/dev/ttyUSB0', baud=921600)
    
    # Define labels for servo and motor control
    servo_label = ['RY','LY','RX','LX','RT','LT']
    motor_labels = ["ML", "MR"]
    current_values = [0, 0]

    control_mode = 'motor'  # Initial control mode
    toggle = False

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
                        toggle = True
                    elif toggle and parsed_data[6] == 0:
                        toggle = False
                        control_mode = 'motor' if control_mode == 'servo' else 'servo'
                        print(f"Toggled control mode to {control_mode}")

                    # Servo control
                    if control_mode == 'servo':
                        for i in range (len(servo_label)):
                            label=servo_label[i]
                            input= parsed_data[i]
                            
                        # Create the list with 'X' and the formatted input
                            formatted_data = format_servo_data(label,input).encode()+ b'\n'
                            print(formatted_data)
                            serial_wrapper.send_data(formatted_data, control_mode)
                            print(control_mode)

                    # Motor control
                    else:  
                        for i in range(len(motor_labels)):
                            label = motor_labels[i]
                            input = parsed_data[i]
                            for new_value in gradualIncrease(current_values[i], input):
                                formatted_data = format_motor_data(label, new_value).encode() + b'\n'
                                print(f"Formatted {label} value: {formatted_data}")
                                serial_wrapper.send_data(formatted_data,control_mode)
                                current_values[i] = new_value
                    
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"WebSocket connection closed: {e}")
                    break
                except Exception as e:
                    print(f"Error processing data: {e}")
    except Exception as e:
        print(f"Error connecting to WebSocket: {e}")

asyncio.get_event_loop().run_until_complete(receive_data())
