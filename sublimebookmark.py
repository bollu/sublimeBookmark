import sublime
import sublime_plugin
import threading 
import os.path
from itertools import islice
from pickle import dump, load
from copy import deepcopy

REGION_BASE_TAG = "__SublimeBookmark__"
SETTINGS_NAME = "SublimeBookmarks.sublime-settings"
#if someone names their project this, we're boned
NO_PROJECT = "___NO_PROJECT_PRESENT____"

BOOKMARKS = []

#list of bookmarks that have ben deleted. 
#This is used to remove bookmarks' buffer highlights. Without this, if a bookmark is removed,
#when a file is revisited, the buffer will still be marked. This will keep track of bookmarks
#that have been removed.
ERASED_BOOKMARKS = []

#whether all bookmarks (even unrelated) should be shown
SHOW_ALL_BOOKMARKS = True

class OptionsSelector(threading.Thread):
	def __init__(self, window, panelItems, onDone, onHighlight):
		self.window = window
		self.panelItems = panelItems
		self.onDone = onDone
		self.onHighlight = onHighlight

		threading.Thread.__init__(self)

	def run(self):
		view = self.window.active_view()
		startIndex = 0
		
		self.window.show_quick_panel(self.panelItems, self.onDone, startIndex, 0, self.onHighlight)

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
#Region manipulation-----------------------------
def getCurrentLineRegion(view):
	(row, col) = view.rowcol(view.sel()[0].begin())
	pt = view.text_point(row, col)
	region =  view.full_line(pt)

	return region 

def markBuffer(view, bookmark):
	uid = bookmark.getUid()
	region  = bookmark.getRegion()
	view.add_regions(str(uid), [region], "text.plain", "bookmark", sublime.DRAW_NO_FILL | sublime.DRAW_EMPTY_AS_OVERWRITE)

def unmarkBuffer(view, bookmark):
	uid = bookmark.getUid()
	view.erase_regions(str(uid))

#Bookmark manipulation---------------------
def genUid(count):
	return REGION_BASE_TAG + str(count)
	

def gotoBookmark(bookmark, window):
	filePath = bookmark.getFilePath()
	lineNumber = bookmark.getLineNumber()

	rowCol = ":" + str(0) + ":" + str(lineNumber)

	view = window.open_file(filePath + rowCol, sublime.TRANSIENT | sublime.ENCODED_POSITION)
	view.show_at_center(bookmark.getRegion())

	#move cursor to given position
	view.sel().clear()
	view.sel().add(bookmark.getRegion())


def shouldShowBookmark(bookmark, window, showAllBookmarks):
	currentProjectPath = window.project_file_name()
	
	#free bookmarks can be shown. We don't need a criteria
	if showAllBookmarks:
		return True
	#there is no current project now. Show all bookmarks
	elif currentProjectPath == None or currentProjectPath == "":
		return True

	#return if the bookmark belongs to current project or not.
	else:
		return bookmark.getProjectPath() == currentProjectPath
#Menu generation-----------------------------------
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

def createBookmarkPanelItems(window, bookmarks, shouldShowAllBookmarks):	
	bookmarkItems = []
	
	for bookmark in bookmarks:
		if shouldShowBookmark(bookmark, window, shouldShowAllBookmarks):

			bookmarkName = bookmark.getName()
			bookmarkLine = ellipsisStringEnd(bookmark.getLineStr(), 55)
			bookmarkFile = ellipsisStringBegin(bookmark.getFilePath(), 55)

			bookmarkItems.append( [bookmarkName, bookmarkLine, bookmarkFile] )
		else:
			continue

	return bookmarkItems


def setStatus(statusMessage):
	sublime.status_message(statusMessage)


#Bookmark-----------
class Bookmark:
	def __init__(self, uid, name, filePath, projectPath, region, lineNumber, lineStr):
		self.uid = int(uid)
		self.name = str(name)
		self.region = region
		self.filePath = str(filePath)
		self.projectPath = str(projectPath)
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

	def getProjectPath(self):
		return self.projectPath

	def getLineNumber(self):
		return self.lineNumber

	def getLineStr(self):
		return self.lineStr

	

	def setLineStr(self, newLineStr):
		self.lineStr = newLineStr

	def setRegion(self, region):
		self.region = region

