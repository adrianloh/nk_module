# -----------------------------------------------------
# This module contains primarily node customizations
# such as additional knobs that are added when 
# nodes are created, either to give nodes extra
# paramaters, or entirely new abilities, like batch file
# operations on Read and Write nodes
# ----------------------------------------------------

import nuke
import os, re
import string
import threading
import time
from uuid import uuid4
from random import sample

# -------------- KNOB CREATION ---------------- #

def all_labels(n):
	""" Return all labels of knobs"""
	return [n[i].label() for i in n.knobs()]
	
def all_names(n):
	""" Return all variable names of knobs"""
	return [n[i].name() for i in n.knobs()]

# WARNING: The following "root" functions are used by nk_shotgun

def getRootLabels():
	return [nuke.root()[k].label() for k in nuke.root().knobs()]

def getRootNames():
	return [k for k in nuke.root().knobs()]

def pyScriptKnob(label, script, name=None):
	name = name if name else uuid4().hex
	knob = nuke.PyScript_Knob(name, label)
	knob.setValue(script)
	return knob

def createRootKnob(k):
	if k.name() not in getRootNames():
		nuke.root().addKnob(k)

# ---------------------------------------------------------

def draw_line(n,label):
	n.addKnob(nuke.Text_Knob(uuid4().hex,label))
	return n

# ------------------- CALLBACKS ------------------- #
# Nuke has two primary ways of adding callbacks to nodes.
# addOnUserCreate and addUpdateUI. The difference is that
# addOnUserCreate changes a node only at the moment of 
# creation, while addUpdateUI changes nodes continuously, 
# thus consequently, if you open an old script, it will 
# retroactively modify the script's nodes.

def customizeNodeOnUserCreate():
	n = nuke.thisNode()
	nClass = nuke.thisClass()
	
	if nClass == "Write":
		n['channels'].setValue("rgba")
		currentDirOut = "[file dirname [value root.name]]/[knob name]/[knob name].%07d.exr"
		n['file_type'].setValue("exr")
		n['file'].setValue(currentDirOut)

	elif nClass == "Switch":
		n['label'].setValue("[knob which]")
		n['note_font'].setValue("Arial Bold")
		n['note_font_size'].setValue(18)

	elif nClass == "Card2":
		label = "[knob translate.x] [knob translate.y] [knob translate.z]"
		n['label'].setValue(label)

	elif nClass == "Shuffle":
		n['label'].setValue("[knob alpha] > alpha")

	elif nClass == "NoOp":
		n['note_font'].setValue("Bebas Neue")
		n['note_font_size'].setValue(18)

	elif nClass == "CameraTracker1_0":
		n['analysisRange'].setValue("Analysis Range")
		n['analysisStart'].setValue(nuke.root().firstFrame())
		n['analysisStop'].setValue(nuke.root().lastFrame())
		n['lensDistortionType'].setValue("Unknown Lens")

	elif nClass == "Read":
		n['label'].setValue("[file dirname [knob file]]")
	
	else: pass

nuke.addOnUserCreate(customizeNodeOnUserCreate)

def uniquifyWrites():
	"""
	Make sure Write names are not of the generic form "Write1","Write2", etc.
	BUG: We hook this function to addUpdateUI because customizing node name 
	at addOnUserCreate crashes Nuke!
	"""
	n = nuke.thisNode()
	if re.search(r"^Write\d+$",n.name()):
		suffix = "".join(sample(string.ascii_letters,6)).upper()
		n['name'].setValue("Write_"+suffix)

nuke.addOnCreate(uniquifyWrites,(),{},"Write")

def writeReadingStatus():
	"""
	Change appearance of Write nodes based on whether the node
	is in read/write mode.
	"""
	n = nuke.thisNode()
	if n['reading'].value():
		n['postage_stamp'].setValue(True)
		n['tile_color'].setValue(13500671)
	elif n['reading'].value() != True and n['tile_color'].value != 0:
		n['postage_stamp'].setValue(False)
		n['tile_color'].setValue(0)
	else: pass

nuke.addUpdateUI(writeReadingStatus,(),{},"Write")

def dpxNoAlpha():
	"""
	Do not allow DPX files to be written with alpha
	"""
	n = nuke.thisNode()
	if nuke.filename(n).endswith("dpx"):
		n['channels'].setValue("rgb")

nuke.addUpdateUI(dpxNoAlpha,(),{},"Write")

# Attach Reveal in Finder to Write/Read nodes"""
def deprecated_attach_reveal_in_finder():
	n = nuke.thisNode()
	if not n.knobs().has_key("revealPath"):
		K = pyScriptKnob(" Reveal file ", "nuke.revealFile(nuke.filename(nuke.thisNode()))", "revealPath")
		n.addKnob(K)

#nuke.addUpdateUI(attach_reveal_in_finder,(),{},"Write")
#nuke.addUpdateUI(attach_reveal_in_finder,(),{},"Read")
nuke.addOnScriptLoad(createRootKnob,pyScriptKnob(" Reveal file ", "nuke.revealFile(nuke.root().name())", "revealPath"))
