import sublime, sublime_plugin
import threading 

from . import common



class AddBookmarkCommand(sublime_plugin.WindowCommand, common.BaseBookmarkCommand):
	def __init__(self, window):
		self.thread = None
		common.BaseBookmarkCommand.__init__(self, window)

	def run(self):
		if self.thread is not None:
			self.thread.join()

		self.thread = AddBookmarkHandler(self.window, self)
		self.thread.start()
	
	def description(self):
		return "Add a Bookmark"

class AddBookmarkHandler(threading.Thread):
	def __init__(self, window, addBookmarkCommand):
		self.window = window
		self.bookmarks = common.get_bookmarks(self.window)

		threading.Thread.__init__(self)  
		
		

	def run(self):
		view = self.window.active_view()
		defaultString = ""

		self.window.show_input_panel("Add Bookmark", defaultString, self._done, None, self._cancel)
	

	def _cancel(self):		
		return


	def _done(self, viewString):
		bookmark = common.Bookmark(self.window, viewString)
		bookmark.print_dbg()

		self.bookmarks.append(bookmark)

		common.set_bookmarks(self.bookmarks, self.window)

		return
	