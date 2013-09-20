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

#TODO, change the size of the buttons

import pygtk
pygtk.require("2.0")
import gtk

import sys
import socket
import thread
import time
import os
import gobject
from utils import serverHelp

gobject.threads_init()


vers = "v1.15"
window = True
logging = True
buff = 256
port = 6667


if len(sys.argv) > 1:
	if "--help" in sys.argv or "-h" in sys.argv:
		serverHelp()
		sys.exit()

	if "--version" in sys.argv or "-v" in sys.argv:
		print "Python Internet Relay Chat Server - pirc %s" % vers
		sys.exit()
	
	if "--no-window" in sys.argv or "-nw" in sys.argv:
		window = False

	if "--no-logging" in sys.argv or "-nl" in sys.argv:
		logging = False

	if "--buffer-size" in sys.argv:
		index = sys.argv.index("--buffer-size")
		buff = int(sys.argv[index+1])	

	if "-bs" in sys.argv:
		index = sys.argv.index("-bs")
		buff = int(sys.argv[index+1])

	if "--port" in sys.argv:
		index = sys.argv.index("--port")
		port = int(sys.argv[index+1])
		
	if "-p" in sys.argv:
		index = sys.argv.index("-p")
		port = int(sys.argv[index+1])

	assert type(port) is int
	assert type(buff) is int
	

