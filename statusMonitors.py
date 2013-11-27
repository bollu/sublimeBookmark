import sublime, sublime_plugin
from . import common

g_ACTIVE = False

class gutterMarker(sublime_plugin.EventListener):
	def __init__(self):
		global g_ACTIVE
		g_ACTIVE = False

		def on_activated_async(self, view):
			common.init(sublime.active_window())

			
# 	def on_activated_async(self, view):
# 		global g_ACTIVE

# 		#calling mark_gutter causes on_activaed_async to be called recursively
# 		#prevent that.
# 		if(g_ACTIVE):
# 			return

# 		g_ACTIVE = True

# 		window = sublime.active_window()

# 		#only mark those bookmarks which can
# 		#for bookmark in common.get_bookmarks(window, True):
# 		#	pass
# #			bookmark.mark_gutter(window)

# 		g_ACTIVE = False

	

	def on_pre_close(self, view):
		common._write_bookmarks_to_disk(sublime.active_window())

class BookmarkLoader(sublime_plugin.WindowCommand):
	def run(self, window):
		common.init(window)



	
	