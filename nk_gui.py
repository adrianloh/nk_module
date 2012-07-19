# -----------------------------------------------------
# This module contains functions that extend the GUI
# workings of Nuke on a non-node-specific basis.
# -----------------------------------------------------

import nuke
import nukescripts
import os
from random import randint
import re
from subprocess import Popen,PIPE
import threading
from uuid import uuid4

def hexColor(rgb):
	r,g,b = rgb
	return int('%02x%02x%02x%02x' % (r*255,g*255,b*255,1),16)

nuke.hexColor = hexColor

def randomColor(hex=False):
	color = [float("0."+str(randint(0,10000))) for i in range(3)]
	return hex and hexColor(color) or color

nuke.randomColor = randomColor

def randomColorConstant():
	color = nuke.randomColor()
	constant = nuke.nodes.Constant(channels="rgba", postage_stamp=False, tile_color=nuke.hexColor(color))
	constant['color'].setValue(color+[1.0])
	return constant

nuke.randomColorConstant = randomColorConstant

def nk_break_fbx():
	"""
	Break FBX
	"""
	n = nuke.selectedNode()
	if n.knobs().has_key("fbx_node_name"):
		source = n.dependencies()[0] if n.dependencies() else None
		_scale = " ".join(["%0f" % i for i in n['scaling'].value()])
		_file = n['file'].value()
		enum_string = n["fbx_node_name"].value().split(" ")
		nodes = enum_string[1:]
		if nuke.ask("Create %i nodes?" % len(nodes)):
			for (i,node_name) in enumerate(nodes):
				enum_string[0] = "{%i}" % i
				v = " ".join(enum_string)
				g = nuke.nodes.ReadGeo2(file=_file, fbx_node_name=v, read_from_file=False, scaling=_scale)
				g.setInput(0, randomColorConstant())
	
def nk_virtual_axis():
	"""
	Virtual Axis
	"""
	control = nuke.nodes.Axis()
	deltas = {}

	def add(a,b):
		return [v+b[i] for (i,v) in enumerate(a)] if type(a)==list else a+b
			
	def diff(new,old):
		return [v-old[i] for (i,v) in enumerate(new)] if type(new)==list else new-old

	def callback():
		k = nuke.thisKnob()
		name, v = k.name(), k.value()
		if not deltas.has_key(name):
			deltas[name] = v
			d = deltas[name]
		else:
			d = diff(v,deltas[name])
			deltas[name] = v
		[n[name].setValue(add(n[name].value(),d)) for n in nuke._allNodes() if n['selected'].value() and n!=control and n.knobs().has_key(name)]

	nuke.addKnobChanged(callback, args=(), kwargs={}, node=control)

def nk_open_dependents():
	"""
	Open all dependents
	"""
	def gen(x):
		while True:
			x+=1
			yield "_%i" % x

	suffix = gen(0)

	p = nuke.Panel('Open dependents')
	if not len(nuke._selectedNodes()):
		nuke.message("No nodes selected.")
	else:
		root = nuke._selectedNodes()[0]
		crawl = [root]
		node_options = {}
		while len(crawl)>0:
			this = crawl.pop()
			name = this.name()
			if node_options.has_key(name): name+=suffix.next()
			node_options[name] = this
			[crawl.append(n) for n in this.dependencies() if n.Class() not in ["Dot"]]
		node_options_keys = sorted(node_options.keys())
		p.addEnumerationPulldown('dependencies', " ".join(node_options_keys))
		p.show()
		target = p.value('dependencies')
		if target: node_options[target].showControlPanel()

def nk_read_nodes():
	"""
	Read nodes from file
	"""
	f = nuke.getFilename("Select nuke script to source nodes")
	nuke.scriptReadFile(f)
	
def nk_read_shotgun():
	"""
	Read from Shotgun
	"""
	nuke.readInFromShotgun()
	
