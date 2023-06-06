import struct
import asyncio
from consts import *


class Event:
    # fixes the attributes
    __slots__ = 'button', 'type', 'value'

    def __init__(self, button, type_, value):
        self.button, self.type, self.value = button, 0 if type_ < 0 else type_, value

    def __repr__(self):
        return EVENT_FORMAT.format(EVENT_TYPES[self.type], BUTTONS.get((self.type, self.button), ""), self.value)


class ControllerButtons:
    running = True
    event_format = '3Bh2b'
    event_length = struct.calcsize(event_format)

    def __init__(self, joystick_file='/dev/input/js0'):
        self.file, self.queue = joystick_file, []

    def read(self, file):
        return struct.unpack(self.event_format, file.read(self.event_length))[:2:-1]

    async def get_event(self, file):
        return await asyncio.to_thread(self.read, file)

    async def mainloop(self):
        with open(self.file, 'rb') as file:
            while self.running:
                self.queue.append(Event(*await self.get_event(file)))


if __name__ == '__main__':
    c = ControllerButtons()
    with open(c.file, 'rb') as f:
        while True:
            print(Event(*c.read(f)))