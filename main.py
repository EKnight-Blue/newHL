import cmd
from micro import *


class BaseShell(cmd.Cmd, Manager):
    prompt, waiting = '(PicoShell) > ', None

    def __init__(self):
        cmd.Cmd.__init__(self)
        Manager.__init__(self, ShellMicro)
        print('\nFound :', *self.serials, sep='\n')

    @staticmethod
    def within_bits(x, bits, comp2=False):
        return 0 <= x + comp2 * (1 << bits - 1) < (1 << bits)

    @classmethod
    def comp_2(cls, x, bits=16):
        if not cls.within_bits(x, bits, True):
            raise ValueError(f"{x} is out bounds for a {bits} bits signed integer")
        return x + (x < 0) * (1 << bits)

    @classmethod
    def de_comp_2(cls, x, bits=16):
        if not cls.within_bits(x, bits):
            raise ValueError(f"{x} is out bounds for a {bits} bits integer")
        return x - ((x >> bits - 1) & 1) * (1 << bits)

    @staticmethod
    def float_to_int(num):
        # integer from the IEEE-754 representation of a float
        return sum(b << (8 * i) for i, b in enumerate(struct.pack('f', num)))

    @staticmethod
    def bytes_to_float(buffer):
        # float from its IEEE-754 representation with bytes
        return struct.unpack('!f', buffer)[0]

    def terminate(self, order_id):
        if order_id == self.waiting:
            self.waiting = None

    def send(self, id_, comp, arg):
        Manager.send(self, id_, comp, arg)
        self.wait(id_)

    def wait(self, order_id):
        self.waiting = order_id
        try:
            while self.waiting is not None:
                self.scan()
        except KeyboardInterrupt:
            Manager.send(self, RAW, 0, 0)


class ShellMicro(Micro):
    master: BaseShell

    def terminate(self, mess: bytes):
        Micro.terminate(self, mess)
        self.master.terminate(mess[0] & 0xf)

    def var_get(self, mess: bytes):
        Micro.var_get(self, mess)
        var_id, value = mess[0] & 0xf, BaseShell.bytes_to_float(mess[1:])
        self.log_method(f'{VARIABLES[var_id] if var_id < len(VARIABLES) else red("?")} = {value}', NOTHING)


# ----------------------------------------------- Decorators -----------------------------------------------------------

commands = {}


def command(func):
    n: str = func.__name__
    commands[f'do_{n[n.startswith("_"):]}'] = func
    return func


def arg_type(cls: type, arg: str):
    try:
        cls(arg)
        return True
    except ValueError:
        return False


def trier(func):
    def n_func(self, arg):
        try:
            return func(self, arg)
        except ValueError as e:
            print(f"Value error occurred in {func.__name__} : {e}")
            return 0
    n_func.__name__, n_func.__doc__ = func.__name__, func.__doc__
    return n_func


def arguments_number(n: int):
    def decor(func):
        def n_func(self: BaseShell, line: str):
            args = line.split()
            if len(args) != n:
                return print(f"Invalid number of arguments {len(args)} expected {n}")
            return func(self, *args)
        n_func.__name__, n_func.__doc__ = func.__name__, func.__doc__
        return n_func
    return decor


def simple_complete(value_set: tuple[str]):
    def decor(func):
        def complete(self: BaseShell, text, line, start_x, end_x):
            if text:
                return [x for x in value_set if x.startswith(text)]
            return value_set

        n: str = func.__name__
        commands[f'complete_{n[n.startswith("_"):]}'] = complete
        return func
    return decor


# -------------------------------------------------- Raw order command -------------------------------------------------

@trier
def raw_short(self: BaseShell, arg):
    return self.comp_2(int(arg), 16)


@trier
def raw_int(self: BaseShell, arg):
    return self.comp_2(int(arg), 32)


@trier
def raw_float(self: BaseShell, arg):
    return self.float_to_int(float(arg))


raw_key_words = {
    '-a0': raw_short,
    '-a1': raw_short,
    '-a': raw_int,
    '-f': raw_float,
}


@command
def order(self: BaseShell, line):
    words, running, result = iter(line.split()), True, dict()
    try:
        result['id'], result['comp'] = int(next(words)), int(next(words))
        if not self.within_bits(result['id'], 4) or not self.within_bits(result['comp'], 4):
            raise ValueError('first 2 arguments must be between 0 and 15')
    except StopIteration:
        return print("Expected at least 4 arguments")
    except ValueError as e:
        return print(e)

    while running:
        try:
            curr = next(words)
            if curr not in raw_key_words:
                return print(f'Invalid key word {curr}')
            try:
                result[curr] = raw_key_words[curr](self, next(words))
            except StopIteration:
                return print(f"Expected 1 argument after {curr}")
        except StopIteration:
            running = False

    if '-a0' in result and '-a1' in result:
        return self.send(result['id'], result['comp'], (result['-a0'] << 16) | result['-a1'])
    elif '-a' in result:
        return self.send(result['id'], result['comp'], result['-a'])
    elif '-f' in result:
        return self.send(result['id'], result['comp'], result['-f'])
    print('Invalid arguments')

# ------------------------------------------------- Commands -----------------------------------------------------------


@command
@arguments_number(2)
def motors(self: BaseShell, left: str, right: str):
    if not arg_type(int, left) or not arg_type(int, right):
        return print(f"Expected integer arguments")
    try:
        left, right = self.comp_2(int(left)), self.comp_2(int(right))
    except ValueError as e:
        return print(e)
    self.send(RAW, 0, (left << 16) | right)


@command
@arguments_number(1)
@simple_complete(VARIABLES + ('-a',))
def _get(self: BaseShell, var: str):
    if var == '-a':
        for i in range(len(VARIABLES)):
            self.send(GET, i, 0)
        return
    if var not in VARIABLES:
        return print(f"Invalid variable name {var} expected one among {', '.join(VARIABLES + ('-a',))}")
    self.send(GET, VARIABLES.index(var), 0)


@command
@arguments_number(2)
@simple_complete(VARIABLES)
def _set(self: BaseShell, var: str, value: str):
    if not arg_type(float, value):
        return print(f"Expected float value")
    if var not in VARIABLES:
        return print(f"Invalid variable name {var} expected one among {', '.join(VARIABLES)}")
    self.send(SET, VARIABLES.index(var), self.float_to_int(float(value)))


@command
@arguments_number(1)
@simple_complete(LEVELS)
def log(self: BaseShell, level):
    if level not in LEVELS:
        return print(f"Invalid log level {level} expected one among {', '.join(LEVELS)}")
    self.log_level = LEVELS.index(level)


@command
@arguments_number(0)
def reset(self: BaseShell):
    self.reset()
    print('\nFound :', *self.serials, sep='\n')


@command
def _quit(self: BaseShell, line):
    Manager.send(self, RAW, 0, 0)
    for usb in self.serials:
        usb.serial.close()
    return 1


Shell = type('Shell', (BaseShell,), commands)

if __name__ == '__main__':
    Shell().cmdloop()
