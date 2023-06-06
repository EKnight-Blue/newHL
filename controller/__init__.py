from controller_classes import ControllerButtons
import asyncio


class Controller:
    """
    Tool to get events from a ps4 controller, works on UNIX
    """
    
    def __init__(self, joystick_file='/dev/input/js0'):
        self.buttons = ControllerButtons(joystick_file)

    def get_events(self):
        q = self.buttons.queue
        self.buttons.queue = []
        return q


async def read(c: Controller):
    try:
        while True:
            events = c.get_events()
            if events:
                print(*events, sep='\n')
            await asyncio.sleep(.1)
    except KeyboardInterrupt:
        c.buttons.running = False


async def main():
    c = Controller()
    await asyncio.gather(c.buttons.mainloop(), read(c))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass