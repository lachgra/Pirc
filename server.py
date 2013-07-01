#!/usr/bin/env python

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import sys
import socket
import thread
import time
import os

vers = "v1.14"
window = False

if len(sys.argv) > 1:
	if "--help" in sys.argv or "-h" in sys.argv:
		print "Usage: python server.py [ARGUMENTS]..."
		print "-h, --help		prints help message"
		print "-v, --version		print the version"
		sys.exit()

	if "--version" in sys.argv or "-v" in sys.argv:
		print "Python Internet Relay Chat - pirc %s" % vers
		sys.exit()

	if "--no-window" in sys.argv or "-nw" in sys.argv:
		window = False

## server class ##
class server:
	def __init__(self, window):
		self.addr = "127.0.0.1"
		self.port = 5001
		self.buffer_size = 1024
		self.logging = False
		self.window = window

		self.clientmap = {}
		self.disconnected = []
		self.threshold = 10

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)		# creates an empty socket
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 	# makes port reusable
		self.sock.bind((self.addr, self.port))					# binds to the port
		self.sock.listen(1)							# listens for connections
		self.banner()

		if self.logging:
			if not "log" in os.listdir("."):
				os.mkdir("log")
			self.log_file = file("log/log.txt", 'a')
			self.log("Listening on " + repr(self.sock.getsockname()))
			print "\n"

		while True:
			try:
				sock, addr = self.sock.accept()						# accepts a new client
				index = len(self.clientmap) + len(self.disconnected) 			# the client index
				c = client(index, sock, addr)							# the client instance
				self.clientmap[index] = c						# add the client to clientmap
				thread.start_new_thread(self.listen, (c,))				# listens on the client socket
			except KeyboardInterrupt:	
				sys.exit("Exiting: KeyboardInterrupt")

			except socket.error as e:
				if e.errorno == 32: # broken pipe
					sys.exit("Exiting: Broken pipe")

	def listen(self, sender):
		self.log("New socket, #%s, %s, %s" % (repr(sender.index), sender.addr[0], sender.nick))
		while True:
			message = sender.sock.recv(self.buffer_size)
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
			self.log(repr(sender.index) + ": " + sender.nick + ": " + message)
			self.send(message, sender.nick)

	def send(self, message, nick, details=True):
		"""Sends data to specified clients (default: All)"""
		for index in self.clientmap:
			receiver = self.clientmap[index]		
			if details:
				receiver.sock.send(receiver.nick + ": " + message)
			else:
				receiver.sock.send(message)

	def disconnect(self, client):
		self.log("Disconnected socket, #%s, %s, %s" % (repr(client.index), client.addr[0], client.nick))
		del self.clientmap[client.index]	# delete the client instance

	def log(self, log_message):
		"""Logs everything to a file"""
		if self.logging:
			print log_message
			ctime = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime())
			self.log_file.write(ctime + ": " + log_message + "\n")

	def banner(self):
		"""Prints a pretty banner"""
		if "banner.txt" in os.listdir(".") and not window:
			banner = file("banner.txt", 'r') 
			for i in banner.readlines():
				print i,
			print "\n"
			if not self.logging:
				print "Listening on " + repr(self.sock.getsockname()) + "\n"

## client class ##
class client:
	def __init__(self, index, sock, addr):
		self.index = index
		self.sock = sock
		self.addr = addr
		self.nick = self.nickname()

	def nickname(self):
		while True:
			return self.sock.recv(20)
			


## __main__ loop ##
if __name__ == "__main__":
	s = server(window)

