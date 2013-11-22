import sublime, sublime_plugin
from . import common
	
class bookmarkSaver(sublime_plugin.EventListener):

	def on_modified_async(self, view):
		common.writeBookmarksToDisk()

		
	def on_pre_save_async(self, view):
		common.writeBookmarksToDisk()

	
	