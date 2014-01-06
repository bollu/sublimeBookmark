import sublime
import sublime_plugin
import threading 
import os.path
from itertools import islice
from pickle import dump, load
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

def markBuffer(view, bookmark):
	uid = bookmark.getUid()
	region  = bookmark.getRegion()
	view.add_regions(str(uid), [region], "text.plain", "bookmark", sublime.DRAW_NO_FILL)

def unmarkBuffer(view, bookmark):
	uid = bookmark.getUid()
	view.erase_regions(str(uid))

#Bookmark manipulation------------
def genUid(count):
	return REGION_BASE_TAG + str(count)
	

def serealizeBookmark(bookmark):
	uID = str(bookmark.getUid())
	name = bookmark.getName()
	filePath = bookmark.getFilePath()
	regionBegin = str(bookmark.getRegion().a)
	regionEnd = str(bookmark.getRegion().b)
	lineNumber = str(bookmark.getLineNumber())
	lineStr = str(bookmark.getLineStr())

	return  uID + "\n" + name + "\n" + filePath + "\n" + regionBegin + "\n" + regionEnd + "\n" + lineNumber + "\n" + lineStr


def deserealizeBookmark(string):
	lines = string.splitlines()

	uID = int(lines[0].strip())
	name = str(lines[1].strip())
	filePath = str(lines[2])
	
	regionBegin = int(lines[3].strip())
	regionEnd =  int(lines[4].strip())
	lineNumber = int(lines[5].strip())
	lineStr = str(lines[6].strip())

	region = sublime.Region(regionBegin, regionEnd)

	return Bookmark(uID, name, filePath, region, lineNumber, lineStr)

def readBookmarkString(file):
	lines = []

	for x in range(0, 7):
		lines.append(file.readline())

	return lines

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

	def getLineNumber(self):
		return self.lineNumber

	def getLineStr(self):
		return self.lineStr

	

	def setLineStr(self, newLineStr):
		self.lineStr = newLineStr

	def setRegion(self, region):
		self.region = region

