import sublime, sublime_plugin
from pickle import dump, load
import threading 

from . import common

class RemoveAllBookmarksCommand(sublime_plugin.WindowCommand):
	def run(self):
	
		for bookmark in common.gBookmarks:
			bookmark.Remove()
		
		emptyBookmarks = []
		common.setBookmarks(emptyBookmarks)
		common.updateGutter(self.window.active_view())


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
		self.bookmarks = common.getBookmarks()

		self.originalFile = common.Bookmark(window, "originalFile")

		threading.Thread.__init__(self)  


	def run(self):
		view = self.window.active_view()

		bookmarkItems = common.createBookmarksPanelItems(self.window, self.bookmarks)
		self.window.show_quick_panel(bookmarkItems, self.Done_, sublime.MONOSPACE_FONT, 1, self.Highlighted_)


	def Done_(self, index):
		#first go back to the original file (from where removeBookmars was called from...)
		self.originalFile.Goto(self.window, True)

		if index < 0:			
			common.gLog("Canceled Remove Bookmark")
		else:
			
			#delete the bookmark in my personal index
			self.bookmarks[index].Remove()
			del self.bookmarks[index]

			#update the global bookmarks list
			common.setBookmarks(self.bookmarks)
			common.updateGutter(self.window.active_view())

			common.gLog("Removed Bookmark")

		

	def Highlighted_(self, index):
		self.GotoBookmark_(index)


	def GotoBookmark_(self, index):
		selectedBookmark = self.bookmarks[index]
		selectedBookmark.Goto(self.window, False)
