from inputs import get_gamepad # library used to read inputs from devices like keyboards, mice, and game controllers
import math
import threading
import asyncio
import websockets

class XboxController(object):
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self):

        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0
        self.LeftTrigger = 0
        self.RightTrigger = 0
        self.LeftBumper = 0
        self.RightBumper = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.B = 0
        self.LeftThumb = 0
        self.RightThumb = 0
        self.Back = 0
        self.Start = 0
        self.LeftDPad = 0
        self.RightDPad = 0
        self.UpDPad = 0
        self.DownDPad = 0

        # start a thread to monitor the controller without interfering with main program
        self._monitor_thread = threading.Thread(target=self._monitor_controller, args=())
        self._monitor_thread.daemon = True  # sets thread to run in the background and auto terminate when program exits
        self._monitor_thread.start()

    # return the buttons/triggers that you care about in this method
    def read(self): 
        LX = self.LeftJoystickX
        LY = self.LeftJoystickY
        RX = self.RightJoystickX
        RY = self.RightJoystickY
        LT = self.LeftTrigger
        RT = self.RightTrigger
        RB = self.RightBumper
        return [RY, LY, RX, LX, RT, LT, RB]

    def _monitor_controller(self):
        while True:
            events = get_gamepad()  # function from inputs library that retrieves a list of events from controller (each event is an input change)

            # ABS = absolute, BTN = key
            for event in events:    # loop through each event to process them
                if event.code == 'ABS_Y':
                    self.LeftJoystickY = (event.state / XboxController.MAX_JOY_VAL)  # normalize between -1 and 1
                elif event.code == 'ABS_X':
                    self.LeftJoystickX = (event.state / XboxController.MAX_JOY_VAL)  # normalize between -1 and 1
                elif event.code == 'ABS_RY':
                    self.RightJoystickY = (event.state / XboxController.MAX_JOY_VAL)  # normalize between -1 and 1
                elif event.code == 'ABS_RX':
                    self.RightJoystickX = (event.state / XboxController.MAX_JOY_VAL)  # normalize between -1 and 1
                elif event.code == 'ABS_Z':
                    self.LeftTrigger = (event.state / XboxController.MAX_TRIG_VAL)  # normalize between 0 and 1
                elif event.code == 'ABS_RZ':
                    self.RightTrigger = (event.state / XboxController.MAX_TRIG_VAL)  # normalize between 0 and 1
                elif event.code == 'BTN_TL':
                    self.LeftBumper = event.state
                elif event.code == 'BTN_TR':
                    self.RightBumper = event.state
                elif event.code == 'BTN_SOUTH':
                    self.A = event.state
                elif event.code == 'BTN_NORTH':
                    self.Y = event.state # previously switched with X
                elif event.code == 'BTN_WEST':
                    self.X = event.state # previously switched with Y
                elif event.code == 'BTN_EAST':
                    self.B = event.state
                elif event.code == 'BTN_THUMBL':
                    self.LeftThumb = event.state
                elif event.code == 'BTN_THUMBR':
                    self.RightThumb = event.state
                elif event.code == 'BTN_SELECT':
                    self.Back = event.state
                elif event.code == 'BTN_START':
                    self.Start = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY1':
                    self.LeftDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY2':
                    self.RightDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY3':
                    self.UpDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY4':
                    self.DownDPad = event.state

# reads controller inputs and sends them over WebSocket connection to connected client
async def handler(websocket, path):
    joy = XboxController()
    while True:
        data = str(joy.read()).encode() # converts list of inputs to a string and encodes it to bytes
        print(f"Sending data: {data}")  # Debug print
        await websocket.send(data)      # sends encoded data over WebSocket connection
        await asyncio.sleep(0.1)        # controls rate of data sent

# Create a WebSocket server that listens on all available IP addresses
start_server = websockets.serve(handler, "0.0.0.0", 5678)   # handler function handles incoming connections
print("WebSocket server started")

asyncio.get_event_loop().run_until_complete(start_server) # setups up server
asyncio.get_event_loop().run_forever()  # runs server indefinitely
