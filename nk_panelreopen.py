import nuke

PANEL_HISTORY = []

def close_panel():
	if nuke.thisKnob().name()=='hidePanel':
		PANEL_HISTORY.append(nuke.thisNode().name())

nuke.addKnobChanged(close_panel)

def nk_reopen_panels():
	"""
	Reopen panels
	SS Alt+q
	"""
	if len(PANEL_HISTORY)>0:
		last_node = nuke.toNode(PANEL_HISTORY.pop())
		if last_node is not None:
			last_node.showControlPanel()
	else:
		nuke.message("No more panels to reopen!")