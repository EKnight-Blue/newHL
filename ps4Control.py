import asyncio

from controller import Controller, Event
from controller.consts import *
from micro import Manager, Micro
from constants import *


class Controls:
    running = True

    def __init__(self):
        self.controller = Controller()
        self.manager = Manager(Micro)
        self.dist, self.dir = 0, 0

    def send(self):
        right = -(self.dist + self.dir) // 16
        right = right + 800 * (right > 0) - 800 * (right < 0)
        right = self.manager.comp_2(right)
        left = -(self.dist - self.dir) // 16
        left = left + 800 * (left > 0) - 800 * (left < 0)
        left = self.manager.comp_2(left)
        self.manager.send(RAW, 0, (left << 16) | right)

    def stop(self, event):
        self.running = False

    def nothing(self, event):
        pass

    def options(self, event):
        if event.value:
            self.manager.log_level = (self.manager.log_level + 1) % len(LEVELS)

    def distance(self, event: Event):
        self.dist = event.value
        self.send()

    def direction(self, event: Event):
        self.dir = event.value
        self.send()

    manage_events = {
        (ANALOG, LY): 'distance',
        (ANALOG, RX): 'direction',
        (DIGITAL, OPTIONS): 'options',
        (DIGITAL, PS): 'stop'
    }

    async def event_loop(self):
        with open(self.controller.file, 'rb') as f:
            while self.running:
                res = await self.controller.get_event(f)
                event = Event(*res)
                getattr(self, self.manage_events.get((event.type, event.button), 'nothing'))(event)

    async def micro_loop(self):
        while self.running:
            self.manager.scan()
            await asyncio.sleep(0.5)

    async def mainloop(self):
        await asyncio.gather(self.event_loop(), self.micro_loop())


if __name__ == '__main__':
    asyncio.run(Controls().mainloop())