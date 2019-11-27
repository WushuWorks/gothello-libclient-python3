# Gothello Daemon Python Client Library
Bart Massey

**This is not yet finished. You are looking at a prerelease
of code to be finished shortly.**

The Python client "library" for the Gothello daemon
[`gthd`](http://github.com/pdx-cs-ai/gothello-gthd) is a standard
Python 3 module.  You will want to
import `gthclient.py` into your Python program.

In brief, the client stubs are used by calling
`gthclient.start_game()` which automatically connects to the
specified server on the specified host as the specified
player.  (See the documentation on running a Gothello game
for details.)  The code then handles the details of making
moves and getting moves from the server, using the
`gthclient.make_move()` and `gthclient.get_move()` functions.  These accept
and return move strings: either a coordinate or "pass".

Time control tracking is performed by the client,
which caches a bunch of state information about the game
in progress in global variables.
