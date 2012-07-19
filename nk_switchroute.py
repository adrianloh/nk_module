# -----------------------------------------------------------
# This module enables Write nodes to render different "routes"
# of the DAG by altering existing Switch nodes before each 
# Write node is executed
# -----------------------------------------------------------

import nuke
import nukescripts
import re

def setSwitchRoute():
	"""
	Hook into addBeforeRender of Write nodes. Sets the "state" of 
	Swicthes across the DAG before rendering.
	"""
	try:
		route = nuke.thisNode()['switchroute'].value()
		nodename = nuke.thisNode().name()
		if route:
			ss = route.split(" ")
			for s in zip(ss[0::2],ss[1::2]):
				switchname = s[0]
				which = int(s[1])
				print "%s | %s -> %i" % (nodename, switchname, which)
				if nuke.exists(switchname):
					nuke.toNode(switchname)['which'].setValue(which)
				else:
					print "%s switch does not exists!" % name
	except NameError:
		pass

def getSwitchRoute():
	""" 
	Get the current "state" of all Switches in the DAG.
	"""
	switches = [(n.name(),int(n['which'].value())) for n in nuke.allNodes("Switch")]
	if not switches:
		nuke.message("There are no Switches in this comp!")
		return
	state = " ".join([n[0]+" "+str(n[1]) for n in switches])
	nuke.thisNode()['switchroute'].setValue(state)
	b4render = nuke.thisNode()['beforeRender'].value()
	if b4render:
		if re.search("setSwitchRoute",b4render):
			pass
		else:
			b4render = b4render + "; nuke.setSwitchRoute()"
	else:
		b4render = "nuke.setSwitchRoute()"
	nuke.thisNode()['beforeRender'].setValue(b4render)

def attach_switchRoute(*args):
	n = nuke.thisNode()
	if 'switchroute' not in n.knobs().keys():
		n.addKnob(nuke.String_Knob("switchroute","switchroute"))
		n.addKnob(nuke.PyScript_Knob("pyKnob_switchroute"," Get current route ", "nuke.getSwitchRoute()"))
	return n

nukescriptsOriginalExecutePanel = nukescripts.execute_panel

def custom_execute_panel(_list, exceptOnError = True):
	"""
	Override the default way Nuke executes multiple Write nodes to allow
	each Write node's addBeforeRender and addBeforeFrameRender to execute
	code *specific to that node* before they are rendered.
	"""
	_list = nuke.allNodes("Write") if _list[0]	== nuke.root() else _list
	_list = [n for n in _list if not (n['disable'].value() or n['reading'].value())]
	if len(_list) == 0:
		nuke.message("No renderable Write nodes!")
		return
	else:
		_list = sorted(_list,key=lambda x: x['render_order'].value())
		nuke.scriptSave("")
		for n in _list:
			if n['use_limit'].value():
				first,last = n['first'].value(),n['last'].value()
			else:
				first,last = nuke.root().firstFrame(),nuke.root().lastFrame()
			print "Render started: %s" % n.name()
			nuke.execute(n.name(),int(first),int(last))
			print "Render completed: %s" % n.name()

nukescripts.execute_panel = custom_execute_panel
nuke.addOnUserCreate(attach_switchRoute,(),{},"Write")
nuke.getSwitchRoute = getSwitchRoute
nuke.setSwitchRoute = setSwitchRoute














