#!/usr/bin/env python

# Copyright (C) 2014 Lachie Grant <https://github.com/lachgra>

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
pygtk.require("2.0")
import gtk

import sys
import socket
import threading
import os
import time
import gobject

gobject.threads_init()

vers = "v1.15"
window = True
logging = True
buff = 256
port = 6667

if len(sys.argv) > 2 and sys.argv[1] == "-s":
	screen_size = sys.argv[2].split('x')
	for i in range(2):
		screen_size[i] = int(screen_size[i])
	width, height = screen_size
	
else:
	width, height = gtk.gdk.screen_get_default().get_width(), gtk.gdk.screen_get_default().get_height()

def serverHelp():
	print "Usage: python server.py [ARGUMENTS]..."
	print "-h, --help		print help message"
	print "-v, --version		print the version"

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

		self.clients = []

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)		# creates an empty socket
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 	# makes port reusable
		self.sock.bind((self.addr, self.port))					# binds to the port
		self.sock.listen(1)							# listens for connections

		self.listener = threading.Thread(group=None, target=self.acceptClients, name=None, args=())	# starts the client accepting method
		self.listener.setDaemon(True)
		self.listener.start()

		if self.logging: 
			if not "log" in os.listdir(".") : os.mkdir("log")
			self.log_file = file("log/log.txt", 'a')
			self.banner()

		self.output("Listening on " + repr(self.sock.getsockname()), False)
		self.output("bfrsize %s, window %s, logging %s" % (str(buff), str(window), str(logging)), False)

		self.main()

	# the main thread
	def main(self):
		if window : gtk.main()
		self.exit()
		
	# accepts new clients and associated threads
	def acceptClients(self):
		while True:
			sock, addr = self.sock.accept()
		
			c = client(sock, addr)
			self.clients.append(c)
			
			self.output("New socket, %s, %s" % (c.addr[0], c.nick))				# log the new client addition
			listener = threading.Thread(None, target=self.listen, args=(c,))		# define thread
			listener.setDaemon(True)							# make thread a daemon
			listener.start()								# start listening

	# listen to and distribute replies
	def listen(self, sender):
		while True:
			message = sender.sock.recv(self.buffer_size)
			if message == "/close":
				sender.disconnect()
				self.output("Disconnected socket, %s, %s" % (sender.addr[0], sender.nick), True)
				self.clients.remove(sender)
				break
			if message == "/help":
				pass
			if message == "/msg":
				pass
			self.send(message, sender.nick)
	
	# reply distribution
	def send(self, message, nick, details=True):
		"""Sends data to specified clients (default: All)"""
		for c in self.clients:
			if details: 
				c.sock.send(nick + ": " + message)
			else:
				c.sock.send(message)

		self.output(nick + ": " + message)


	# executes commands
	def execute(self, command):
		if command == 'reboot':
			self.output("Restarting server...")
			for c in self.clients:
				c.disconnect()
			self.output("Server restarted")
			
		elif command == 'help':
			self.output("Commands are: shutdown, reboot, kick")
	
		else:
			self.output("Invalid command, type help for a list of commands.")

	# broadcast a message to the whole server
	def broadcast(self, message, to_window_log=True):
		self.send(message, "SERVER")
		self.output(message, to_window_log)

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

	# kick a player method
	def kick(self, client):
		"""Kicks a client, by passing a client instance as an argument."""
		self.output("Kicking client " + client.nick)
		self.send("Kicked client " + client.nick, "SERVER")
		self.disconnect(client)

	# print a pretty banner :-)
	def banner(self):
		if "banner.txt" in os.listdir(".") and not window:
			banner = file("banner.txt", 'r') 
			for i in banner.readlines():
				self.output(i)
			print "\n"
	
	# initializes the GUI
	def setupGui(self):
		"""Creates a new Gtk Window that can be used to control the server,
		containing an input line for both messaging and commands, and several
		controls."""

		"""The vbox is a verical box (the main box with a scrolled window
		The sbox is a horizontal box (the button and input box)"""

		# create a new window
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.resize(800, 600)
		# set window parameters
		self.window.set_title("Pirc Daemon")
		self.window.set_border_width(10)

		# connects the exit button to gtk.main_quit
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
		self.cmdExec = gtk.Button("Execute")
		self.cmdSend = gtk.Button("Send")
		self.cmdExit = gtk.Button("Exit")
		
		# pack vbox
		self.vbox.pack_start(self.winScroll, True, True, 0)
		self.vbox.pack_start(self.sbox, True, True, 0)

		# pack sbox (subset of vbox)	
		self.sbox.pack_start(self.txtInput, True, True, 0)
		self.sbox.pack_start(self.cmdExec, False, False, 0)
		self.sbox.pack_start(self.cmdSend, False, False, 0)
		self.sbox.pack_start(self.cmdExit, False, False, 0)

		"""Send_handler is the handler ID, used to disconnect or block the handler
		of the "clicked" signal, emitted by the cmdSend GtkWidget instance.
		This method call connected the button signal to the event handler (i.e. the method)"""

		# define handler IDs
		exec_handler_id = self.cmdExec.connect("clicked", self.btnClick, "cmdExec")
		send_handler_id = self.cmdSend.connect("clicked", self.btnClick, "cmdSend")
		exit_handler_id = self.cmdExit.connect("clicked", self.btnClick, "cmdExit")

		# show everything
		self.window.show_all()

	# a simple button event handler
	def btnClick(self, widget, args):
		"""Button handler for the GUI"""
		if not args:
			raise ValueError

		if args == "cmdExec":
			command = self.txtInput.get_text()
			if command != "":
				self.execute(command) #TODO
				self.output(command)
				self.txtInput.set_text("")

		if args == "cmdSend":
			message = self.txtInput.get_text()
			if message != "":
				self.send(message, "SERVER")
				self.txtInput.set_text("")
		
		if args == "cmdExit":
			if window: 
				gtk.main_quit() # close the window
			self.quit = True

	# an exit method
	def exit(self):
		self.broadcast("Goodbye!")
		for c in self.clients:
			c.disconnect()
		self.sock.close() 		# close main socket
		exit()	 			# finally exit the terminal


## client class ##
class client:
	"""Represents a client, used as an attribute of the server instance."""
	def __init__(self, sock, addr):
		self.sock = sock
		self.addr = addr
		self.nick = self.nickname()
		

	def nickname(self):
		while True:
			return self.sock.recv(20)

	def disconnect(self):
		self.sock.close()
		
## __main__ ##
if __name__ == "__main__":
	s = Server(window, logging, buff, port)
