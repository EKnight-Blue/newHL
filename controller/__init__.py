from controller_classes import ControllerButtons
import asyncio


class Controller:
    """
    Tool to get events from a ps4 controller, works on UNIX
    """
    
    def __init__(self, joystick_file='/dev/input/js0'):
        self.buttons = ControllerButtons(joystick_file)

    def get_events(self):
        yield from self.buttons.queue


async def read(c: Controller):
    while True:
        print(*c.get_events(), sep='\n')
        await asyncio.sleep(1.)


async def main():
    c = Controller()
    await asyncio.gather(c.buttons.mainloop(), read(c))

if __name__ == '__main__':
    asyncio.run(main())