class SublimeBookmarkCommand(sublime_plugin.WindowCommand):
	def __init__(self, window):
		global BOOKMARKS

		self.window = window
		BOOKMARKS = []
		self.thread = None
		self.uid = 0
		#bookmark that represents the file from which the panel was activated
		self.revertBookmark = None

		currentDir = os.path.dirname(os.path.realpath(__file__))
		self.SAVE_PATH = currentDir + '/sublimeBookmarks.pickle'
		print(currentDir)

		self._Load()
		


	def run(self, type):
		settings = sublime.load_settings(SETTINGS_NAME)
		assert settings is not None
		#settings.add_on_change("always_show_free_bookmarks", self._LoadSettings())
		#settings.add_on_change("always_show_project_bookmarks", self._LoadSettings())
		global SHOW_ALL_BOOKMARKS

		if type == "add":
			self._addBookmark()

		elif type == "goto":
			self._gotoBookmark()

		elif type == "remove":
			self._removeBookmark()

		elif type == "show_all_bookmarks":
			SHOW_ALL_BOOKMARKS = True

		elif type == "show_project_bookmarks":
			SHOW_ALL_BOOKMARKS = False

		elif type == "remove_all":
			self._removeAllBookmarks()

		elif type == "mark_buffer":
			self._markBuffer()

		elif type == "move_bookmarks":
			self._MoveBookmarks();



	#event handlers----------------------------
	def _addBookmark(self):
		print ("add")
		input = OptionsInput(self.window, "Add Bookmark", "", self._AddBookmarkCallback, None)
		input.start()

	def _gotoBookmark(self):
		window = self.window
		#create a revert bookmark to go back if the user cancels
		self.revertBookmark = self._createRevertBookmark(window.active_view())

		#create a list of acceptable bookmarks based on settings
		bookmarkItems = createBookmarkPanelItems(window, BOOKMARKS, SHOW_ALL_BOOKMARKS)

		#if no bookmarks are acceptable, don't show bookmarks
		if len(bookmarkItems) == 0:
			return
		#create a selection panel and launch it
		selector = OptionsSelector(window, bookmarkItems, self._HilightDoneCallback, self._AutoMoveToBookmarkCallback)
		selector.start()


	def _removeBookmark(self):
		window = self.window

		#create a revert bookmark to go back if the user cancels
		self.revertBookmark = self._createRevertBookmark(window.active_view())
		
		#create a list of acceptable bookmarks based on settings
		bookmarkItems = createBookmarkPanelItems(window, BOOKMARKS, SHOW_ALL_BOOKMARKS)

		#if no bookmarks are acceptable, don't show bookmarks
		if len(bookmarkItems) == 0:
			return

		#create a selection panel and launch it
		selector = OptionsSelector(window, bookmarkItems, self._RemoveDoneCallback, self._AutoMoveToBookmarkCallback)
		selector.start()


	def _removeAllBookmarks(self):
		window = self.window
		view = window.active_view()
		filePath = view.file_name()

		global BOOKMARKS
		global ERASED_BOOKMARKS

		for bookmark in BOOKMARKS:
			#store erased bookmarks for delayed removal
			ERASED_BOOKMARKS.append(deepcopy(bookmark))
			#unmark all bookmarks that are currently visible for immediate feedback
			if bookmark.getFilePath() == filePath:
				unmarkBuffer(view, bookmark)

		#yep. nuke em
		del BOOKMARKS
		BOOKMARKS = []	

		#save to eternal storage
		self._Save()

	def _markBuffer(self):
		print ("MARKING BUFFER")

		window = self.window
		view = window.active_view()
		filePath = view.file_name()
		
		#mark all bookmarks that are visible
		for bookmark in BOOKMARKS:
			shouldShow = shouldShowBookmark(bookmark, window, SHOW_ALL_BOOKMARKS)

			if bookmark.getFilePath() == filePath and shouldShow:
				markBuffer(view, bookmark)
			
		#unmark all erased bookmarks
		for bookmark in ERASED_BOOKMARKS:
			if bookmark.getFilePath() == filePath:
				unmarkBuffer(view, bookmark)

	def _MoveBookmarks(self):
		window = self.window
		view = window.active_view()
		filePath = view.file_name()
		
		global BOOKMARKS

		for bookmark in BOOKMARKS:
			#this bookmark (might) have been changed. We're on a thread anyway so update it.
			if bookmark.getFilePath() == filePath:
				uid = bookmark.getUid()
				#load the new region and set the bookmark's region again
				regions = view.get_regions(str(uid))

				#there is no region in the view
				if len(regions) == 0:
					return

				newRegion = view.get_regions(str(uid))[0]
				newLineStr = view.substr(newRegion) 

				assert newRegion is not None
				bookmark.setRegion(newRegion)
				bookmark.setLineStr(newLineStr)

				#re-mark the buffer. This automagically clears the previous mark
				markBuffer(view, bookmark)
					
	#helpers-------------------------------------------

	def _createRevertBookmark(self, activeView):
		name = ""
		filePath = activeView.file_name()
		projectPath = ""
		uID = -1

		region = getCurrentLineRegion(activeView)
		lineStr = ""
		lineNumber = activeView.rowcol(activeView.sel()[0].begin())[0]

		return Bookmark(uID, name, filePath, projectPath, region, lineNumber, lineStr)

	#callbacks---------------------------------------------------
	def _AddBookmarkCallback(self, name):
		window = self.window
		view = window.active_view()
		filePath = view.file_name()

		#figure out the project path
		projectPath = window.project_file_name()
		if projectPath is None or projectPath is "":
			projectPath = NO_PROJECT

		#set the uID and increment it
		uID = self.uid
		self.uid = self.uid + 1

		#get region and line data
		region = getCurrentLineRegion(view)
		lineStr = view.substr(region)
		lineNumber = view.rowcol(view.sel()[0].begin())[0]

		#create a bookmark and add it to the global list
		global BOOKMARKS

		bookmark = Bookmark(uID, name, filePath, projectPath, region, lineNumber, lineStr)
		BOOKMARKS.append(bookmark)

		markBuffer(view, bookmark)
		
		#File IO Here!--------------------
		self._Save()

	#display highlighted bookmark
	def _AutoMoveToBookmarkCallback(self, index):
		assert index < len(BOOKMARKS)
		bookmark = BOOKMARKS[index]
		assert bookmark is not None

		#goto highlighted bookmark
		gotoBookmark(bookmark, self.window)
		self._markBuffer()
	
	#if the user cancelled, go back to the original file
	def _HilightDoneCallback(self, index):
		if index == -1:
			assert self.revertBookmark is not None
			gotoBookmark(self.revertBookmark, self.window)
			
		self.revertBookmark = None
		self._markBuffer()

	#remove the selected bookmark or go back if user cancelled
	def _RemoveDoneCallback(self, index):
		if index == -1:
			assert self.revertBookmark is not None
			gotoBookmark(self.revertBookmark, self.window)
			return
		else:

			global BOOKMARKS
			global ERASED_BOOKMARKS

			assert index < len(BOOKMARKS)

			#remove the mark from the bookmark
			window = self.window
			bookmark = BOOKMARKS[index]
			assert bookmark is not None

			gotoBookmark(bookmark, window)
			unmarkBuffer(window.active_view(), bookmark)
			
			#add to list of erased bookmarks
			ERASED_BOOKMARKS.append(deepcopy(bookmark))
			del BOOKMARKS[index]

		self.revertBookmark = None
		self._markBuffer()

		#File IO Here!--------------------
		self._Save()


	#Save-Load----------------------------------------------------------------
	def _Load(self):
		global BOOKMARKS

		print("LOADING BOOKMARKS")
		try:
			savefile = open(self.SAVE_PATH, "rb")

			self.uid = load(savefile)
			BOOKMARKS = load(savefile)
	
		except (OSError, IOError) as e:
			print (e)
		
		#now mark the buffer
		#self._markBuffer()


	def _Save(self):
		global BOOKMARKS
		print("SAVING BOOKMARKS")

		try:
			savefile = open(self.SAVE_PATH, "wb")

			dump(self.uid, savefile)
			dump(BOOKMARKS, savefile)
			savefile.close()
		except (OSError, IOError) as e:
			print (e)


	def _LoadSettings(self):
		
		#not a fan of hardcoding this
		settings = sublime.load_settings(SETTINGS_NAME)
		assert settings is not None

		#self.showFreeBookmarks = settings.get("always_show_free_bookmarks", True)
		#self.showProjectBookmarks = settings.get("always_show_project_bookmarks", True)

		#assert self.showFreeBookmarks is not None
		#assert self.showProjectBookmarks is not None