## Server class ##
class Server:
	def __init__(self, window, logging, buff, port):
		self.addr = "127.0.0.1"
		self.port = port
		self.buffer_size = buff
		self.logging = logging
		self.quit = False
		self.window = window
		if window : self.setupGui()

		self.clientmap = {}
		self.disconnected = 0
		self.threshold = 10

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)		# creates an empty socket
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 	# makes port reusable
		self.sock.bind((self.addr, self.port))					# binds to the port
		self.sock.listen(1)							# listens for connections

		thread.start_new_thread(self.clients, ())				# starts the client adding method

		if self.logging: 
			if not "log" in os.listdir(".") : os.mkdir("log")
			self.log_file = file("log/log.txt", 'a')
			self.banner()

		self.output("Listening on " + repr(self.sock.getsockname()), False)
		self.output("bfrsize %s, window %s, logging %s" % (str(buff), str(window), str(logging)), False)

		thread.start_new_thread(self.main(), ())

	def main(self):
		if window : gtk.main()
		while not self.quit:
			pass
		self.shutdown()
		

	# accepts new clients as they send requests, and then creates threads to listen on that socket
	def clients(self):
		while not self.quit:
			try:
				sock, addr = self.sock.accept()							# accepts a new client
				index = len(self.clientmap) + self.disconnected					# the client index
				c = client(index, sock, addr)							# the client instance
				self.clientmap[index] = c							# add the client to clientmap
				self.output("New socket, #%s, %s, %s" % (repr(c.index), c.addr[0], c.nick))	# log the new client addition
				thread.start_new_thread(self.listen, (c,))					# listens on the client socket

			except KeyboardInterrupt:	
				sys.exit("Exiting: KeyboardInterrupt")

			except socket.error as e:
				if e.errorno == 32: # broken pipe
					sys.exit("Exiting: Broken pipe")

	# listen to and distribute replies as they are received
	def listen(self, sender):
		while not self.quit:
			message = sender.sock.recv(self.buffer_size)
			if not sender.connected: # to prevent the very last message from getting through
				break
			if message == "/close":
				self.disconnect(sender)
				return
			if message == "/exit":
				self.disconnect(sender)
				return
			if message == "/help":
				pass
			if message == "/msg":
				pass
			#self.output(repr(sender.index) + ": " + sender.nick + ": " + message)
			self.send(message, sender.nick)
	
	# reply distribution
	def send(self, message, nick, details=True):
		"""Sends data to specified clients (default: All)"""
		for index in self.clientmap:
			receiver = self.clientmap[index]		
			if details:
				receiver.sock.send(nick + ": " + message)
			else:
				receiver.sock.send(message)

		self.output(nick + ": " + message)

	# disconnect a socket
	def disconnect(self, client):
		self.output("Disconnected socket, #%s, %s, %s" % (repr(client.index), client.addr[0], client.nick), False) # not logged to window
		self.disconnected += 1
		self.clientmap[client.index].disconnect()
		del self.clientmap[client.index]


	# server-wide automated logger
	def output(self, log_message, to_window_log=True):
		"""Outputs anything relevant in accordance with the server settings"""
		if self.logging:	
			ctime = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime())
			self.log_file.write(ctime + ": " + log_message + "\n")

		if self.window and to_window_log:
			position = self.txtBuffer.get_end_iter()
			gobject.idle_add(lambda:self.txtBuffer.insert(position, ctime + " | " + log_message + "\n"))
		else:
			print log_message

	# executes commands
	def execute(self, command):
		if command == 'reboot':
			self.output("Restarting server...")

		elif command.startswith("kick"):
			index = int(command.strip()[4:])
			for c in self.clientmap.keys():
				if c == index:
					client = self.clientmap[c]
					self.send("%s has been kicked from the server." %client.nick, "SERVER")
					self.disconnect(client)
		elif command == 'help':
			self.output("Commands are: shutdown, reboot, kick")
	
		else:
			self.output("Invalid command, type help for a list of commands.")

	def banner(self):
		"""Prints a pretty banner"""
		if "banner.txt" in os.listdir(".") and not window:
			banner = file("banner.txt", 'r') 
			for i in banner.readlines():
				self.output(i)
			print "\n"
	
	# sets up the window
	def setupGui(self):
		"""
		The vbox is a verical box (the main box with a scrolled window
		The sbox is a horizontal box (the button and input box)
		"""

		# create a new window
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.resize(600, 600)
		# set window parameters
		self.window.set_title("Pirc Daemon")
		self.window.set_border_width(10)

		# connects the exit button with gtk.main_quit
		self.window.connect("delete-event", gtk.main_quit)

		# define and add the vertical box
		self.vbox = gtk.VBox(False, 0)
		self.window.add(self.vbox)
	
		# create the button and input box
		self.sbox = gtk.HBox(False, 0)
	
		# create the log viewer
		self.logView = gtk.TextView()
		self.logView.set_editable(False)
		
		# define the textbuffer
		self.txtBuffer = self.logView.get_buffer()

		# define the scrolled window
		self.winScroll = gtk.ScrolledWindow()
		self.winScroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

		# add the textview to the scrolled window		
		self.winScroll.add(self.logView)

		# define the command text box
		self.txtInput = gtk.Entry()
		self.cmdExecute = gtk.Button("Execute")
		self.cmdSend = gtk.Button("Send")
		
		# pack vbox
		self.vbox.pack_start(self.winScroll, True, True, 0)
		self.vbox.pack_start(self.sbox, True, True, 0)

		# pack sbox (subset of vbox)	
		self.sbox.pack_start(self.txtInput, True, True, 0)
		self.sbox.pack_start(self.cmdExecute, False, False, 0)
		self.sbox.pack_start(self.cmdSend, False, False, 0)

		"""
		Send_handler is the handler ID, used to disconnect or block the handler
		of the "clicked" signal, emitted by the cmdSend GtkWidget instance.
		This method call connected the button signal to the event handler (i.e. the method)
		"""

		execute_handler_id = self.cmdExecute.connect("clicked", self.btnClick, "cmdExecute")
		send_handler_id = self.cmdSend.connect("clicked", self.btnClick, "cmdSend")
		self.window.show_all()

	def btnClick(self, widget, args):
		if not args:
			raise ValueError

		if args == "cmdExecute":
			command = self.txtInput.get_text()
			if command != "":
				self.execute(command)
				self.txtInput.set_text("")

		if args == "cmdSend":
			message = self.txtInput.get_text()
			if message != "":
				self.send(message, "SERVER")
				self.txtInput.set_text("")
				#self.output("SERVER" + ": " + message)

	def shutdown(self):
		self.quit = True
		self.sock.close()
		print "Goodbye!"
		sys.exit()


## client class ##
class client:
	"""Represents a client as an attribute of the server"""
	def __init__(self, index, sock, addr):
		self.index = index
		self.sock = sock
		self.addr = addr
		self.nick = self.nickname()
		self.connected = True

	def nickname(self):
		while True:
			return self.sock.recv(20)

	def disconnect(self):
		self.sock.close()
		self.connected = False
			


## __main__ ##
if __name__ == "__main__":
	s = Server(window, logging, buff, port)

