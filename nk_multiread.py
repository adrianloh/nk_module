import os
import re

def _getClips(dir,format="nuke",symbol="@"):
	"""
	Given a directory, returns a dictionary of sequence files in the form:
		dict[sequence_template] = [first_frame,last_frame]
	e.g.
		when format is "nuke":
			d[sequence_v1.%05d.exr] = [1,100]
		when format is "shake":
			d[sequence_v1.@@@@@@.exr] = [1,100]
	"""

	d = {}
	r = {}

	def make_pattern(filename):
		"""
		Creates a regular expression pattern from a filename, aka a "template"
		to match against other files. Assumes that rightmost consecutive digits
		is the "index counter". E.g:
			shot01_project1234_version01.0001.exr #-> shot01_project1234_version01.\d\d\d\d.exr
		"""
		sf = re.sub('\d',"@",fn)
		rmost_counter = re.findall("@{1,}",sf)[-1]
		pat_len = len(rmost_counter)
		pat_position = sf.rindex(rmost_counter)
		bfn = re.findall(".",filename)
		for i in range(pat_len):
			pp = pat_position+i
			bfn[pp] = r"\d"
		t = "^"+"".join(bfn)+"$"
		return t

	os.chdir(dir)

	fff = [f for f in os.listdir(dir) if os.path.isfile(f)]

	if fff:

		for fn in fff:
			template = make_pattern(fn)
			if template in d:
				continue
			else:
				d.setdefault(template,[])

		for t in d.keys():
			for f in fff:
				if re.search(t,f):
					d[t].append(f)

		for dr in d.keys():
			c = dr.count("\d")
			printf = re.sub("(\\\d)+","%%0%id"%c,dr)[1:-1]
			substr = re.sub("\\\d","%s"%symbol,dr)[1:-1]
			np = re.sub("(\\\d)+","("+"\d"*c+")",dr)
			cc = sorted(d[dr])
			first = int(re.findall(np,cc[0])[0])
			last = int(re.findall(np,cc[-1])[0])
			if format == "nuke":
				r[printf] = [first,last]
			elif format == "shake":
				r[substr] = [first,last]

	return r

def _nk_load_directory():
	"""
	Load directory
	"""
	formats = "tif tiff tif16 tiff16 ftif ftiff tga targa rla xpm yuv avi cin dpx exr gif \
				hdr hdri jpg jpeg iff png png16 mov r3d raw psd sgi rgb rgba sgi16 pic"

	SUPPORTED_FORMATS = "["+ "|".join(formats) + "]"	# Compile regex pattern

	loadDir = nuke.getClipname("Select a folder...")
	if os.path.isdir(loadDir):
		for f,ff,fff in os.walk(loadDir):
			clips = getClips(f)
			if clips:
				for clip in clips.keys():
					extension = os.path.splitext(clip)[-1][1:]
					if re.search(SUPPORTED_FORMATS,extension,re.IGNORECASE):
						path = "%s/%s" % (f,clip)
						first,last = clips[clip][0],clips[clip][1]
						read = nuke.createNode("Read",inpanel=False,knobs="first %i last %i before bounce after bounce" % (first,last))
						read['file'].setValue(path)