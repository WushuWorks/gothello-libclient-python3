import random

import gthclient

client = gthclient.GthClient("black", "localhost", 0)

def letter_range(letter):
    for i in range(5):
        yield chr(ord(letter) + i)

board = {letter + digit
         for letter in letter_range('a')
         for digit in letter_range('1')}

while True:
    move = random.choice(list(board))
    print("me:", move)
    try:
        client.make_move(move)
        board.remove(move)
    except gthclient.MoveError as e:
        if e.cause == e.ILLEGAL:
            print("me: made illegal move, passing")
            client.serial -= 1
            client.make_move("pass")

    cont, move = client.get_move()
    print("opp:", cont, move)
    if not cont:
        break
    if move == "pass":
        client.make_move("pass")
        break
    else:
        board.remove(move)
