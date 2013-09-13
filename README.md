PIRC is an Internet Relay Chat system written in Python, licensed under the GNU GPLv3.

server.py -- runs the server (IRC daemon)

client.py -- runs the GUI client

The server maps client instances to addresses, sockets and nicknames, and relays the messages between the clients, prefacing each message with the sender nickname.

The client (written with pyGTK) receives messages from the server and displays them on a gtk.TextView(). This allows users to send data to the server.

Usage:

python server.py [--help][--version]

python client.py [--help][--version][--opt][--nick nickname]

To do:
Add encryption
Add a GTK interface for the server

Feel free to contact me on any queries you may have. :-)

E-mail: lachie.j.g@live.com


