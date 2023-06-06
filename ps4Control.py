from controller import Controller, Event
from controller.consts import *
from micro import Manager, Micro
from constants import *


class Controls:
    def __init__(self):
        self.controller = Controller()
        self.manager = Manager(Micro)
        self.dist, self.dir = 0, 0

    def send(self):
        right = (self.dist + self.dir) // 16
        right = right + 800 * (right > 0) - 800 * (right < 0)
        left = (self.dist - self.dir) // 16
        left = left + 800 * (left > 0) - 800 * (left < 0)
        self.manager.send(RAW, 0, (left << 16) | right)

    def nothing(self, event):
        pass

    def distance(self, event: Event):
        self.dist = event.value
        self.send()

    def direction(self, event: Event):
        self.dir = event.value
        self.send()

    manage_events = {
        (ANALOG, LY): 'distance',
        (ANALOG, RX): 'direction'
    }

    def mainloop(self):
        with open(self.controller.file, 'rb') as f:
            while True:
                res = self.controller.read(f)
                print(res)
                event = Event(*res)
                # print(event)
                getattr(self, self.manage_events.get((event.type, event.button), 'nothing'))(event)


Controls().mainloop()
