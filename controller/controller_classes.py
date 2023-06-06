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

    def __init__(self, location):
        self.file, self.queue = location, []

    def read(self, f):
        return struct.unpack(self.event_format, f.read(self.event_length))[:2:-1]

    async def get_event(self, f):
        return await asyncio.to_thread(self.read, f)

    async def mainloop(self):
        try:
            with open(self.file, 'rb') as f:
                while self.running:
                    self.queue.append(Event(*await self.get_event(f)))
        except KeyboardInterrupt:
            pass
