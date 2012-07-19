import nuke, os, re
from hashlib import sha1
from nk_customize import pyScriptKnob, createRootKnob

def readShot():
	import shotgun
	shotcode = nuke.getInput('Shot Code')
	s = shotgun.getShotData(shotcode, ['Source clip', 'Cut In', 'Cut Out'])
	(clipName, crc) = s['Source clip'].strip().split(':')
	results = nuke.spotlight(clipName)
	if results:
		for readPath in results:
			if sha1(open(readPath).read()).hexdigest() == crc:
				readPath = nuke.pacify(readPath)
				nuke.createNode('Read','file %s' % readPath)
				rangeStr = 'first_frame %s last_frame %i' % (s['Cut In'],int(s['Cut Out']-1))
				nuke.createNode('FrameRange',rangeStr)
	else:
		nuke.message('Cannot locate clip %s' % clipName)

nuke.readInFromShotgun = readShot

def updateShotgunStatus():
	import shotgun
	stats = {"In_Progress":"ip", "On_Hold":"hld", "Final":"fin"}
	scriptPath = re.sub(r'/',r'\\',nuke.root().name())
	scriptName = os.path.split(scriptPath)[-1].split('.')[0]
	shotcode = scriptName.split("__")[0]
	try:
		shot = shotgun.getShotData(shotcode,'Status')
		print shot['Status']
	except Exception as e:
		nuke.message("Can't figure out Shot Code from script name!")
		return None
	p = nuke.Panel('Update Status: %s' % shotcode)
	p.addEnumerationPulldown('Status', " ".join(stats.keys()))
	if p.show()==1:
		stat = p.value('Status')
		try:
			shotgun.updateShot(shotcode, 'Status', stats[stat])
			nuke.message("Update OK!")
		except Exception:
			nuke.message("Update failed!")
	else:
		pass

nuke.updateShotgunStatus = updateShotgunStatus

def createShotgunVersion():
	import shotgun
	scriptPath = re.sub(r'/',r'\\',nuke.root().name())
	scriptName = os.path.split(scriptPath)[-1].split('.')[0]
	projCode = scriptName.split('_')[0]
	res = shotgun.sg.find_one('Project',[['sg_code','is',projCode]],['name'])
	if res is None:
		nuke.message("Cannot locate project code '%s'. Please check filename." % projCode)
		return None
	else:
		projName = res['name']
		projShotcodes = [h['Shot Code'] for h in shotgun.getShotsInProject(projName,['Shot Code'])]
		shotCode = scriptName.split('__')[0]
		h = {True:shotCode, False:"%s **WARNING** Shotcode doesn't exists" % shotCode}
		shotCode = h[shotCode in projShotcodes]
		p = nuke.Panel('Create Shotgun version')
		p.setWidth(600)
		p.addSingleLineInput('shotcode', shotCode)
		p.addSingleLineInput('version name', scriptName)
		p.addMultilineTextInput('description', '')
		res = p.show()
		if res==1:
			shotCode = p.value('shotcode')
			vrName = p.value('version name')
			vrDescrip = p.value('description')
			try:
				res = shotgun.createVersion(projName, shotCode, vrName, vrDescrip, scriptPath)
				if res.has_key('id'): nuke.message('Published to Shotgun!')
			except Exception:
				nuke.message('Publish failed!')

nuke.createShotgunVersion = createShotgunVersion

nuke.addOnScriptLoad(createRootKnob,pyScriptKnob("Publish version","nuke.createShotgunVersion()",'publishVr'))
nuke.addOnScriptLoad(createRootKnob,pyScriptKnob("Update status","nuke.updateShotgunStatus()",'updateSGStatus'))