def nk_new_scene(nodes=None):
	""" 
	New scene
	SS Ctrl+Alt+s
	Creates a new 3D scene with renderer and a camera attached. If invoked with 
	any other node selected *and a scene node*, they are fed into the scene node.
	"""
	if not nodes:
		nodes = nuke.selectedNodes()
	if nodes != [] and nodes[-1].Class() == "Scene":
		scene = nodes[-1]
		inputs = nodes[0:-1]
	else:
		scene = nuke.nodes.Scene()
		existing_camera = [n for n in nodes if n.Class()=="Camera2"]
		camera = existing_camera[0] if existing_camera else nuke.nodes.Camera2()
		camera['translate'].setValue([0,0,1])
		render = nuke.nodes.ScanlineRender()
		scene.setInput(scene.inputs(),camera)
		render.setInput(2,camera)
		render.setInput(1,scene)
		inputs = nodes
	for input in inputs:
		connected = scene.setInput(scene.inputs(),input)
		if not connected:
			card = nuke.nodes.Card()
			card.setInput(0,input)
			scene.setInput(scene.inputs(),card)
	return scene

def nk_autoBackdrop():
	"""
	Autobackdrop
	"""
	import operator, random
	selNodes = nuke.selectedNodes()
	if not selNodes:
		return nuke.nodes.BackdropNode()
	positions = [(i.xpos(), i.ypos()) for i in selNodes]
	xPos = sorted(positions, key = operator.itemgetter(0))
	yPos = sorted(positions, key = operator.itemgetter(1))
	xMinMaxPos = (xPos[0][0], xPos[-1:][0][0])
	yMinMaxPos = (yPos[0][1], yPos[-1:][0][1])
	n = nuke.nodes.BackdropNode(xpos = xMinMaxPos[0]-10,
				    bdwidth = xMinMaxPos[1]-xMinMaxPos[0]+110,
				    ypos = yMinMaxPos[0]-85,
				    bdheight = yMinMaxPos[1]-yMinMaxPos[0]+160,
				    tile_color = randomColor(True),
				    note_font_size = 42)
	n['selected'].setValue(False)
	# revert to previous selection
	[i['selected'].setValue(True) for i in selNodes]
	return n
	
def nk_connect_to_switches():
	"""
	Connect to Switches
	Connect all selected nodes into all selected Switches
	"""
	sel = nuke.selectedNodes()
	switches = [n for n in sel if n.Class() == "Switch"]
	others = [n for n in sel if n not in switches]
	[s.setInput(s.inputs(),n) for s in switches for n in others]

def nk_kiss():
	"""
	Kiss
	SS Alt+a
	Mimics IFFFS-style kissing on nodes. Select the parent node,
	then subsequently the children to be parented.
	"""
	sel = nuke.selectedNodes()
	parent = sel[0]
	children = sel[1:]
	[n.setInput(n.inputs(),parent) for n in children]

def nk_gangbang():
	"""
	Gangbang
	SS Alt+Shift+a
	Plug all selected nodes into the last selected node
	"""
	sel = nuke.selectedNodes()
	slut = sel[-1]
	bangers = sel[:-1]
	[slut.setInput(slut.inputs(),b) for b in bangers]

def nk_rv(nodes=None):
	"""
	Send to RV
	SS Shift+r
	"""
	f_image = lambda node: os.path.join(nuke.actualFilename(n)[0],nuke.actualFilename(n)[-1])
	
	path = {}
	path['Write'] = f_image
	path['Read'] = f_image
	path['Precomp'] = lambda node: nuke.filename(node)
	
	inbox_rv = []
	inbox_nuke = []
	
	send_to = {}
	send_to['Read'] = inbox_rv
	send_to['Write'] = inbox_rv
	send_to['Precomp'] = inbox_nuke
	
	n = [send_to[n.Class()].append(path[n.Class()](n)) for n in nuke.selectedNodes() if n.Class() in path.keys()]

	[Popen("""nuke --nukex %s""" % p, stdout=PIPE, shell=True) for p in inbox_nuke]
	
	rv_cmd = {}
	rv_cmd[0] = lambda n: None
	rv_cmd[1] = lambda n: """%s -fullscreen "%s" """ % (os.environ['RVPATH'], n[0])
	rv_cmd[2] = lambda n: """%s -fullscreen -sessionType stack %s """ % ( os.environ['RVPATH']," ".join(n) )

	cmd = rv_cmd.get(len(inbox_rv), rv_cmd[2])(inbox_rv)
	if cmd: Popen(cmd, stdout=PIPE, shell=True)

def nk_batchChangeSelected():
	"""
	Batch change
	"""
	input = nuke.getInput("""Eg. translate=[0,1,3] / rotate=90.0 / label="some text" """)
	try:
		param,value = input.split("=")
		[n[param].setValue(eval(value)) for n in nuke.selectedNodes()]
	except Exception: pass

