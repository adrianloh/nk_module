import nuke
import select
import sys
import pybonjour
import socket
import threading

name    = socket.gethostname()
regtype = "_nuke._tcp"
port    = 6980

def register_callback(sdRef, flags, errorCode, name, regtype, domain):
	if errorCode == pybonjour.kDNSServiceErr_NoError:
		print 'Registered service:'
		print '  name    =', name
		print '  regtype =', regtype
		print '  domain  =', domain


sdRef = pybonjour.DNSServiceRegister(name = name,
									 regtype = regtype,
									 port = port,
									 callBack = register_callback)

def advertise():
	try:
		try:
			while True:
				ready = select.select([sdRef], [], [])
				if sdRef in ready[0]:
					pybonjour.DNSServiceProcessResult(sdRef)
		except KeyboardInterrupt:
			pass
	finally:
		sdRef.close()

threading.Thread( None, advertise ).start()


from base64 import urlsafe_b64decode as decode
from bottle import route, run

@route('/')
@route('/cmd/:cmdString')
def index(cmdString="world"):
	cmd = "Cannot decode command.\n"
	try:
		cmd = decode(cmdString)
		def c():
			print cmd
			eval(cmd)
		nuke.executeInMainThread(c)
	except:
		pass
	return cmd

threading.Thread(target=run, kwargs={"host":name+".local","port":6980} ).start()