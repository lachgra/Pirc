PIRC is an Internet Relay Chat system written in Python, licensed under the GNU GPLv3.

server.py -- runs the IRC daemon, GUI client

client.py -- runs the GUI client

The server maps client instances to addresses, sockets and nicknames, and relays the messages between the clients, prefacing each message with the sender nickname.

The client receives messages from the server and displays them on a gtk.TextView(). This allows users to send data to the server.

Both are written in pure Python, importing exclusively from the python standard library and PyGTK.

Usage:

python server.py [--help][--version]

python client.py [--help][--version][--nick nickname]

To do:
Add encryption
Resize the buttons

Feel free to contact me on any queries you may have. :-)

E-mail: lachie.j.g@live.com


