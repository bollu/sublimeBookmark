import sublime
import sublime_plugin
import threading 

REGION_BASE_TAG = "__SublimeBookmark__"

class OptionsSelector(threading.Thread):
	def __init__(self, window, panelItems, onSelect, onHighlight):
		self.window = window
		self.panelItems = panelItems
		self.onSelect = onSelect
		self.onHighlight = onHighlight

		threading.Thread.__init__(self)

	def run(self):
		view = self.window.active_view()
		self.window.show_quick_panel(self.panelItems, self.onSelect, 0, -1, self.onHighlight)

class OptionsInput(threading.Thread):
	def __init__(self, window, caption, initalText, onDone, onCancel):
		self.window = window
		self.caption = caption
		self.initalText = initalText
		self.onDone = onDone
		self.onCancel = onCancel

		threading.Thread.__init__(self)

	def run(self):
		view = self.window.active_view()
		self.window.show_input_panel(self.caption, self.initalText, self.onDone, None, self.onCancel)

#helper functions--------------------------------
#Region manipulation-----
def getCurrentLineRegion(view):
	(row, col) = view.rowcol(view.sel()[0].begin())
	pt = view.text_point(row, col)
	region =  view.line(pt)

	return region 

def markBuffer(view, uid, region):
	view.add_regions(str(uid), [region], "text.plain", "bookmark", sublime.DRAW_NO_FILL)

def unmarkBuffer(view, uid):
	view.erase_regions(uid)

#Bookmark manipulation---
def genUid(count):
	return REGION_BASE_TAG + str(count)

def serealizeBookmark(bookmark):
	regionBegin = str(bookmark.getRegion().a)
	regionEnd = str(bookmark.getRegion().b)
	uID = str(bookmark.getUid())
	name = bookmark.getName()
	filePath = bookmark.getFilePath()
	return filePath + "\n" + name + "\n" + regionBegin + "\n" + regionEnd + "\n" + uID + "\n" 

def deserealizeBookmark(string):
	lines = string.splitlines()

	filePath = str(lines[0])
	name = str(lines[1].strip())
	regionBegin = int(lines[2].strip())
	regionEnd =  int(lines[3].strip())
	uID = int(lines[4].strip())
	

	region = sublime.Region(regionBegin, regionEnd)

	return Bookmark(uID, name, filePath, region)

#Bookmark-----------
class Bookmark:
	def __init__(self, uid, name, filePath, region):
		self.uid = uid
		self.name = name
		self.region = region
		self.filePath = filePath

	def getName(self):
		return self.name

	def getUid(self):
		return self.uid

	def getRegion(self):
		return self.region

	def getFilePath(self):
		return self.filePath



class SublimeBookmarkCommand(sublime_plugin.ApplicationCommand):
	def __init__(self):
		self.bookmarks = []
		self.thread = None
		self.uid = 0

	def run(self, type):
		if type == "add":
			self._addBookmark()

		elif type == "goto":
			self._gotoBookmark()

		elif type == "remove":
			self._removeBookmark()

		elif type == "remove_all":
			self._removeAllBookmarks()


	#event handlers-----
	def _addBookmark(self):
		print ("add")
		input = OptionsInput(sublime.active_window(), "Add Bookmark", "", self._AddBookmarkCallback, None)
		input.start()

	def _gotoBookmark(self):
		print ("goto")
		pass

	def _removeBookmark(self):
		print ("remove")
		pass

	def _removeAllBookmarks(self):
		print ("remove_all")
		pass

	#callbacks----
	def _AddBookmarkCallback(self, name):
		view = sublime.active_window().active_view()
		filePath = view.file_name()
		uID = self.uid
		self.uid = self.uid + 1

		region = getCurrentLineRegion(view)

		bookmark = Bookmark(uID, name, filePath, region)
		markBuffer(view, uID, region)
		print(serealizeBookmark(deserealizeBookmark(serealizeBookmark(bookmark))))


	def _AutoMoveToCallback(self, index):