class SublimeBookmarkCommand(sublime_plugin.ApplicationCommand):
	def __init__(self):
		self.bookmarks = []
		self.thread = None
		self.uid = 0
		#bookmark that represents the file from which the panel was activated
		self.revertBookmark = None

		#File IO here!
		currentDir = os.path.dirname(os.path.realpath(__file__))
		print(currentDir)
		self.SAVE_PATH = currentDir + '/sublimeBookmarks.pickle'
		self._Load()

	def run(self, type):
		if type == "add":
			self._addBookmark()

		elif type == "goto":
			self._gotoBookmark()

		elif type == "remove":
			self._removeBookmark()

		elif type == "remove_all":
			self._removeAllBookmarks()

		elif type == "unmark_buffer":
			self._unmarkBuffer()

		elif type == "mark_buffer":
			self._markBuffer()

		elif type == "save_data":
			self._Save();

		elif type == "move_bookmarks":
			self._MoveBookmarks();

	#event handlers----------------------------
	def _addBookmark(self):
		print ("add")
		input = OptionsInput(sublime.active_window(), "Add Bookmark", "", self._AddBookmarkCallback, None)
		input.start()

	def _gotoBookmark(self):
		window = sublime.active_window()

		self.revertBookmark = self._createRevertBookmark(window.active_view())
		
		bookmarkItems = createBookmarkPanelItems(window, self.bookmarks)
		selector = OptionsSelector(window, bookmarkItems, self._HilightDoneCallback, self._AutoMoveToBookmarkCallback)
		selector.start()


	def _removeBookmark(self):
		window = sublime.active_window()

		self.revertBookmark = self._createRevertBookmark(window.active_view())
		
		bookmarkItems = createBookmarkPanelItems(window, self.bookmarks)
		selector = OptionsSelector(window, bookmarkItems, self._RemoveDoneCallback, self._AutoMoveToBookmarkCallback)
		selector.start()


	def _removeAllBookmarks(self):
		window = sublime.active_window()
		view = window.active_view()
		filePath = view.file_name()

		for bookmark in self.bookmarks:
			#unmark all bookmarks that are currently visible for immediate feedback
			if bookmark.getFilePath() == filePath:
				unmarkBuffer(view, bookmark)

		del self.bookmarks
		self.bookmarks = []	

	def _unmarkBuffer(self):
		print("unmarking buffer")
		window = sublime.active_window()
		view = window.active_view()
		filePath = view.file_name()
		
		for bookmark in self.bookmarks:
			if bookmark.getFilePath() == filePath:
				unmarkBuffer(view, bookmark)

	def _markBuffer(self):
		print("marking buffer")
		window = sublime.active_window()
		view = window.active_view()
		filePath = view.file_name()
		
		for bookmark in self.bookmarks:
			if bookmark.getFilePath() == filePath:
				markBuffer(view, bookmark)
			else:
				unmarkBuffer(view, bookmark)

	def _MoveBookmarks(self):
		print("marking buffer")
		window = sublime.active_window()
		view = window.active_view()
		filePath = view.file_name()
		
		for bookmark in self.bookmarks:
			if bookmark.getFilePath() == filePath:
				uid = bookmark.getUid()
				#load the new region and set the bookmark's region again
				newRegion = view.get_regions(str(uid))[0]
				newLineStr = view.substr(newRegion) 

				assert newRegion is not None
				bookmark.setRegion(newRegion)
				bookmark.setLineStr(newLineStr)
				#re-mark the buffer
				markBuffer(view, bookmark)
					
	#helpers-------------------------------------------

	def _createRevertBookmark(self, activeView):
		name = ""
		filePath = activeView.file_name()
		uID = -1

		region = getCurrentLineRegion(activeView)
		lineStr = ""
		lineNumber = activeView.rowcol(activeView.sel()[0].begin())[0]

		return Bookmark(uID, name, filePath, region, lineNumber, lineStr)

	#callbacks---------------------------------------------------
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
		markBuffer(view, bookmark)
		print(serealizeBookmark(deserealizeBookmark(serealizeBookmark(bookmark))))
		
		#File IO Here!
		self._Save()

	def _AutoMoveToBookmarkCallback(self, index):
		assert index < len(self.bookmarks)
		bookmark = self.bookmarks[index]
		assert bookmark is not None

		gotoBookmark(bookmark, sublime.active_window())
		self._markBuffer()
	
	def _HilightDoneCallback(self, index):
		if index == -1:
			print ("cancelled")
			
			assert self.revertBookmark is not None
			gotoBookmark(self.revertBookmark, sublime.active_window())
			
		self.revertBookmark = None
		self._markBuffer()

	def _RemoveDoneCallback(self, index):
		if index == -1:
			print ("cancelled")
			
			assert self.revertBookmark is not None
			gotoBookmark(self.revertBookmark, sublime.active_window())
			return
		else:
			assert index < len(self.bookmarks)

			#remove the mark from the bookmark
			window = sublime.active_window()
			bookmark = self.bookmarks[index]
			assert bookmark is not None

			gotoBookmark(bookmark, window)
			unmarkBuffer(window.active_view(), bookmark)
			
			del self.bookmarks[index]

		self.revertBookmark = None
		self._markBuffer()

		#File IO Here!
		self._Save()


	#Save-Load----------------------------------------------------------------
	def _Load(self):
		print("loading")

		try:
			savefile = open(self.SAVE_PATH, "rb")

			self.uid = load(savefile)
			self.bookmarks = load(savefile)
			
		
		except (OSError, IOError) as e:
			print (e)
		
		#now mark the buffer
		#self._markBuffer()


	def _Save(self):
		print ("saving")

		try:
			savefile = open(self.SAVE_PATH, "wb")
			dump(self.uid, savefile)
			dump(self.bookmarks, savefile)

		except (OSError, IOError) as e:
			print (e)
