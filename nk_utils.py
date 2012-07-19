import nuke, nukescripts
import os, re

def actualFilename(node):
	"""
	Given a node that reads a file, returns a tuple where:
	[0] The parent/containing folder of the file
	[1] The file's name you see in nuke's panel
	[2] A real name for the file
	"""
	(dirPath,basename) = os.path.split(nuke.filename(node))
	def getFirstFrameOfSequence():
		first_frame = node['first'].value()
		if node.Class()=='Write' and (node['first'].value()==node['last'].value()):
			# For Write nodes without a render range set, assume the
			# first frame is the comp's first frame.
			first_frame = nuke.root().firstFrame()
		return first_frame
	if re.search('#+',basename):
		# NOTE: On Read nodes, for some fucky reason, if a node's file name
		# is file.%05d.jpg -- nuke.filename(node) gives you file.#####.jpg instead.
		# c = '%0' + str(len(re.findall('#',basename))) + 'd'
		# filename = re.sub('#+',c,basename) % getFirstFrameOfSequence()
		basename = nukescripts.replaceHashes(basename)
	if re.search(r"%\d+d",basename): # Sequence files
		filename = basename % getFirstFrameOfSequence()
	else: # Standalone/single non-sequence files
		filename = basename
	return dirPath, basename, filename

nuke.actualFilename = actualFilename

def _allNodes():
	nodes = []
	[nodes.append(n) for n in nuke.allNodes() if n.Class() not in ["Group", "Viewer"]]
	[[nodes.append(n) for n in gg] for gg in [g.nodes() for g in nuke.allNodes("Group")]]
	return nodes

nuke._allNodes = _allNodes

def _selected():
	return [n for n in _allNodes() if n.shown()]

nuke._selectedNodes = _selected