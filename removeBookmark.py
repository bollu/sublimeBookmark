import sublime, sublime_plugin
import threading 

from . import common

class RemoveAllBookmarksCommand(sublime_plugin.WindowCommand, common.BaseBookmarkCommand):
	def __init__(self, window):
		common.BaseBookmarkCommand.__init__(self, window)

	def run(self):
		for bookmark in common.get_bookmarks():
			bookmark.remove()
		
		emptyBookmarks = []
		common.set_bookmarks(emptyBookmarks)


class RemoveBookmarkCommand(sublime_plugin.WindowCommand, common.BaseBookmarkCommand):
	def __init__(self, window):
		self.thread = None
		common.BaseBookmarkCommand.__init__(self, window)

	def run(self):
		if self.thread is not None:
			self.thread.join()

		self._load() 

		if not self.bookmarks:
			sublime.status_message("no bookmarks to goto!")
			return 0

		self.thread = RemoveBookmarkHandler(self.window)
		self.thread.start()

		
class RemoveBookmarkHandler(threading.Thread):
	def __init__(self, window):
		self.window = window
		self.bookmarks = common.get_bookmarks()

		self.originalFile = common.Bookmark(window, "originalFile")

		threading.Thread.__init__(self)  


	def run(self):
		view = self.window.active_view()

		bookmarkItems = common.create_bookmarks_panel_items(self.window, self.bookmarks)
		self.window.show_quick_panel(bookmarkItems, self._done, sublime.MONOSPACE_FONT, 1, self._highlighted)


	def _done(self, index):
		#first go back to the original file (from where removeBookmars was called from...)
		self.originalFile.goto(self.window, True)

		if index < 0:			
			common.g_log("Canceled remove Bookmark")
		else:
			
			#delete the bookmark in my personal index
			self.bookmarks[index].remove()
			del self.bookmarks[index]

			#update the global bookmarks list
			common.set_bookmarks(self.bookmarks)

			common.g_log("Removed Bookmark")


	def _highlighted(self, index):
		self._goto_bookmark(index)


	def _goto_bookmark(self, index):
		selectedBookmark = self.bookmarks[index]
		selectedBookmark.goto(self.window, False)
