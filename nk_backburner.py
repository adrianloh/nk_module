import nuke
import os
from subprocess import Popen
import threading
import shutil

def nk_backburner():
	"""
	Background render
	Note: this assumes that the nuke executable is in PATH
	"""
	nuke.scriptSave()
	op = nuke.root()['name'].value()
	name = nuke.selectedNode().name()
	np = op+"_%s.bburn"%name
	shutil.copy2(op,np)
	ranges = "%s-%s" % (nuke.root().firstFrame(),nuke.root().lastFrame())
	cmd = """ "%s" -m %i -F %s -X %s -ix %s""" % (nuke.EXE_PATH, int(nuke.env['numCPUs']/2), ranges, name, np)
	print cmd

	def render():
		print "Background rendering %s" % name
		try:
			Popen(cmd).wait()
		except WindowsError: # TODO: WTF is up with this?
			os.popen(cmd).read()
		nuke.message("%s Background render finished!" % name)
		nuke.executeInMainThread(nuke.toNode(name)['reading'].setValue,True)
		os.remove(np)

	def changeNodeColor(thisName):
		if nuke.thisNode().name() == thisName:
			nuke.executeInMainThread(nuke.toNode(thisName)['tile_color'].setValue,552079871)
			nuke.executeInMainThread(nuke.toNode(thisName)['postage_stamp'].setValue,True)
			nuke.removeKnobChanged(changeNodeColor,thisName,{},"Write")

	this = nuke.toNode(name)
	this['tile_color'].setValue(943405567)
	this['postage_stamp'].setValue(False)
	this['reading'].setValue(False)

	nuke.addKnobChanged(changeNodeColor,name,{},"Write")

	T = threading.Thread(target=render)
	T.start()