def nk_color_tiles(src=False):
	"""
	Color nodes with swatch
	"""
	nodes = nuke.selectedNodes()
	color = nodes[0]['tile_color'].value() if src else nuke.getColor()
	dst = nodes[1:]	if src else nodes
	[n['tile_color'].setValue(color) for n in dst]

def nk_color_others():
	"""
	Color others with first selected node
	"""
	nk_color_tiles(True)

def nk_backburner():
	"""
	Background render
	Note: this assumes that the nuke executable is in PATH
	"""
	from nk_backburner import nk_backburner
	nk_backburner()

def nk_comp_multipass_exr():
	"""
	Comp multipass EXR
	"""
	mergeLUT = dict(DIFFNS="plus", SPECNS="plus", INDIRR="plus", REFL="plus", SHD="difference")
	bases = ["DIFFNS"]
	read = nuke.selectedNode()
	if read.Class()=="Read":
		remove = nuke.nodes.Remove(channels="alpha")
		remove.setInput(0,read)
		known_passes = [name for name in nuke.layers(read) if name.split("_")[0] in mergeLUT.keys()]
		# Shuffle each pass into RGB:
		shuffles = [nuke.nodes.Shuffle(out='rgb', label="[knob in]") for _pass in known_passes]
		[shuffle['in'].setValue(name) for (shuffle,name) in zip(shuffles,known_passes)]
		[shuffle.setInput(0,remove) for shuffle in shuffles]
		base_nodes, layers = [], []
		[base_nodes.append(shuffle) if name.split("_")[0] in bases else layers.append((name,shuffle))
		 for (shuffle,name) in zip(shuffles,known_passes)]
		last_merge = None
		for base in base_nodes:
			last_merge = base
			for (name, output) in layers:
				operation = mergeLUT[name.split("_")[0]]
				merge = nuke.nodes.Merge(output='rgb', operation=operation)
				merge.setInput(0,output)
				merge.setInput(1,last_merge)
				last_merge = merge
		copy = nuke.nodes.Copy(from0="alpha", to0="alpha")
		copy.setInput(1,read)
		copy.setInput(0,last_merge)

def nk_reveal_in_finder():
	"""
	Reveal in Finder
	SS Ctrl+r
	If selected node reads/writes to/from a file, open it in Explorer/Finder
	"""
	def reveal_in_finder(path):
		"""
		Given a path to a file, opens the containing/parent folder
		ala OS X's "Reveal in Finder"
		"""
		__open__ = [lambda p:os.startfile(p,'open'), lambda p:os.popen("""open "%s" """ % p), lambda p:Popen("""nautilus '%s' """ % p, shell=True)]
		platform = [nuke.env['WIN32'], nuke.env['MACOS'], nuke.env['LINUX']].index(True)
		parent = os.path.split(path)[0]
		if os.path.exists(parent):
			f = __open__[platform]
			f(parent)
		else:
			nuke.message("Cannot find path:\n%s" % parent)
	nodes = nuke.selectedNodes()
	[reveal_in_finder(path) for path in [nuke.filename(node) for node in nodes] if path]

def nk_hide_open_panels():
	"""
	Close open panels
	SS Ctrl+h
	"""
	[n.hideControlPanel() for n in nuke._allNodes() if n.shown()]

def knobChange():
	print nuke.thisKnob().name()

#nuke.addKnobChanged(knobChange)

# ------ Import NK functions from other modules into current namespace ------ #

#from nk_rotoreveal import nk_get_roto_from_color
from nk_threadrender import nk_multithreadedRender
from nk_panelreopen import nk_reopen_panels

if nuke.env['gui']:

	# --- Return list of nodes in the order they were selected --- #

	nukeOriginalSelectedNodes = nuke.selectedNodes
	reverseSelected = lambda: nukeOriginalSelectedNodes()[::-1]
	nuke.selectedNodes = reverseSelected

	# ------------------------------------------------------------ #

	funcs = [func for (k,func) in locals().items() if k.startswith('nk')]

	from nk_load_nk import createMenu
	createMenu('NK',funcs)

	toolbar = nuke.menu('Nodes')
	gizMenu = toolbar.addMenu('Gizmos')
	for giz in [os.path.splitext(n)[0] for n in os.listdir(os.path.join(os.environ["HOME"],".nuke")) if re.search("gizmo",n)]:
		gizMenu.addCommand(giz,"nuke.createNode('%s')"%giz)
