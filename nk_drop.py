import nuke, nukescripts
import os
import re
import threading
import urllib2

def read_from_http(url):
	"""
	Read from URL
	This is an example of handling clipboard data when it is pasted
	into the DAG, your (callback) function must take two arguments,
	the mimetype of the data, and the data itself. If you're handling it,
	return True, else None.
	"""
	file_name = url.split('/')[-1]
	u = urllib2.urlopen(url)
	save_path = os.path.join(os.path.split(nuke.root().name())[0],file_name)
	f = open(save_path, 'wb')
	save_path = nuke.pacify(save_path)
	meta = u.info()
	file_size = int(meta.getheaders("Content-Length")[0])
	def download():
		task = nuke.ProgressTask("Downloading %s" % file_name)
		task.setMessage("Downloading: %s Bytes: %s" % (file_name, file_size))
		file_size_dl = 0
		block_sz = 8192
		while True:
			buffer = u.read(block_sz)
			if not buffer:
				break
			file_size_dl += len(buffer)
			f.write(buffer)
			status = file_size_dl*100.0/file_size
			task.setProgress(int(status))
		f.close()
		read = nuke.createNode("Read","file %s" % save_path, inpanel=False)
		read['selected'].setValue(True)
	threading.Thread( None, download ).start()

def read_fbx(path):
	path = re.sub("file:\/\/", "", path)
	nuke.nodes.ReadGeo2(file=path)

def create_precomp(path):
	path = re.sub("file:\/\/", "", path)
	if nuke.ask("Create precomp? [Yes] Import nodes [No]"):
		nuke.nodes.Precomp(file=path)
		return True
	else:
		return None

def clipboardHandler(mime,data):
	if mime=='text/plain':
		if data.startswith("http") and re.search("\.\w+$",data):
			read_from_http(data)
			return True
		elif re.search("^file:\/\/.+fbx", data, re.IGNORECASE):
			read_fbx(data.strip())
			return True
		elif re.search("^file:\/\/.+nk", data, re.IGNORECASE):
			return create_precomp(data.strip())
		else:
			path = re.sub(r"\"",r"",data)
			if os.path.exists(path) and os.path.isfile(path):
				save_path = nuke.pacify(path)
				read = nuke.createNode("Read","file %s" % save_path, inpanel=False)
				read['selected'].setValue(True)
				return True
			else:
				return None
	else:
		return None

nukescripts.addDropDataCallback(clipboardHandler)
