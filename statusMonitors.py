import sublime, sublime_plugin
from . import common

class gutterMarker(sublime_plugin.TextCommand):
	def __init__(self, view):
		self.view = view
		common.updateGutter(self.view)



	def run(self, edit):
		common.updateGutter(self.view)
		pass

class bookmarkSaver(sublime_plugin.EventListener):
	def __init__(self):
		pass

	def on_modified_async(self, view):
		common.updateGutter(view)
		
	def on_pre_close(self, view):
		common.gPersist.writeToDisk()

	def on_pre_save_async(self, view):
		common.gPersist.writeToDisk()