import sublime, sublime_plugin
import threading 

from . import common



class AddBookmarkCommand(sublime_plugin.WindowCommand, common.baseBookmarkCommand):
	def __init__(self, window):
		self.thread = None
		common.baseBookmarkCommand.__init__(self, window)

	def run(self):
		if self.thread is not None:
			self.thread.join()

		self.thread = AddBookmarkHandler(self.window, self)
		self.thread.start()
		
class AddBookmarkHandler(threading.Thread):
	def __init__(self, window, addBookmarkCommand):
		self.window = window
		self.bookmarks = common.getBookmarks()

		threading.Thread.__init__(self)  
		
		

	def run(self):
		view = self.window.active_view()
		defaultString = ""

		self.window.show_input_panel("Add Bookmark", defaultString, self.Done_, None, self.Cancel_)
	
	def Cancel_(self):
		return

	def Done_(self, viewString):
		bookmark = common.Bookmark(self.window, viewString)
		bookmark.printDbg()
		self.bookmarks.append(bookmark)

		
		common.setBookmarks(self.bookmarks)
		common.updateGutter(self.window.active_view())
		return
		