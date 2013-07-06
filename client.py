#!/usr/bin/env python

# Copyright (C) 2013 Lachie Grant <https://github.com/lachgra>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import pygtk
pygtk.require('2.0')
import gtk

import sys
import socket
import thread
import time
import gobject
from utils import clientHelp

gobject.threads_init()

vers = "v1.14"
nick = "anonymous"
addr = '127.0.0.1'
port = 5001
buffer_size = 512

if len(sys.argv) > 1:
	if "--help" in sys.argv or "-h" in sys.argv:
		clientHelp()
		sys.exit()

	if "--version" in sys.argv or "-v" in sys.argv:
		print "Python Internet Relay Chat Client - pirc %s" % vers
		sys.exit()

	if "--nick" in sys.argv:	# specify a nickname
		i = sys.argv.index("--nick") + 1
		nick = sys.argv[i]

	if "-n" in sys.argv:
		i = sys.argv.index("-n") + 1
		nick = sys.argv[i]

	if "--server" in sys.argv: 	# specify a server address
		i = sys.argv.index("--server") + 1
		addr = sys.argv[i]

	if "-s" in sys.argv:	
		i = sys.argv.index("-s") + 1
		addr = sys.argv[i]

	if "--port" in sys.argv: 	# specify a port
		i = sys.argv.index("--port") + 1
		port = sys.argv[i]

	if "-p" in sys.argv:
		i = sys.argv.index("-p") + 1
		port = sys.argv[i]

	if "--opt" in sys.argv or "-o" in sys.argv: # set custom options (overwrites)
		print "Python Internet Relay Chat - pirc %s" % vers
		print "Setting custom options overwrites other arguments"
		nick = raw_input("Enter a nickname: ")
		addr = raw_input("Enter a server address: ")
		port = int(raw_input("Enter a port: "))
	
## Client class ##
class Client:
	"""Represents an independent client"""
	def __init__(self, addr, port, nick):
		self.addr = addr	# server address
		self.port = port	# server tcp/ip port
		self.nick = nick	# client nickname
		self.quit = False	# False when running

	def connect(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((self.addr, self.port))

	def main(self):
		self.socket.send(self.nick)  # send the nick
		thread.start_new_thread(self.listen, ())
		self.setupGui()

		gtk.main()
		self.disconnect()

	def disconnect(self):
		self.socket.send("/close")
		self.quit = True
		self.socket.close()
		
	def send(self, data):
		if data == "/close": # close
			self.disconnect()
			sys.exit("Exiting: /close")
		if data == "/help": # help
			pass
		self.socket.send(data)

	def listen(self):
		while self.quit == False:
			data = self.socket.recv(buffer_size)
			if data:
				ctime = time.strftime("%H:%M:%S", time.gmtime())
				position = self.txtBuffer.get_end_iter()
				gobject.idle_add(lambda:self.txtBuffer.insert(position, ctime + " | " + data + "\n"))
				#print data
				
	def btnClick(self, widget, args):
		if not args:
			raise ValueError

		if args == "cmdSend":
			if self.txtInput.get_text() != "":
				self.send(self.txtInput.get_text())
				self.txtInput.set_text("")

	def setupGui(self):
		# create a new window
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.resize(600, 400)

		# connects the exit button with gtk.main_quit
		self.window.connect("delete-event", gtk.main_quit) 

		# sets the window name
		self.window.set_title("Pirc Client")

		# sets the window border
		self.window.set_border_width(10)

		### define and add the vertical box
		self.vbox = gtk.VBox(False, 0)
		self.window.add(self.vbox) # all additions to this box will be added

		### add components to the vertical box
		self.sbox = gtk.HBox(False, 0)
		
		self.txtView = gtk.TextView()
		self.txtView.set_editable(False)

		# define the textbuffer
		self.txtBuffer = self.txtView.get_buffer()

		# define the label
		self.label = gtk.Label()
		self.label.set_text("  " + self.nick + ": ")

		self.winScroll = gtk.ScrolledWindow()
		self.winScroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		# add the textview to the scrolled window		
		self.winScroll.add(self.txtView)
		
		self.cmdSend = gtk.Button("Send") # send button
		self.txtInput = gtk.Entry() 	  # input line	

		# pack boxes
		self.vbox.pack_start(self.winScroll, True, True, 0)
		self.vbox.pack_start(self.sbox, True, True, 0)

		self.sbox.pack_start(self.cmdSend, False, False, 0)
		self.sbox.pack_start(self.label, False, False, 0)
		self.sbox.pack_start(self.txtInput, True, True, 0)
		

		"""
		Send_handler is the handler ID, used to disconnect or block the handler
		of the "clicked" signal, emitted by the cmdSend GtkWidget instance.
		This method call will still connect the button with the function
		cmdSendClicked()
		"""

		send_handler = self.cmdSend.connect("clicked", self.btnClick, "cmdSend")
		self.window.show_all()

if __name__ == "__main__":
	me = Client(addr, port, nick) # attempt to connect
	
	try:
		me.connect()
	except socket.error as e:
		sys.exit("Exiting: Socket " + repr(e) + ", try again.\n")

	try:
		me.main()
		me.disconnect()
	except socket.error as e:
		if e.errno == 9: # bad file descriptor
			sys.exit()
		if e.errno == 32: # broken pipe
			sys.exit("Exiting: Socket error + repr(e)")
		if e.errno == 111: # connection refused
			sys.exit("Exiting: Socket error + repr(e)")
	except KeyboardInterrupt:
		me.disconnect()
		sys.exit("Exiting: KeyboardInterrupt")

