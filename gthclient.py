# Gothello daemon client library
# Bart Massey <bart@cs.pdx.edu>

sock = None
fsock_in = None
fsock_out = None

client_version = "0.9.1"
server_base = 29068

who = None

msg_text = None
msg_code = None
msg_serial = None

white_time_control = None
black_time_control = None
my_time = None
opp_time = None

winner = None


class ClientError(Exception):
    pass


class MoveError(ClientError):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class MessageError(ClientError):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class ProtocolError(ClientError):
    def __init__(self, expression, text, message):
        self.expression = expression
        self.text = text
        self.message = message


def get_msg():
    global msg_code, msg_text
    while True:
        line = next(fsock_in)
        words = line.split()
        if len(words) > 0:
            break
    if len(words[0]) != 3:
        raise MessageError(line, "invalid message code")
    for c in words[0]:
        if c not in "0123456789":
            raise MessageError(c, "invalid message code digit")
    msg_code = int(words[0])
    msg_text = ' '.join(words[1:])
    

def closeall():
    fsock_out.close()
    fsock_in.close()
    sock.close()


def opponent(who):
    if who == "white":
        return "black"
    if who == "black":
        return "white"
    assert False


def get_time_controls():
    global white_time_control, black_time_control
    words = msg_text.split()
    time_controls = [int(t) for t in words[:2]]
    if len(time_controls) > 0:
        white_time_control = time_controls[0]
    if len(time_controls) > 1:
        black_time_control = time_controls[1]
    else:    
        black_time_control = white_time_control


def start_game(side, host, server):
    global sock, fsock_in, fsock_out
    global my_time, opp_time
    global who
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, server_base + server))
    fsock_in = sock.makefile("r", buffer=1, encoding="utf_8", newline="\r\n")
    fsock_out = sock.makefile("w", buffer=1, encoding="utf_8", newline="\r")

    get_msg()
    if msg_code != 0:
        raise ProtocolError(
            msg_code,
            msg_text,
            "illegal greeting",
        )

    print(
        "{} player {}".format(client_version, side),
        file=fsock_out,
    )

    get_msg()
    if msg_code not in {100, 101}:
        raise ProtocolError(
            msg_code,
            msg_text,
            "side failure",
        )

    if msg_code == 101:
        get_time_controls()
        if side == "white":
            my_time = white_time_control
            opp_time = black_time_control
        else:
            my_time = black_time_control
            opp_time = white_time_control

    get_msg()

    if (msg_code != 351 and side == "white") or \
       (msg_code != 352 and side == "black"):
        raise ProtocolError(
            msg_code,
            msg_text,
            "got wrong side",
        )

    who = side


def make_move(pos):
    global serial, winner, my_time

    if who == None:
        raise MoveError(None, None, "move before initialized")

    if winner != None:
        raise MoveError(None, None, "move with game over")

    if who == "black":
        ellipses = ""
        serial += 1
    elif who == "white":
        ellipses = " ..."
    else:
        assert False
      
    print(
        "{}{} {}".format(serial, ellipses, movebuf),
        file=fsock_out,
    )

    get_msg()
    if msg_code == 201:
        winner = who
    elif msg_code == 202:
        winner = opponent(who)
    elif msg_code == 203:
        raise MoveError(msg_code, msg_text, "game ended early")

    if winner != None:
        closeall()
        return False

    if msg_code != 200 and msg_code != 207:
        raise MoveError(msg_code, msg_text, "unexpected move result code")


    if msg_code == 207:
        my_time = get_time()

    get_msg();
    if msg_code < 311 or msg_code > 318:
        raise MoveError(msg_code, msg_text, "unexpected move status code")

    return True


def get_move():
    global serial, winner, my_time

    if who == None:
        raise MoveError(None, None, "move before initialized")

    if winner != None:
        raise MoveError(None, None, "move with game over")

    if who == "white":
        serial += 1

    get_msg()
    if (msg_code < 311 or msg_code > 326) and msg_code not in {361, 362}:
        raise MoveError(msg_code, msg_text, "bad move result code")

    if who == "white":
        codes = {312, 314, 316, 318, 323, 324, 326}
    else:
        codes = {311, 313, 315, 317, 321, 322, 325}
    if msg_code in codes:
        raise MoveError(msg_code, msg_text, "move received from wrong side")

    if (msg_code >= 311 and msg_code <= 318) or \
       (msg_code >= 321 and msg_code <= 326):
       get_move(pos)

    if who == "white":
        if msg_code in {311, 313, 315, 317}:
            return True
        if msg_code in {321, 361}:
            winner = "black"
            return False
        if msg_code in {322, 362}:
            winner = "white"
            return False
        if msg_code == 325:
            raise MoveError(msg_code, msg_text, "game terminated early")
    elif who == "black":
        if msg_code in {312, 314, 316, 318}:
            return True
        if msg_code in {323, 362}:
            winner = "white"
            return False
        if msg_code in {324, 361}:
            winner = "black"
            return False
        if msg_code == 326:
            raise MoveError(msg_code, msg_text, "game terminated early")

    raise MoveError(msg_code, msg_text, "unknown move status code")
