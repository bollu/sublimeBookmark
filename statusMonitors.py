import sublime, sublime_plugin
from . import common

g_ACTIVE = False

class gutterMarker(sublime_plugin.EventListener):
	def __init__(self):
		global g_ACTIVE
		g_ACTIVE = False

	

	def on_modified_async(self, view):
		window = sublime.active_window()

		for bookmark in common.get_bookmarks(window, True):
			bookmark.update_row_column(window)
	
		common._write_bookmarks_to_disk(window)



class BookmarkLoader(sublime_plugin.WindowCommand):
	def run(self, window):
		common.init(window)



	
	