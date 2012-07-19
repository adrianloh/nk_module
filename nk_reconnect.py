# ---------------------------------------------------------
# This module contains callback functions that bind to the
# major events of a script's lifecycle, namely when scripts
# are loaded, saved and rendered
# --------------------------------------------------------

import nuke, nukescripts
import os, re, hashlib
import threading

def checksumOfReadNode(threaded=True):
	readingNodes = [n for n in nuke._allNodes() if not n.hasError() and nuke.filename(n) is not None]
	task = nuke.ProgressTask("")
	task.setMessage("Checking external file dependencies")
	def run():
		for (i,node) in enumerate(readingNodes):
			if 'checksums' not in node.knobs().keys():
				tKnob = nuke.Text_Knob('checksums','checksums')
				tKnob.setVisible(False)
				node.addKnob(tKnob)
			(dirPath, basename, filename) = nuke.actualFilename(node)
			filepath = os.path.join(dirPath, filename)
			if os.path.exists(filepath):
				crc = hashlib.sha1(open(filepath).read(10485760)).hexdigest()
				node['checksums'].setValue(crc)
			task.setProgress(int(i*1./len(readingNodes)*100))
	if threaded: threading.Thread( None, run ).start()
	else: run()

nuke.addOnScriptLoad(checksumOfReadNode)
nuke.addOnScriptClose(checksumOfReadNode, args=(), kwargs={'threaded':False}, nodeClass='Root')

# ------------- Reconnect functions ---------------- #
# Callback functions used to reconnect all missing reads on
# scripLoad with the help of OS-dependent indexing services.
#

def reconnectMissing(indexCmd):
	# On Windows, use Everything (http://www.voidtools.com/).
	# Assumes "es.exe" command line program is in PATH. Note that
	# "es.exe" doesn't work with networked drives.
	# On OS X, use Spotlight.
	errors = [n for n in nuke._allNodes() if n.hasError() and nuke.filename(n) is not None]
	if errors:
		task = nuke.ProgressTask("Missing files!")
		task.setMessage("Reconnecting %i nodes" % len(errors))
		checkLog = False
		for (i,node) in enumerate(errors):
			(dirPath, basename, searchStr) = nuke.actualFilename(node)
			print "Reconnecting %s --> %s" % (node.name(), searchStr)
			results = [l.strip() for l in os.popen("""%s "%s" """ % (indexCmd,searchStr)).readlines()]
			def getNewPath(resultLine):
				(newPath, newBase) = os.path.split(resultLine)
				setPath = re.sub("\\\\","/",newPath) + "/" + basename
				return setPath
			if len(results)==1:
				node['file'].setValue(getNewPath(results[0]))
			elif len(results)>1:
				checkLog = True
				if 'checksums' in node.knobs().keys():
					crc = node['checksums'].value()
					checksums = [hashlib.sha1(open(f).read(10485760)).hexdigest() for f in results]
					if crc in checksums:
						res = results[checksums.index(crc)]
						node['file'].setValue(getNewPath(res))
					else:
						msg = "%s: CRC mismatch with found files" % node.name()
						print "-"*40 + "\n" + msg
						for (i,line) in enumerate(results): print "[%i] %s" % (i,line)
				else:
					node['file'].setValue(getNewPath(results[0]))
					msg = "More than 1 file found for %s:" % node.name()
					print "-"*40 + "\n" + msg
					for (i,line) in enumerate(results): print "[%i] %s" % (i,line)
			else:
				print "Reconnection failed. No files found."
			task.setProgress(int(i*1./len(errors)*100))
		if checkLog:
			msg = "More than 1 file was found for some nodes.\nCheck script editor."
			nuke.executeInMainThread( nuke.message, args=(msg) )
	else:
		pass

def reconnectMissing_Win(): reconnectMissing("es") # On Windows, "es.exe"
def reconnectMissing_OSX(): reconnectMissing("mdfind -name") # On OS X, "mdfind"
def reconnectMissing_Pass(): pass # TODO: On Linux, ignore?

reconnectFunctions = (reconnectMissing_Win, reconnectMissing_OSX, reconnectMissing_Pass)
platform = [nuke.env['WIN32'], nuke.env['MACOS'], nuke.env['LINUX']].index(True)

def reconnectWithTimeout(): #TODO: Implement a timeout
	func = reconnectFunctions[platform]
	threading.Thread( None, func ).start()

nuke.addOnScriptLoad(reconnectWithTimeout)




