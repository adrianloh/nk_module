import nuke

def createMenu(menuName, funcs):
	if nuke.env['gui']:
		toolbar = nuke.menu('Nodes')
		submenu = toolbar.addMenu(menuName)
		for func in funcs:
			fname = func.__name__
			ftemp = func
			exec("nuke.%s=ftemp" % fname)
			docstring = [l.strip() for l in func.__doc__.split("\n")]
			label = docstring[1]
			if docstring[2].startswith("SS"):
				shortcut = docstring[2].split(" ")[1]
				submenu.addCommand(label,"nuke.%s()" % fname,shortcut)
			else:
				submenu.addCommand(label,"nuke.%s()" % fname)