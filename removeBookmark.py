import sublime, sublime_plugin
import threading 

from . import common

class RemoveAllBookmarksCommand(sublime_plugin.ApplicationCommand, common.BaseBookmarkCommand):
	def __init__(self):
		self.window = sublime.active_window()
		common.BaseBookmarkCommand.__init__(self, self.window)
		

	def run(self):
		self.window = sublime.active_window()
		#disable bookmark filters to access *all* bookmarks
		for bookmark in common.get_bookmarks(self.window, False):
			bookmark.remove(self.window)
		
		emptyBookmarks = []
		common.set_bookmarks(emptyBookmarks, self.window)

	def description(self):
		return "Remove **all** Bookmarks. Be careful!"

class RemoveBookmarkCommand(sublime_plugin.ApplicationCommand, common.BaseBookmarkCommand):
	def __init__(self):
		self.window = sublime.active_window()
		self.thread = None
		common.BaseBookmarkCommand.__init__(self, self.window)

	def run(self):
		self.window = sublime.active_window()

		if self.thread is not None:
			self.thread.join()

		self._load() 

		if not self.bookmarks:
			sublime.status_message("no bookmarks to goto!")
			return 0

		self.thread = RemoveBookmarkHandler(self.window)
		self.thread.start()

		
	def description(self):
		return "Remove an added Bookmark"



class RemoveBookmarkHandler(threading.Thread):
	def __init__(self, window):
		self.originalFile = common.Bookmark(window, "originalFile", visible=False)

		self.window = window
		self.bookmarks = common.get_bookmarks(self.window)


		threading.Thread.__init__(self)  


	def run(self):
		view = self.window.active_view()

		bookmarkItems = common.create_bookmarks_panel_items(self.window, self.bookmarks)
		self.window.show_quick_panel(bookmarkItems, self._done, sublime.MONOSPACE_FONT, 1, self._highlighted)


	def _done(self, index):

		if index == -1:			
			common.g_log("Canceled remove Bookmark")
			self.originalFile.goto(self.window, True)
		else:
			
			#first go back to the original file (from where removeBookmars was called from...)
			self.originalFile.goto(self.window, True)

			#delete the bookmark in my personal index
			self.bookmarks[index].remove(self.window)
			del self.bookmarks[index]

			#update the global bookmarks list
			common.set_bookmarks(self.bookmarks, self.window)
			
			common.g_log("Removed Bookmark")

		
	def _highlighted(self, index):
		self._goto_bookmark(index)


	def _goto_bookmark(self, index):
		selectedBookmark = self.bookmarks[index]
		selectedBookmark.goto(self.window, False)
