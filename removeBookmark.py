import sublime, sublime_plugin
from pickle import dump, load
import threading 

from . import common


class RemoveBookmarkCommand(sublime_plugin.WindowCommand, common.baseBookmarkCommand):
	def __init__(self, window):
		self.thread = None
		common.baseBookmarkCommand.__init__(self, window)
		self.load_()

	def run(self):
		if self.thread is not None:
			self.thread.join()

		self.load_() 

		if len(self.bookmarks) == 0:
			sublime.status_message("no bookmarks to goto!")
			return 0

		self.thread = RemoveBookmarkHandler(self.window)
		self.thread.start()

		
class RemoveBookmarkHandler(threading.Thread):
	def __init__(self, window):
		self.window = window
		
		global gPersist
		self.bookmarks = common.gPersist.getBookmarks()
		self.originalFile = common.Bookmark(window, "originalFile")

		threading.Thread.__init__(self)  


	def run(self):
		view = self.window.active_view()

		bookmarkItems = common.createBookmarksPanelItems(self.bookmarks)
		self.window.show_quick_panel(bookmarkItems, self.Done_, sublime.MONOSPACE_FONT, 1, self.Highlighted_)


	def Done_(self, index):
		#first go back to the original file (from where removeBookmars was called from...)
		self.originalFile.Goto(self.window, True)

		if index < 0:			
			common.gLog("Cancelled")
		else:
			
			#delete the bookmark
			del self.bookmarks[index]
			
			global gPersist
			#update the global bookmarks list
			common.gPersist.setBookmarks(self.bookmarks)
			common.updateGutter(self.window.active_view())

			common.gLog("Removed Bookmark")

		

	def Highlighted_(self, index):
		self.GotoBookmark_(index)


	def GotoBookmark_(self, index):
		selectedBookmark = self.bookmarks[index]
		selectedBookmark.Goto(self.window, False)
