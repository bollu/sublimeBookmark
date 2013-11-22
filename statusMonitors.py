import sublime, sublime_plugin
from . import common
	
class BookmarkSaveLoad(sublime_plugin.EventListener):
	def on_new_async(self, view):
		common._read_bookmarks_from_disk()

		
	def on_modified_async(self, view):
		common._write_bookmarks_to_disk()

	
	def on_pre_save_async(self, view):
		common._write_bookmarks_to_disk()

	
	