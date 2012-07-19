import nuke
from nk_load_nk import createMenu

def nk_align_vert():
	"""
	V Align
	"""
	positions = [t.ypos() for t in nuke.selectedNodes()]
	mid = (min(positions)+max(positions))/2
	[t.setYpos(mid) for t in nuke.selectedNodes()]

def nk_align_distribute_across():
	"""
	H Spread
	"""
	nodes = sorted([n for n in nuke.selectedNodes()], key=lambda n: n.xpos())
	minX = nodes[0].xpos()
	distance = 150
	print [nodes[i].setXpos(minX+distance*i) for i in range(1,len(nodes))]

funcs = [func for (k,func) in locals().items() if k.startswith('nk')]
createMenu('DAG Clean',funcs)

