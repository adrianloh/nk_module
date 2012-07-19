def findAlpha():
	"""
	On Copy nodes, check whether incoming alpha channel from "A" input exists,
	or whether it's solid white/black then uses red channel instead. Note that
	the DAG will at first show an ERROR on the node, change channels in the
	viewport and changing back gets rid of it.
	"""
	n = nuke.thisNode()
	# Sample a 4K area from the alpha channel, just to be sure
	sample = n.sample("rgba.alpha",0,0,4000,4000)
	if sample == 1 or sample == 0 or n.hasError():
		n['from0'].setValue("red")

nuke.addUpdateUI(findAlpha,(),{},"Copy")

def nk_paste_to_selected_nodes():
	"""
	Paste into selected
	"""
	sel = nuke.selectedNodes()
	[n['selected'].setValue(False) for n in nuke.selectedNodes()]
	for n in sel:
		n['selected'].setValue(True)
		nuke.nodePaste(nukescripts.cut_paste_file())
		n['selected'].setValue(False)