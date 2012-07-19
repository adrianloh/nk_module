# ---------------------------------------------------------
# This module contains callback functions that bind to the
# major events of a script's lifecycle, namely when scripts
# are loaded, saved and rendered
# --------------------------------------------------------

import nuke
import os

def createWriteDirs():
	""" Automatically create directories in Write path if path doesn't exists. """
	f = nuke.filename(nuke.thisNode())
	dirr = os.path.dirname(f)
	if not os.path.exists(dirr):
		osdir = nuke.callbacks.filenameFilter(dirr)
		os.makedirs(osdir)

nuke.addBeforeRender(createWriteDirs)

def writeNoOverwrite():
	""" Automatically create directories in Write path if path doesn't exists. """
	if nuke.thisNode()['no_overwrite'].value():
		file_to_be_rendered = nuke.filename(nuke.thisNode(), nuke.REPLACE)
		if os.path.exists(file_to_be_rendered):
			msg = "File already exists: %s" % file_to_be_rendered
			try: raise RuntimeError(msg)
			except RuntimeError as e: print e

nuke.addBeforeFrameRender(writeNoOverwrite)

def writeNoOverwriteKnob():
	n = nuke.thisNode()
	if 'no_overwrite' not in n.knobs().keys():
		n.addKnob(nuke.Boolean_Knob("no_overwrite","no_overwrite"))
	else: pass

nuke.addOnCreate(writeNoOverwriteKnob,(),{},"Write")

def setEnvironment():
	"""
	Any knob added to a script's Root panel whose name is all capitalized is declared
	as an environment variable callable from any node with [getenv VARIABLE]. Note
	that you must reload the script before the variable becomes active.
	"""
	isAllCaps = lambda s: True if s.upper() == s else False
	N = [nuke.root()[i].name() for i in nuke.root().knobs() if isAllCaps(nuke.root()[i].name())]
	V = [nuke.root()[i].value() for i in nuke.root().knobs() if isAllCaps(nuke.root()[i].name())]
	h = dict(zip(N,V))
	for k in h.keys(): os.environ[k] = h[k]

nuke.addOnScriptLoad(setEnvironment)

def removeTimecode():
	try:
		nuke.thisNode()['timecode'].setValue(None)
	except NameError: pass

nuke.addBeforeRender(removeTimecode, args=(), kwargs={}, nodeClass='Write')
