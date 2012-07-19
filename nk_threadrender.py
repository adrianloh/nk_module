import nuke
import threading

def nk_multithreadedRender():
	"""
	Multithreaded Render
	"""
	threads = nuke.env['threads']-2
	c = nuke.getInput("Number of threads (default %i)" % threads)
	if c: threads = int(c)
	THREADCOUNT = threads
	nuke.scriptSave()
	renderNode = nuke.selectedNode()
	use_limit = renderNode['use_limit'].value()
	first = renderNode['first'].value() if use_limit else nuke.root().firstFrame()
	last = renderNode['last'].value() if use_limit else nuke.root().lastFrame()
	frames = [i for i in range(first,last+1)]
	threads = [[] for i in range(0,THREADCOUNT)]
	[threads[i%THREADCOUNT].append(frame) for (i,frame) in enumerate(frames)]

	THREAD_FRAMES = {}

	def render(frameList):
		_maxCache = str(max(nuke.memory("max_usage") / 1097152, 16)*4) + "M"
		try:
			t = nuke.executeBackgroundNuke(nuke.EXE_PATH,
				[renderNode],
				nuke.FrameRanges(frameList),
				nuke.views(),
				{"maxThreads":1,"maxCache":_maxCache})
			THREAD_FRAMES[t] = frameList
		except Exception as e:
			print e

	[render(frameList) for frameList in threads]
