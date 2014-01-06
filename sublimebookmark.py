import sublime
import sublime_plugin
import threading 

REGION_BASE_TAG = "__SublimeBookmark__"

class OptionsSelector(threading.Thread):
	def __init__(self, window, panelItems, onDone, onHighlight):
		self.window = window
		self.panelItems = panelItems
		self.onDone = onDone
		self.onHighlight = onHighlight

		threading.Thread.__init__(self)

	def run(self):
		view = self.window.active_view()
		self.window.show_quick_panel(self.panelItems, self.onDone, 0, -1, self.onHighlight)

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

#Bookmark manipulation------------
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

def gotoBookmark(bookmark, window):
	filePath = bookmark.getFilePath()
	lineNumber = bookmark.getLineNumber()

	view = window.open_file(filePath, sublime.TRANSIENT)
	view.show_at_center(bookmark.getRegion())

#Menu generation---------
def ellipsisStringEnd(string, length):
	#I have NO idea why the hell this would happen. But it's happening.
	if string is None:
		return ""
	else:
		return string if len(string) <= length else string[ 0 : length - 3] + '...'


def ellipsisStringBegin(string, length):
	if string is None:
		return ""
	else:	
		return string if len(string) <= length else '...' + string[ len(string) + 3 - (length)  : len(string) ] 

def createBookmarkPanelItems(window, bookmarks):	
	bookmarkItems = []

	for bookmark in bookmarks:

		bookmarkName = bookmark.getName()
		bookmarkLine = ellipsisStringEnd(bookmark.getLineStr(), 55)
		bookmarkFile = ellipsisStringBegin(bookmark.getFilePath(), 55)

		bookmarkItems.append( [bookmarkName, bookmarkLine, bookmarkFile] )

	return bookmarkItems



#Bookmark-----------
class Bookmark:
	def __init__(self, uid, name, filePath, region, lineNumber, lineStr):
		self.uid = int(uid)
		self.name = str(name)
		self.region = region
		self.filePath = str(filePath)
		self.lineStr = str(lineStr)
		self.lineNumber = int(lineNumber)

	def getName(self):
		return self.name

	def getUid(self):
		return self.uid

	def getRegion(self):
		return self.region

	def getFilePath(self):
		return self.filePath

	def getLineStr(self):
		return self.lineStr

	def getLineNumber(self):
		return self.lineNumber

	def setLine(self, lineStr, lineNumber):
		self.lineStr = lineStrs
		self.lineNumber = lineNumber



class SublimeBookmarkCommand(sublime_plugin.ApplicationCommand):
	def __init__(self):
		self.bookmarks = []
		self.thread = None
		self.uid = 0
		#bookmark that represents the original file
		self.revertBookmark = None

	def run(self, type):
		if type == "add":
			self._addBookmark()

		elif type == "goto":
			self._gotoBookmark()

		elif type == "remove":
			self._removeBookmark()

		elif type == "remove_all":
			self._removeAllBookmarks()


	#event handlers------------
	def _addBookmark(self):
		print ("add")
		input = OptionsInput(sublime.active_window(), "Add Bookmark", "", self._AddBookmarkCallback, None)
		input.start()

	def _gotoBookmark(self):
		print ("goto")
		window = sublime.active_window()

		self.revertBookmark = self._createRevertBookmark(window.active_view())
		
		bookmarkItems = createBookmarkPanelItems(window, self.bookmarks)
		#both onDone and onHighlight do the same thing...
		selector = OptionsSelector(window, bookmarkItems, self._HilightDoneCallback, self._AutoMoveToBookmarkCallback)
		selector.start()


	def _removeBookmark(self):
		print ("remove")
		pass

	def _removeAllBookmarks(self):
		print ("remove_all")
		pass

	#helpers-------------------------
	def _hilightBookmarks(self, activeView):
		pass

	def _createRevertBookmark(self, activeView):
		name = ""
		filePath = activeView.file_name()
		uID = -1

		region = getCurrentLineRegion(activeView)
		lineStr = ""
		lineNumber = activeView.rowcol(activeView.sel()[0].begin())[0]

		return Bookmark(uID, name, filePath, region, lineNumber, lineStr)

	#callbacks-----------------------
	def _AddBookmarkCallback(self, name):
		view = sublime.active_window().active_view()
		filePath = view.file_name()
		uID = self.uid
		self.uid = self.uid + 1

		region = getCurrentLineRegion(view)
		lineStr = view.substr(region)
		lineNumber = view.rowcol(view.sel()[0].begin())[0]


		bookmark = Bookmark(uID, name, filePath, region, lineNumber, lineStr)
		self.bookmarks.append(bookmark)
		markBuffer(view, uID, region)
		print(serealizeBookmark(deserealizeBookmark(serealizeBookmark(bookmark))))


	def _AutoMoveToBookmarkCallback(self, index):
	
		assert index < len(self.bookmarks)
		bookmark = self.bookmarks[index]
		assert bookmark is not None

		gotoBookmark(bookmark, sublime.active_window())
	
	def _HilightDoneCallback(self, index):
		if index == -1:
			print ("cancelled")
			
			assert self.revertBookmark is not None
			gotoBookmark(self.revertBookmark, sublime.active_window())

			self._hilightBookmarks(view)
		
		
		self.revertBookmark = None

