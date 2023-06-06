import serial
import time
import struct

from constants import *
from serial.tools.list_ports import comports


class Manager:
    log_level = LOW
    serials: tuple = ()

    def __init__(self, micro: type):
        self.micro = micro
        self.reset()

    def reset(self):
        for usb in self.serials:
            usb.serial.close()

        self.serials = tuple(
            self.micro(serial.Serial(usb.device, BAUD_RATE, writeTimeout=0), self) for usb in comports()
        )

        for s in self.serials:
            s.pre_sync()

        time.sleep(1.)
        self.clear()
        self.send(IDE, 0, 0)

        date = time.perf_counter()
        while time.perf_counter() - date < 5. and any(usb.id == len(usb.names) - 1 for usb in self.serials):
            self.scan()
        self.serials = tuple(usb for usb in self.serials if usb.id != len(usb.names) - 1)

    def clear(self):
        for usb in self.serials:
            usb.clear()

    def send(self, id_, comp, arg):
        for usb in self.serials:
            usb.send(usb.prepare(id_, comp, arg))

    def scan(self):
        for usb in self.serials:
            usb.scan()


class Micro:
    names = 'Generic', 'Movement', 'Action', 'Unknown'

    def __init__(self, s: serial.Serial, master: Manager):
        self.serial, self.id, self.master = s, len(self.names) - 1, master

    def log_method(self, text: str, level=LOW):
        if level <= self.master.log_level:
            print(f'{self} {text}')

    def pre_sync(self):
        self.serial.write(SYNC_STRING)

    def clear(self):
        self.serial.read(self.serial.in_waiting)

    def sync(self):
        self.pre_sync()
        time.sleep(1.)
        self.clear()

    def scan(self):
        if self.serial.in_waiting >= FEEDBACK_LENGTH:
            self.receive()

    def receive(self):
        res: bytes = self.serial.read(FEEDBACK_LENGTH)
        self.log_method(f'{IN} 0x{res.hex()}', LOW)
        self.feedback(res)

    def __repr__(self):
        return f'{self.names[self.id]}({self.serial.port})'

    def prepare(self, id_, comp, arg):
        return int.to_bytes((((id_ << 4) | comp) << 32) | arg, ORDER_LENGTH, 'big')

    def send(self, mess: bytes):
        self.log_method(f'{OUT} 0x{mess.hex()}', LOW)
        self.serial.write(mess)

    def acknowledge(self, mess: bytes):
        order_id = mess[0] & 0xf
        self.log_method(f'{yellow("ACK")} {blue(ORDERS[order_id]) if order_id < len(ORDERS) else red("?")}', MEDIUM)

    def var_get(self, mess: bytes):
        var_id = mess[0] & 0xf
        value = struct.unpack('!f', mess[1:])[0]
        self.log_method(
            f'{yellow("GET")} {blue(VARIABLES[var_id]) if var_id < len(VARIABLES) else red("?")} {value}', MEDIUM
        )

    def terminate(self, mess: bytes):
        order_id = mess[0] & 0xf
        self.log_method(f'{yellow("TER")} {blue(ORDERS[order_id]) if order_id < len(ORDERS) else red("?")}', MEDIUM)

    def deliver_id(self, mess: bytes):
        self.id = min(mess[0] & 0xf, len(self.names) - 1)
        self.log_method(f'{yellow("ID")} {blue(mess[0] & 0xf)}', MEDIUM)

    def feedback(self, mess: bytes):
        feed_id = mess[0] >> 4
        if feed_id >= len(FEEDBACKS):
            return
        getattr(self, FEEDBACKS[feed_id].lower())(mess)


if __name__ == '__main__':
    Manager.log_level = LOW
    Manager(Micro)
