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
import pickle
import time
import os

clientmap = {}		# maps indexes to client instances
disconnected = []	# list of disconnected clients
threshold = 10		# maximum client number

port = 5001		# port to bind
addr = '127.0.0.1' 	# address to bind
vers = "v1.13"		# string of version
buffer_size = 1024 	# size of each packet
logging = True		# bool of logging

if len(sys.argv) > 1:
	if sys.argv[1] == "--help" or sys.argv[1] == "-h":
		print "Usage: python server.py [ARGUMENTS]..."
		print "-h, --help		prints help message"
		print "-v, --version		print the version"
		sys.exit()

	elif sys.argv[1] == "--version" or sys.argv[1] == "-v":
		print "Python Internet Relay Chat - pirc %s" % vers

	else:
		pass

if "banner.txt" in os.listdir("."):
	banner = file("banner.txt", 'r').readlines()

if logging:
	if not "log" in os.listdir("."):
		os.mkdir("log")
	log_file = file("log/log.txt", 'a')

class client:
	def __init__(self, index, sock, addr):
		self.index = index				# client index -> clientmap.keys()
		self.socket = sock				# client socket
		self.address = addr				# client address

		self.nick = self.getNickname()			# instantiates client nickname
		self.send("New client connected: %s" % self.nick, False)
		log("New socket, #" + repr(self.index) + ", " + repr(self.address[0]) + ", " + self.nick)

		thread.start_new_thread(self.listen, ())	
		"""
		Creates a new thread to listen to the
		client.socket itself. This allows the main
		thread to listen for new connections on the
		parent socket, and create new client instances
		using the return values of socket.accept() as 
		arguments for the client.__init__() method.
		"""

	def listen(self):
		"""
		Listens for new data on the socket attribute of 
		the client. If there is new data it will be printed.
		Handles all client commands.
		"""
		while True:
			message = self.socket.recv(buffer_size)
			if message == "/close":
				self.disconnect()
				return
			if message == "/help": # TODO
				pass
			if message == "/msg":
				pass
			log(repr(self.index) + ": " + self.nick + ": " + message)
			self.send(message)
	
	def send(self, message, details=True):
		"""Sends data to all clients currently connected"""
		for index in clientmap.keys():
			if index in disconnected:
				print "Skipping: index %d" % index
				continue
			client = clientmap[index]		
			if details:
				client.socket.send(self.nick + ": " + message)
			else:
				client.socket.send(message)

	def disconnect(self):
		print "Socket #%d closed: /close" % self.index
		self.socket.close()
		disconnected.append(self.index) # disconnected
		del clientmap[self.index]


	def getNickname(self):
		"""Returns the nickname of the client."""
		while True:
			data = self.socket.recv(buffer_size)
			if data:
				return data
	
## __main__ functions ##
def log(log_message):
	"""Logs everything to a file"""
	if logging:
		print log_message
		ctime = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime())
		log_file.write(ctime + ": " + log_message + "\n")

def do_banner():
	"""Prints a pretty banner"""
	if "banner" in globals():
		for i in banner:
			print i,
		print "\n"
	

## __main__ loop ##
if __name__ == "__main__":
	do_banner()

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 		# creates an empty socket
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 	# makes the socket port reuseable	

	s.bind((addr, port))						# binds the socket
	s.listen(1)							# enable the server to accept connections
	log("Listening on " + repr(s.getsockname()))

	while True:
		try:
			sock, addr = s.accept()				# wait for a new client
			index = len(clientmap) + len(disconnected) 	# the client index
			clientmap[index] = client(index, sock, addr)  	# create the client instance
		
		except KeyboardInterrupt:	
			sys.exit("Exiting: KeyboardInterrupt")

		except socket.error as e:
			if e.errorno == 32: # broken pipe
				sys.exit("Exiting: Broken pipe")
