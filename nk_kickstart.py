import nuke
import os, re
from random import randint
from datetime import datetime

# ----- WORD LIST FOR RANDOM WORD GENERATOR ------ #

from words import words as wordList
nuke.randomWord = lambda: wordList[randint(0,len(wordList)-1)].title()

# ------------------------------------------------- #

def saveRandomName():
	"""
	Automatically saves comps on launch with a random name to NUKE_TEMP_DIR.
	To remove a comp from cache, delete all nodes, save, and quit.
	"""
	if nuke.root().name() == "Root":
		path =	os.environ["NUKE_TEMP_DIR"]\
				  + "/" + nuke.randomWord()\
				  + "-" + nuke.randomWord()\
				  + "_" + datetime.now().strftime("%d-%B-%Y")\
		+ "_v1.nk"
		print "Default saved: " + path
		nuke.scriptSaveAs(path)
		nuke.removeOnUserCreate(saveRandomName)

nuke.addOnUserCreate(saveRandomName)

def deleteEmptyScript():
	""" Removes any *saved* script if the script is empty."""
	allNodes = nuke.allNodes()
	dirPath,script = os.path.split(nuke.root().name())
	if len([n for n in allNodes if n.Class() != "Viewer"]) == 0 and script != "Root":
		os.chdir(dirPath)
		[os.remove(f) for f in os.listdir(dirPath) if re.search(script.split(".")[0],f)]

nuke.addOnScriptClose(deleteEmptyScript)