import nuke
import os
import re

def fileop(oper):
	"""
	Enables copying/moving source files of Read/Write nodes.
	Dialog box enables choosing a destination directory to 
	relocate/copy files. Optionally, if a new name is entered,
	the files will be moved/copied and finally renamed.
	"""
	import shutil
	n = nuke.thisNode()
	first = last = None
	if n.Class() == "Read":
		first = n['first'].value()
		last = n['last'].value()
	elif n.Class() == "Write" and n['use_limit'].value():
		first,last = n['first'].value(),n['last'].value()
	else:
		pass
	if (first != None) and (last != None):
		old_path = os.path.dirname(nuke.filename(n))
		new_path = nuke.getFilename("Choose a new location...",pattern='/')
		rename = True if re.search(r'%0\dd',new_path) else False
		if rename:
			if not os.path.exists(os.path.dirname(new_path)):
				os.mkdir(os.path.dirname(new_path))
		else:
			if not os.path.exists(new_path):
				os.mkdir(new_path)
		if os.path.isdir(new_path) and new_path.endswith("/") is False:
			new_path += "/"
		get_path = lambda p: new_path%i if rename else new_path
		files = [(nuke.filename(n)%i,get_path(i)) for i in range(first,last+1) if os.path.exists(nuke.filename(n)%i)]
		if oper==1:
			mainMsg = "Relocating files..."
			subMsg = "Moved"
		else:
			mainMsg = "Copying files..."
			subMsg = "Copied"
		task = nuke.ProgressTask(mainMsg)
		T = len(files)
		good = 0
		for (i,f) in enumerate(files):
			op,np = f[0],f[1]
			print "%s --> %s" % (op,np)
			try:
				shutil.copy2(op,np)
				good+=1
				task.setMessage("%s:%s"%(subMsg,op))
				x = int((i/float(T)*100))
				task.setProgress(x)
			except:
				break
		if good == T:
			if oper==1:
				try:
					[os.remove(f[0]) for f in files]  ## TODO: This is not working
					nuke.message("All files were relocated")
				except:
					nuke.message("All files were copied but originals could not be removed")
			else:
				nuke.message("All files were copied")
			update_source = nuke.ask("Update node's source/target?")
			if update_source:
				filename = os.path.split(nuke.filename(n))[-1]
				set_new_path = rename and new_path or new_path+filename
				n['file'].setValue(set_new_path)
	else:
		print "Cannot acquire range"

def attach_file_operations(*args):
	n = nuke.thisNode()
	if 'fileops' not in n.knobs().keys():
		n.addKnob(nuke.Text_Knob("fileops","File Operations"))
		n.addKnob(nuke.PyScript_Knob("copyBtn","Copy","nuke.fileop(0)"))
		n.addKnob(nuke.PyScript_Knob("moveBtn","Move","nuke.fileop(1)"))
	return n

nuke.addOnUserCreate(attach_file_operations,(),{},"Write")
nuke.addOnUserCreate(attach_file_operations,(),{},"Read")
nuke.fileop = fileop














