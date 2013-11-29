import sublime, sublime_plugin
from . import common

class gutterMarker(sublime_plugin.EventListener):

	def on_deactivated_async(self, view):
		self.save_all(view)

	def on_activated_async(self, view):
		self.save_all(view)

	def on_clone(self, view):
		self.save_all(view)

	def save_all(self, view):
		window = sublime.active_window()

		#get *ALL* bookmarks and update them
		for bookmark in common.get_bookmarks(window, False):
			bookmark.update_row_column(window)
			bookmark.mark_gutter(window)
		
		common._write_bookmarks_to_disk(window)


class BookmarkLoader(sublime_plugin.ApplicationCommand):
	def run(self, window):
		common.init(window)



	
	