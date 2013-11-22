import sublime, sublime_plugin
from pickle import dump, load
import threading 

from . import common


class GotoBookmarkCommand(sublime_plugin.WindowCommand, common.baseBookmarkCommand):
	def __init__(self, window):
		self.thread = None
		common.baseBookmarkCommand.__init__(self, window)


	def run(self):
		if self.thread is not None:
			self.thread.join()

		self.load_()

		if len(self.bookmarks) == 0:
			sublime.status_message("no bookmarks to goto!")
			return 0
			
		self.thread = GotoBookmarkHandler(self.window, self)
		self.thread.start()


class GotoBookmarkHandler(threading.Thread):
	def __init__(self, window, BookmarkCommand):
		self.window = window
		
		global gPersist
		self.bookmarks = common.getBookmarks() 
		self.originalFile = common.Bookmark(window, "originalFile")

		threading.Thread.__init__(self)  


	def run(self):
		view = self.window.active_view()

		bookmarkItems = common.createBookmarksPanelItems(self.window, self.bookmarks)


		# bookmarkNames = []
		# for bookmark in self.bookmarks:
		# 	bookmarkNames.append(bookmark.getName())
		
		#view = self.window.create_output_panel("Goto Bookmark")

		self.window.show_quick_panel(bookmarkItems, self.Done_, 0, -1, self.Highlighted_)
		

	def Done_(self, index):

		if index == -1:
			#if cancelled, go back to original file
			self.originalFile.Goto(self.window, False)
			common.gLog("Cancelled goto")
		else:
			self.GotoBookmark_(index)
			common.gLog("Done with goto")

	def Highlighted_(self, index):
		self.GotoBookmark_(index)


	def GotoBookmark_(self, index):
		selectedBookmark = self.bookmarks[index]
		selectedBookmark.Goto(self.window, False)

	

	def Items_(self):
		bookmarkItems = []

		for bookmark in self.bookmarks:
			bookmarkName = bookmark.getName()
			bookmarkLine = capStringEnd(bookmark.getLine(), 50)
			bookmarkFile = capStringBegin(bookmark.getFilePath(), 50)

			bookmarkItems.append( [bookmarkName, bookmarkLine, bookmarkFile] )

		return bookmarkItems