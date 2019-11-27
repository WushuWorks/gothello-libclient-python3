# Gothello daemon client library
# Bart Massey <bart@cs.pdx.edu>

import socket

client_version = "0.9.1"
server_base = 29068

class ClientError(Exception):
    pass


class MoveError(ClientError):
    ILLEGAL = 1
    DONE = 2
    DISCO = 3

    def __init__(self, cause, message):
        self.cause = cause
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

def opponent(who):
    if who == "white":
        return "black"
    if who == "black":
        return "white"
    assert False

class GthClient(object):

    def __init__(self, side, host, server):
        self.sock = None
        self.fsock_in = None
        self.fsock_out = None

        self.serial = 0

        self.white_time_control = None
        self.black_time_control = None
        self.my_time = None
        self.opp_time = None

        self.winner = None
        self.who = side

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, server_base + server))
        self.fsock_in = self.sock.makefile(
            "r",
            buffering=1,
            encoding="utf_8",
            newline="\r\n",
        )
        self.fsock_out = self.sock.makefile(
            "w",
            buffering=1,
            encoding="utf_8",
            newline="\r",
        )

        msg_code, msg_text = self.get_msg()
        if msg_code != 0:
            raise ProtocolError(
                msg_code,
                msg_text,
                "illegal greeting",
            )

        self.send("{} player {}".format(client_version, side))

        msg_code, msg_text = self.get_msg()
        if msg_code not in {100, 101}:
            raise ProtocolError(
                msg_code,
                msg_text,
                "side failure",
            )

        if msg_code == 101:
            self.get_time_controls(msg_text)
            if side == "white":
                self.my_time = white_time_control
                self.opp_time = black_time_control
            else:
                self.my_time = black_time_control
                self.opp_time = white_time_control

        msg_code, msg_text = self.get_msg()
        if (msg_code != 351 and side == "white") or \
           (msg_code != 352 and side == "black"):
            raise ProtocolError(
                msg_code,
                msg_text,
                "got wrong side",
            )

    def get_msg(self):
        while True:
            line = next(self.fsock_in)
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
        return (msg_code, msg_text)
    

    def closeall(self):
        self.fsock_out.close()
        self.fsock_in.close()
        self.sock.close()


    def get_time_controls(self, msg_text):
        words = msg_text.split()
        time_controls = [int(t) for t in words[:2]]
        if len(time_controls) > 0:
            self.white_time_control = time_controls[0]
        if len(time_controls) > 1:
            self.black_time_control = time_controls[1]
        else:    
            self.black_time_control = white_time_control


    def get_time(self, msg_text):
        words = msg_text.split()
        return int(words[0])


    def send(self, msg_text):
        print(
            msg_text,
            file=self.fsock_out,
            end="\r\n",
        )
        self.fsock_out.flush()

    def make_move(self, pos):
        if self.winner != None:
            raise MoveError(
                MoveError.DONE,
                "move with game over",
            )

        if self.who == "black":
            ellipses = ""
            self.serial += 1
        elif self.who == "white":
            ellipses = " ..."
        else:
            assert False

        self.send("{}{} {}".format(self.serial, ellipses, pos))

        msg_code, msg_text = self.get_msg()
        if msg_code == 201:
            self.winner = self.who
        elif msg_code == 202:
            self.winner = opponent(self.who)
        elif msg_code == 203:
            raise MoveError(
                MoveError.DISCO,
                "disconnected",
            )

        if self.winner != None:
            self.closeall()
            return False

        if msg_code != 200 and msg_code != 207:
            if msg_code == 291:
                raise MoveError(
                    MoveError.ILLEGAL,
                    "illegal move",
                )
            else:
                raise ProtocolError(
                    msg_code,
                    msg_text,
                    "unexpected move result code",
                )


        if msg_code == 207:
            self.my_time = self.get_time(msg_text)

        msg_code, msg_text = self.get_msg();
        if msg_code < 311 or msg_code > 318:
            raise ProtocolError(
                msg_code,
                msg_text,
                "unexpected move status code",
            )

        return True


    def get_move(self):
        if self.winner != None:
            raise MoveError(
                MoveError.DONE,
                "read move with game over",
            )

        msg_code, msg_text = self.get_msg()
        words = msg_text.split()

        if msg_code in {311, 321, 322, 325, 315}:
            side = "black"
            self.serial = int(words[0])
            pos = words[1]
        elif msg_code in {313, 317}:
            side = "black"
            self.serial = int(words[0])
            pos = words[1]
            self.opp_time = int(words[2])
        elif msg_code in {312, 323, 324, 326, 316}:
            side = "white"
            self.serial = int(words[0])
            pos = words[2]
        elif msg_code in {314, 318}:
            side = "white"
            self.serial = int(words[0])
            pos = words[2]
            self.opp_time = int(words[2])
        else:
            raise ProtocolError(
                msg_code,
                msg_text,
                "unknown move status code",
            )

        if side != opponent(self.who):
            raise ProtocolError(
                msg_code,
                msg_text,
                "move received from wrong side"
            )

        if self.who == "white":
            if msg_code in {311, 313, 315, 317}:
                return (True, pos)
            if msg_code in {321, 361}:
                self.winner = "black"
                return (False, pos)
            if msg_code in {322, 362}:
                self.winner = "white"
                return (False, pos)
            if msg_code == 325:
                raise MoveError(
                    MoveError.DISCO,
                    "game terminated early",
                )
            assert False
        elif self.who == "black":
            if msg_code in {312, 314, 316, 318}:
                return (True, pos)
            if msg_code in {323, 362}:
                self.winner = "white"
                return (False, pos)
            if msg_code in {324, 361}:
                self.winner = "black"
                return (False, pos)
            if msg_code == 326:
                raise MoveError(
                    MoveError.DISCO,
                    "game terminated early",
                )
            assert False
        else:
            assert False
