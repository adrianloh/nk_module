import nuke
import os
import re
import time
from subprocess import Popen,PIPE
import threading
from urllib import urlopen
from uuid import uuid4


HOST = "http://192.168.2.10"
DBNAME = "test_reactor"

try:

	from couchdb import *
	import simplejson as json
	db = Database("%s/%s" % (HOST, DBNAME))
	len(db)
	
	toolbar = nuke.menu('Nodes')
	RMenu = toolbar.addMenu('Reactor')
	RMenu.addCommand("Commit","reactor.commit()")

except:

	print "Could not connect to %s" % DBNAME

def commit():
	""" Commit comp to the database and if Write nodes are found, 
		render a frame as the comp's thumbnail"""	
	
	# For the sake of flexibility, any new knob/parameter (usually a Text_Input knob)
	# added to the comp's root panel with Name that starts with an underscore 
	# is used as the "indexing key" for Views in Couch. This gets us to an array for 
	# View keys that look like this:
	#
	# 	[Parameter1, Paramater2, Parameter2, Year, Month, Day, Hour, Minute, Second]
	#
	# This is easily indexed and has the advantage of giving us the entire
	# traversal tree in one query and is also easily filtered. Also note that the
	# position of the knob in the User tab of the Root panel determines the order
	# of the keys.
	
	N = [nuke.root()[i].name()[1:] for i in nuke.root().knobs() if nuke.root()[i].name().startswith("_")]
	V = [nuke.root()[i].value() for i in nuke.root().knobs() if nuke.root()[i].name().startswith("_")]
	h = dict(zip(N,V))

	# Additional info we wish to store with each comp.
	
	h['modtime'] = time.strftime("%Y-%b-%d-%H%M%S",time.localtime())
	h['comments'] = nuke.root()['label'].value()
	h['dimension'] = "%ix%i" % (nuke.root().width(),nuke.root().height())
	h['fps'] = nuke.root()['fps'].value()
	now_string = time.strftime("%Y-%m-%d-%H-%M-%S",time.localtime())
	now_array = now_string.split('-')
	h['modtime'] = now_array

	# If there are no custom paramaters/knobs, then we assign it to the default
	# "project" called @UNTITLED. Because of this, it's important to implement
	# at least 1 knob called Title which acts as the traditional file name at
	# the very least.
	
	if not V: V = ["@UNTITLED", uuid4().hex]
	
	# The sort key we constructed for the View is also the _id of the comp. We have
	# to join the array into a string.
	
	h['sortkey'] = V + now_array
	_id = "__".join(V) + "__" + now_string
	
	# Save the comp into a temp folder and commit it to Couch.
		
	scriptpath = os.path.join(os.environ["TEMP"],_id+".nk")
	nuke.scriptSaveAs(scriptpath,overwrite=1)
	
	db[_id] = h
	
	db.put_attachment(db[_id], open(scriptpath).read(), _id+".nk", 'application/nuke-x' )

	# With this temp comp, if Write nodes are found, "hack" the Write nodes with sed-like
	# precision to output 256x256 jpegs. We want to render only one frame. For now, 
	# it's always set to frame 10.

	if nuke.allNodes("Write"):

		thumbnailer(scriptpath)

		# Remember that Nuke uses only *nix paths. So if we're on windows
		# change those to Windows paths.

		nodes_to_render = []

		for node in nuke.allNodes("Write"):
			c = {}
			c['name'] = node.name()
			if not re.search(r'mov$',nuke.filename(node)):	# Does this work for movs really? What about other media types?
				p = re.sub(r'\....$',r'.th.jpg"',nuke.filename(node))
			else:
				p = re.sub(r'mov$',r'%05d.th.jpg"',nuke.filename(node))
			c['path'] = p % 10
			nodes_to_render.append(c)

		# Send the comp for background render.
			
		inHerBehind(scriptpath,nodes_to_render,_id)
	


def inHerBehind(scriptpath,nodes,couchID):
	""" Launch a bunch of background threads to render the names of the nodes 
	in the nuke script and attach them to the Couch document with _id
	of couchID """

	def split(p): return re.split(r"[\\\\|/]",p) # Completely split up an os path
	def join(p,x): return x.join(p)[:-1]		 # Join the path (p) back using (x) separator
	def recompose(p,x): return join(split(p),x)  # Perform the above two operations, essentially reconstructing the path

	def render(cmd,name,renderedpath):
		# A single thread process. It attemps to acquire the lock, if acquired,
		# start the render, if not, wait around. After rendering, attach it
		# to the document with couchID.
		while True:
			if free.acquire():
				try:
					ospath = recompose(renderedpath,'\\\\') if nuke.env['WIN32'] else renderedpath
					print "Rendering: %s" % name
					Popen(cmd,stdout=PIPE).wait()
					if os.path.exists(ospath):
						print "Rendering done: %s" % name
						imgName = name+"@"+recompose(renderedpath,"$")
						db.put_attachment(db[couchID], open(ospath,'rb').read(), imgName, 'image/jpeg' )
						os.remove(ospath)
						print "Uploaded to database: %s" % couchID
						free.notifyAll()
						free.release()
						break
					else:
						print "No thumbnail rendered: %s" % name
						raise
				except:
					# If something fucks up, delete the entry from Couch and notify user
					del db[couchID]
					nuke.message("Previous commit to Reactor did not succeed.")
			else:
				free.wait()

	# We want only one thread running at any one time so Nuke's main thead operations
	# are not hindered in any way. This is the simple condition/lock that ensures that.
	
	free = threading.Condition()

	for	node in nodes:
		name = node['name']
		renderedpath = node['path']
		cmd = "nuke -m 1 -F 10 -X %s -ix %s" % (name,scriptpath)
		T = threading.Thread(group=None,target=render,name=None,args=[cmd,name,renderedpath])
		T.start()



def thumbnailer(p):
	insert = """
Reformat {
format "256 256 0 0 256 256 1 square_256"
black_outside true
name Reformat1
selected true
xpos -229
ypos -161
}

"""
	f = open(p).readlines()
	lines = [i for (i,l) in enumerate(f) if l.startswith("Write")]
	for i in lines:
		f[i] = insert+f[i]
	
	ff = open(p,'w')
	for l in f:
		ff.write(l)
	
	ff.close()							### TODO: Clean this shit up, disable OFX plugins to speed up renders

	f = open(p).readlines()
	
	blines = [i for i,l in enumerate(f) if re.search('file',l) and f[i-1].startswith("Write")]

	print blines

	for b in blines:
		f[b] = re.sub(r'\....["|\n]$',r'.th.jpg',f[b])  ### TODO: Make the 'th.jpg' part DRY #reactor_save() has it as well
		f[b+1] = ' type jpeg'
		
	ff = open(p,'w')
	for l in f:
		ff.write(l)
	
	ff.close()
	

