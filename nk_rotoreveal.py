import nuke
from random import randint
import threading
import time

def addColorPickerToViewer():
	n = nuke.thisNode()
	if "color" not in n.knobs().keys():
		k = nuke.Color_Knob("color")
		n.addKnob(k)

nuke.addOnCreate(addColorPickerToViewer,(),{},"Viewer")

def addRotoConstant():
	n = nuke.thisNode()
	n['output'].setValue("rgba")
	constant = nuke.randomColorConstant()
	n.setInput(2, constant)
	last_position = None
	if nuke.selectedNodes():
		sNode = nuke.selectedNodes()[0]
		n.setInput(0,sNode)
		last_position = (sNode.xpos(), sNode.ypos())
	def afterCreate():
		time.sleep(0.05)
		if last_position: n.setXYpos(last_position[0], last_position[1]+80)
		constant.setXYpos(n.xpos()-132,n.ypos())
		n.setInput(3,None)
	threading.Thread( None, afterCreate ).start()

nuke.addOnUserCreate(addRotoConstant, (), {}, "RotoPaint")

def nk_get_roto_from_color():
	"""
	Reveal Roto
	SS Shift+v
	"""
	def colorSum(node):
		color = node['color'].value()
		if isinstance(color,list):
			return sum([int(i*10000) for i in color][0:3])
		else:
			return color
	viewPortSum = colorSum(nuke.activeViewer().node())
	lower,upper = viewPortSum-10,viewPortSum+10
	c = [C.dependent() for C in nuke.allNodes("Constant") if (lower<=colorSum(C)<=upper)]
	cccc = []
	for cc in c:
		for ccc in cc:
			if ccc.Class()=="RotoPaint": cccc.append(ccc)
	[(p.setSelected(True),p.showControlPanel()) for p in cccc]
