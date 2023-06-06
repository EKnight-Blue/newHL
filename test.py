import msvcrt
import asyncio
from constants import red
import os
os.system('color')

PREVIOUS_LINE, FORMATTER = '\x1b[F', '{}'


class Cmd:
    text, index, prompt, animated, state = '', 0, (' > {}',), False, 0

    @staticmethod
    def no_formatter(string):
        lines = len(string.split('\n'))
        return f'{PREVIOUS_LINE * (lines - 1)}\r{string}{FORMATTER}'

    @staticmethod
    def with_formatter(string):
        pass

    def set_display_instructions(self):
        if not self.animated:
            return

    async def display_loop(self):
        pass

    async def read_loop(self):
        pass


sequences = {
    b'\x00G': 'beginning',
    b'\x00H': 'up',
    b'\x00I': 'page_up',
    b'\x00K': 'right',
    b'\x00M': 'right',
    b'\x00O': 'end',
    b'\x00P': 'down',
    b'\x00Q': 'page_down',
    b'\x00R': 'insert',
    b'\x00S': 'supp',
}

special = {
    b'\t': 'tab',
    b'\x08': 'backspace',
    b'\r': 'return'
}


text, running = [], True

# ┌—┴—┐
# |   |
# └———┘

new_prompts = (
    '┌— \n    > {{ {} }}\n   ',
    ' —┐\n    > {{ {} }}\n   ',
    '  ┐\n  | > {{ {} }}\n   ',
    '   \n  | > {{ {} }}\n  ┘',
    '   \n    > {{ {} }}\n —┘',
    '   \n    > {{ {} }}\n└— ',
    '   \n|   > {{ {} }}\n└  ',
    '┌  \n|   > {{ {} }}\n   ',
)

prompts = '-', '/', '|', '\\'


async def display_loop():
    state = 0
    # print(f'\r{prompts[state]} > {str().join(text[0:1])}', end='')
    print('`e\x1b[?25l\n')
    while running:
        print(f'\x1b[F\x1b[F\r{red(new_prompts[state].format("".join(text)))}', end='')
        state = (state + 1) % len(new_prompts)
        await asyncio.sleep(.1)
    print('\x1b[?25h')


async def getch():
    return await asyncio.to_thread(msvcrt.getch)


# b'\x03'
async def read_loop():
    global running
    while (char := await getch()) != b'\x03':
        try:
            text.append(char.decode())
        finally:
            continue
    running = False


async def main():
    await asyncio.gather(display_loop(), read_loop())


asyncio.run(main())


# try:
#     running = True
#     while (c := msvcrt.getch()) != b'\x03':
#         print(c)
#         # print(c.decode('utf-8'))
#         # print(f'\r{(list(text))}', end='')
# except KeyboardInterrupt:
#     print(text)
#
#
# # print('test')
# # print('test2')
# # print('\033[FNin', end='')
