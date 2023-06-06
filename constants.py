SYNC_STRING = b"\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9"
BAUD_RATE = 115200


ESCAPE = '\x1b['


class Codes:
    _red, _green, _yellow, _blue = range(91, 95)

    @staticmethod
    def color(text, color):
        return f'{ESCAPE}{getattr(Codes, f"_{color}")}m{text}{ESCAPE}0m'


red, green, yellow, blue = (
    (lambda text: Codes.color(text, 'red')),
    (lambda text: Codes.color(text, 'green')),
    (lambda text: Codes.color(text, 'yellow')),
    (lambda text: Codes.color(text, 'blue'))
)

OUT, IN = green('-<-'), red('->-')
# log levels
NOTHING, LOW, MEDIUM, HIGH = range(4)
LEVELS = 'nothing', 'low', 'medium', 'high'


ORDER_LENGTH = FEEDBACK_LENGTH = 5
IDE, RAW, MOV, GET, SET, _, _, _, _, _, _, _, _, _, _, _ = range(16)
ORDERS = (
    'DELIVER ID',
    'RAW MOVEMENT COMMAND',
    'MOVEMENT COMMAND',
    'GET VARIABLE',
    'SET VARIABLE'
)

ACK, TER, ID_, GE_, _, _, _, _, _, _, _, _, _, _, _, _ = range(16)
FEEDBACKS = (
    'ACKNOWLEDGE',
    'TERMINATE',
    'DELIVER_ID',
    'VAR_GET'
)


VARIABLES = (
    'dist_Kp',
    'dist_Ki',
    'dist_Kd',
    'dir_Kp',
    'dir_Ki',
    'dir_Kd',
    'min_move'
)
