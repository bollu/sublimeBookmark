import sublime
import sublime_plugin
import threading 
import os.path
from pickle import dump, load, UnpicklingError, PicklingError
from copy import deepcopy

def Log(string):
	if False:
		print (string)


REGION_BASE_TAG = int(11001001000011111101)
SETTINGS_NAME = "SublimeBookmarks.sublime-settings"
#if someone names their project this, we're boned
NO_PROJECT = "___NO_PROJECT_PRESENT____"

BOOKMARKS = []
UID = None

#list of bookmarks that have ben deleted. 
#This is used to remove bookmarks' buffer highlights. Without this, if a bookmark is removed,
#when a file is revisited, the buffer will still be marked. This will keep track of bookmarks
#that have been removed.
ERASED_BOOKMARKS = []
  


#whether all bookmarks (even unrelated) should be shown
def SHOW_ALL_BOOKMARKS():
	return "Show All Bookmarks"

def SHOW_ONLY_PROJECT_BOOKMARKS():
	return "Show Only Project Bookmarks"

def SHOW_ONLY_FILE_BOOKMARKS():
	return "Show Only File Bookmarks"

BOOKMARKS_MODE = SHOW_ALL_BOOKMARKS()

class OptionsSelector:
	def __init__(self, window, panelItems, onDone, onHighlight):
		self.window = window
		self.panelItems = deepcopy(panelItems)
		self.onDone = onDone
		self.onHighlight = onHighlight
		
	def start(self):
		startIndex = 0
		self.window.show_quick_panel(self.panelItems, self.onDone, 0, startIndex, self.onHighlight)

class OptionsInput:
	def __init__(self, window, caption, initalText, onDone, onCancel):
		self.window = window
		self.caption = caption
		self.initalText = initalText
		self.onDone = onDone
		self.onCancel = onCancel

		
	def start(self):
		view = self.window.active_view()
		inputPanelView = self.window.show_input_panel(self.caption, self.initalText, self.onDone, None, self.onCancel)

		#select the text in the view so that when the user types a new name, the old name
		#is overwritten
		assert (len(inputPanelView.sel()) > 0)
		selectionRegion = inputPanelView.full_line(inputPanelView.sel()[0])
		inputPanelView.sel().add(selectionRegion)
	
#helper functions--------------------------------
#Region manipulation-----------------------------
def getCurrentLineRegion(view):
	assert (len(view.sel()) > 0)
	selectedRegion = view.sel()[0]
	region =  view.line(selectedRegion)

	return region 

#Bookmark manipulation---------------------

def moveViewToGroup(window, view, group):
	(viewGroup, viewIndex) = window.get_view_index(view) 


	#the view is not in the required group so move it
	#we have to move the view to the other group and give it a new index
	if group != viewGroup or viewGroup == -1 or viewIndex == -1:
		
		#SUBLIME_BUG
		#if the group the view is currently in has only one element - i.e  this view,
		#sublime text goes crazy and closes our options selector. So, we have to create
		#a new file in the old group and *only then* move the view.
		if len(window.views_in_group(viewGroup)) == 1:
			window.focus_group(viewGroup)
			window.new_file()


		#if there are 0 views, then the moved view will have index 0
		#similarly, if there are n views, the last view will have index (n-1), and
		#so the new view will have index n  
		newIndex = len (window.views_in_group(group))
		#move the view to the highlighted group and assign a
		#correct index
		window.set_view_index(view, group, newIndex)

	#the view is in the right group, so chill
	else:
		pass


def gotoBookmark(bookmark, window):
	filePath = bookmark.getFilePath()
	lineNumber = bookmark.getLineNumber()

	view = window.open_file(filePath)
	view.show_at_center(bookmark.getRegion())
		
	#move cursor to the middle of the bookmark's region
	bookmarkRegionMid = 0.5 * (bookmark.getRegion().begin() +  bookmark.getRegion().end())
	moveRegion = sublime.Region(bookmarkRegionMid, bookmarkRegionMid)
	view.sel().clear()
	view.sel().add(moveRegion)


def shouldShowBookmark(window, activeView, bookmark, bookmarkMode):
	#1)there is no current project now. Show all bookmarks
	#2)current project matches bookmark path
	def isValidProject(currentProjectPath, bookmarkProjectPath):
		return currentProjectPath ==  NO_PROJECT or currentProjectPath == bookmarkProjectPath

	currentFilePath = activeView.file_name()
	currentProjectPath = window.project_file_name() 

	#free bookmarks can be shown. We don't need a criteria
	if bookmarkMode == SHOW_ALL_BOOKMARKS():
		return True
	

	elif bookmarkMode == SHOW_ONLY_PROJECT_BOOKMARKS() and \
			isValidProject(currentProjectPath, bookmark.getProjectPath()):
		return True

	elif bookmarkMode == SHOW_ONLY_FILE_BOOKMARKS() and \
			bookmark.getFilePath() == currentFilePath:
			return True
	else:
		assert("Unknown Mode")
		return False

	return False


#Menu generation-----------------------------------
def filterBookmarks(bookmarks, window, activeView, bookmarkMode):
	filteredBookmarks = []
	for bookmark in bookmarks:
		if shouldShowBookmark(window, activeView, bookmark, bookmarkMode):
			filteredBookmarks.append(bookmark)

	return filteredBookmarks

def createBookmarkPanelItems(window, activeView, filteredBookmarks):	
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


	bookmarkItems = []
	for bookmark in filteredBookmarks:
			bookmarkName = bookmark.getName()

			bookmarkLine = bookmark.getLineStr().lstrip()
			bookmarkFile = ellipsisStringBegin(bookmark.getFilePath().lstrip(), 55)
			
			bookmarkItems.append( [bookmarkName, bookmarkLine, bookmarkFile] )
		

	return bookmarkItems


def showMessage(statusMessage):
	sublime.status_message(statusMessage)


#Bookmark-----------
class Bookmark:
	def __init__(self, uid, name, filePath, projectPath, region, group, lineNumber, lineStr):
		self.uid = int(uid)
		self.name = str(name)
		self.regionA = int(region.a)
		self.regionB = int(region.b)
		self.group = int(group)
		self.filePath = str(filePath)
		self.projectPath = str(projectPath)
		self.lineStr = str(lineStr)
		self.lineNumber = int(lineNumber)

	def getName(self):
		return self.name

	def getUid(self):
		return self.uid

	def getRegion(self):
		return sublime.Region(self.regionA, self.regionB)

	def getFilePath(self):
		return self.filePath

	def getProjectPath(self):
		return self.projectPath

	def getLineNumber(self):
		return self.lineNumber

	def getLineStr(self):
		return self.lineStr

	def getGroup(self):
		return self.group



	def setLineStr(self, newLineStr):
		self.lineStr = str(newLineStr)

	def setRegion(self, region):
		self.regionA = region.a
		self.regionB = region.b

	def setGroup(self, group):
		self.group = int(group)



class SublimeBookmarkCommand(sublime_plugin.WindowCommand):
	def __init__(self, window):
		global BOOKMARKS
		global UID 

		BOOKMARKS = []		
		#initialize to 0
		UID = 0

		self.window = window

		#the bookmark to go to if the user cancels
		self.revertBookmark = None
		self.activeGroup = 0
		
		#bookmarks that are being shown in the panel
		self.displayedBookmarks = None

		#bookmark that represents the file from which the panel was activated
		currentDir = os.path.dirname(sublime.packages_path())
		self.SAVE_PATH = currentDir + '/sublimeBookmarks.pickle'
		Log(currentDir)

		self._Load()

		self.global_bookmark_index = -1


	def run(self, type):
		global BOOKMARKS_MODE

		if type == "add":
			self._addBookmark(False)

		elif type == "goto":
			#on highlighting, goto the current bookmark
			#on option select, just center the selected item
			self._createBookmarkPanel(self._HilightDoneCallback, self._AutoMoveToBookmarkCallback)

		elif type == "goto_next":
			self._gotoNext(True);

		elif type == "goto_previous":
			self._gotoNext(False);

		elif type == "remove":
			#on highlighting, goto the current bookmark
			#on option select, remove the selected item
			self._createBookmarkPanel(self._RemoveDoneCallback, self._AutoMoveToBookmarkCallback)

		elif type == "remove_all":
			self._removeAllBookmarks()

		elif type == "toggle_line":
			self._toggleCurrentLine()

		elif type == "show_all_bookmarks":
			BOOKMARKS_MODE = SHOW_ALL_BOOKMARKS()
			self._Save()
			#update buffer to show all bookmarks
			self._updateBufferStatus()

		elif type == "show_project_bookmarks":
			BOOKMARKS_MODE = SHOW_ONLY_PROJECT_BOOKMARKS()
			self._Save()
			#update buffer to show only project bookmarks
			self._updateBufferStatus()

		elif type == "show_file_bookmarks":
			BOOKMARKS_MODE = SHOW_ONLY_FILE_BOOKMARKS()
			self._Save()
			#update buffer to show only project bookmarks
			self._updateBufferStatus()


		elif type == "mark_buffer":
			self._updateBufferStatus()

		elif type == "move_bookmarks":
			self._UpdateBookmarkPosition();

	def _getActiveBookmarks(self):
		window = self.window
		activeView = window.active_view()

		#create a list of acceptable bookmarks based on settings
		self.displayedBookmarks = filterBookmarks(BOOKMARKS, window, activeView, BOOKMARKS_MODE)

	def _createBookmarkPanel(self, onHighlight, onDone):

		def moveBookmarksToActiveGroup(activeGroup):	
			#move all open bookmark tabs to one group so that group switching does not
			#occur.
			views = window.views()
			for bookmark in BOOKMARKS:
				view = window.open_file(bookmark.getFilePath())
				#if the bookmark is already open, then move it to the active
				#group. If not, leave it alone, since it can be opened when need be.
				if view in views:
					moveViewToGroup(window, view, activeGroup)

		self._getActiveBookmarks();

		window = self.window
		activeView = window.active_view()
		self.activeGroup = self.window.active_group()


		#if no bookmarks are acceptable, don't show bookmarks
		if len(self.displayedBookmarks) == 0:
			sublime.status_message("SublimeBookmarks: NO ACCEPTABLE BOOKMARKS TO GOTO. CHECK CURRENT MODE")
			return

		bookmarkPanelItems = createBookmarkPanelItems(window, activeView, self.displayedBookmarks)

		#create a revert bookmark to go back if the user cancels
		self._createRevertBookmark(activeView)

		#update all bookmark positions that we have so that we know the
		#latest positions of all bookmarks
		self._UpdateBookmarkPosition()
		#move all active bookmarks to the currently active group
		moveBookmarksToActiveGroup(self.activeGroup)

		#create a selection panel and launch it
		selector = OptionsSelector(window, bookmarkPanelItems, onHighlight, onDone)
		selector.start()

	#event handlers----------------------------
	def _addBookmark(self, quick):
		Log ("add")

		window = self.window
		view = window.active_view()
		region = getCurrentLineRegion(view)

		#copy whatever is on the line for the bookmark name
		initialText = view.substr(region).strip()

		if quick:
			self._AddBookmarkCallback(initialText)
		else:
			input = OptionsInput(self.window, "Add Bookmark", initialText, self._AddBookmarkCallback, None)
			input.start()

	def _removeAllBookmarks(self):
		window = self.window
		view = window.active_view()
		filePath = view.file_name()

		global BOOKMARKS
		global ERASED_BOOKMARKS

		for bookmark in BOOKMARKS:
			#store erased bookmarks for delayed removal
			ERASED_BOOKMARKS.append(deepcopy(bookmark))
			
		#yep. nuke em
		del BOOKMARKS
		BOOKMARKS = []	

		#update the buffer since we deleted a bookmark
		self._updateBufferStatus()
		#save to eternal storage
		self._Save()

	def _toggleCurrentLine(self):
		def getLineBookmark(window):
			currentFilePath = window.active_view().file_name()
			cursorRegion = getCurrentLineRegion(window.active_view())

			for bookmark in BOOKMARKS:
				if bookmark.getFilePath() ==  currentFilePath and \
					bookmark.getRegion().contains(cursorRegion):
					return bookmark

			#no bookmark
			return None

		bookmark = getLineBookmark(self.window)

		if bookmark is not None:
			global ERASED_BOOKMARKS
			global BOOKMARKS

			#add to list of erased bookmarks
			ERASED_BOOKMARKS.append(deepcopy(bookmark))
			BOOKMARKS.remove(bookmark)

			self._updateBufferStatus()
			#File IO Here!--------------------
			self._Save()
		else:
			self._addBookmark(True)



	def _updateBufferStatus(self):
		#marks the given bookmark on the buffer
		def markBuffer(view, bookmark):
			uid = bookmark.getUid()
			region  = bookmark.getRegion()
			view.add_regions(str(uid), [region], "text.plain", "bookmark", sublime.DRAW_NO_FILL | sublime.DRAW_EMPTY_AS_OVERWRITE)

		#unmarks the given bookmark on the buffer
		def unmarkBuffer(view, bookmark):
			uid = bookmark.getUid()
			view.erase_regions(str(uid))

		Log ("MARKING BUFFER")

		window = self.window
		view = window.active_view()

		#this can happen if it's a temporary file
		#if view is None:
		#	return

		filePath = view.file_name()
		
		#mark all bookmarks that are visible, and unmark invisible bookmarks
		for bookmark in BOOKMARKS:
			shouldShow = shouldShowBookmark(window, view, bookmark, BOOKMARKS_MODE)
			#only mark if we are in the right file. Otherwise, all bookmarks will get
			#marked across all files
			validContext = bookmark.getFilePath() == filePath
			
			if validContext and shouldShow:
				markBuffer(view, bookmark)
			else:
				unmarkBuffer(view, bookmark)
				
		#unmark all erased bookmarks
		for bookmark in ERASED_BOOKMARKS:
			if bookmark.getFilePath() == filePath:
				unmarkBuffer(view, bookmark)

	#move bookmarks and update their regions when text is entered into the buffer
	def _UpdateBookmarkPosition(self):
		window = self.window
		view = window.active_view()
		filePath = view.file_name()
			
		global BOOKMARKS

		for bookmark in BOOKMARKS:
			#this bookmark (might) have been changed since it's in the current file
			#We're on a thread anyway so update it.
			if bookmark.getFilePath() == filePath:
				uid = bookmark.getUid()
				#load the new region to update it
				regions = view.get_regions(str(uid))

				#the region is not loaded yet
				if len(regions) == 0:
					continue

				#keep the new region on the *WHOLE* line, so that it covers new text also
				newRegion = view.line(regions[0])
				newLineStr = view.substr(newRegion) 
				newGroup = self.window.get_view_index(view)[0]
				
				assert newRegion is not None
				bookmark.setGroup(newGroup)
				bookmark.setRegion(newRegion)
				bookmark.setLineStr(newLineStr)

			
				#if region is empty, delete bookmark 
				#(since there is nothing in the bookmarked line)
				if len (newLineStr.strip()) == 0:
					Log("BOOKMARK IS EMPTY. REMOVING")
					global ERASED_BOOKMARKS

					ERASED_BOOKMARKS.append(deepcopy(bookmark))
					BOOKMARKS.remove(bookmark)
					
		#we've moved regions around so update the buffer
		self._updateBufferStatus()
		#we've moved bookmarks around and may also have deleted them. So, save
		self._Save()
	
	#helpers-------------------------------------------
	#creates a bookmark that keeps track of where we were before opening
	#an options menu. 
	def _createRevertBookmark(self, activeView):
		#there's no file open. return None 'cause there's no place to return TO
		if activeView is None:
			self.revertBookmark = None
			return

		filePath = activeView.file_name()
		#there is no file to go back to
		if filePath is None:
			return None


		region = getCurrentLineRegion(activeView)
		group = self.window.get_view_index(activeView)[0]

		uid = (-1) * REGION_BASE_TAG #does not matter
		name = "" #does not matter
		filePath = activeView.file_name()
		projectPath = "" #does not matter
		lineNumber = -1 #does not matter
		lineStr = "" #does not matter

		self.revertBookmark = Bookmark(uid, name, filePath, projectPath, region, group, lineNumber, lineStr)

	#goes to the revert bookmark
	def _gotoRevertBookmark(self):
		if self.revertBookmark is None:
			return

		#view = self.window.open_file(self.revertBookmark.getFilePath())
		#moveViewToGroup(self.window, view, self.revertBookmark.getGroup())
		gotoBookmark(self.revertBookmark, self.window)
		
		self.revertBookmark = None
		
	
	def _restoreFiles(self):
		views = self.window.views()
		for bookmark in BOOKMARKS:
			view = self.window.open_file(bookmark.getFilePath())
			#the bookmark is opened - reset it (move it's view back to it's group)
			if view in views:
				moveViewToGroup(self.window, view, bookmark.getGroup())



	#callbacks---------------------------------------------------
	def _AddBookmarkCallback(self, name):
		window = self.window
		view = window.active_view()
		filePath = view.file_name()

		#if the view is a temporary view, it can be none
		#if view is None:
		#	return

		#figure out the project path
		projectPath = window.project_file_name()
		if projectPath is None or projectPath is "":
			projectPath = NO_PROJECT

		#set the uID and increment it
		global UID
		myUID = UID
		myUID = REGION_BASE_TAG + myUID
		UID = UID + 1

		#get region and line data
		region = getCurrentLineRegion(view)
		group = self.activeGroup
		lineStr = view.substr(region)
		lineNumber = view.rowcol(view.sel()[0].begin())[0]



		#there's no content
		if len(lineStr.strip()) == 0:
			Log("STRING EMPTY. NOT CREATING BOOKMARK")
			sublime.status_message("SublimeBookmarks: BOOKMARK EMPTY. NOT CREATING BOOKMARK")
			return

		#create a bookmark and add it to the global list
		global BOOKMARKS

		print(filePath)

		bookmark = Bookmark(myUID, name, filePath, projectPath, region, group, lineNumber, lineStr)
		BOOKMARKS.append(bookmark)

		self._updateBufferStatus()
		#File IO Here!--------------------
		self._Save()

	#display highlighted bookmark
	def _AutoMoveToBookmarkCallback(self, index):
		assert index < len(self.displayedBookmarks)
		bookmark = self.displayedBookmarks[index]
		assert bookmark is not None

		#goto highlighted bookmark
		gotoBookmark(bookmark, self.window)
		self._updateBufferStatus()
	


	#if the user canceled, go back to the original file
	def _HilightDoneCallback(self, index):

		#restore all files back to their original places
		self._restoreFiles()

		#if the user canceled, then goto the revert bookmark
		if index == -1:
			self._gotoRevertBookmark()

		#otherwise, goto the selected bookmark
		else:
			#now open the selected bookmark and scroll to bookmark
			self._AutoMoveToBookmarkCallback(index)

			#move the correct bookmark back to the active group
			bookmark = self.displayedBookmarks[index]
			view = self.window.open_file(bookmark.getFilePath())
			moveViewToGroup(self.window, view, self.activeGroup)

		self._updateBufferStatus()

	def _gotoNext(self, forward):
		# Gather appropriate bookmarks
		self._getActiveBookmarks();

		if 0 == len(self.displayedBookmarks):
			return

		# increment or decrement
		if forward:
			self.global_bookmark_index = self.global_bookmark_index + 1
		else:
			self.global_bookmark_index = self.global_bookmark_index - 1

		# if we're pointing off the end, go to the first one instead
		if self.global_bookmark_index >= len(self.displayedBookmarks):
			self.global_bookmark_index = 0
		# if we're pointing off the beginning, go to the last one instead
		if self.global_bookmark_index < 0:
			self.global_bookmark_index = len(self.displayedBookmarks) - 1
		# Go there!
		self._AutoMoveToBookmarkCallback(self.global_bookmark_index)

	#remove the selected bookmark or go back if user cancelled
	def _RemoveDoneCallback(self, index):
		#restore all files back to their original places
		self._restoreFiles()

		#if the user canceled, then goto the revert bookmark
		if index == -1:
			self._gotoRevertBookmark()

		#otherwise, goto the selected bookmark
		else:
			global BOOKMARKS
			global ERASED_BOOKMARKS

			assert index < len(self.displayedBookmarks)

			#remove the mark from the bookmark
			window = self.window
			bookmark = self.displayedBookmarks[index]
			assert bookmark is not None

			#goto the removed bookmark
			gotoBookmark(bookmark, window)

			#add to list of erased bookmarks
			ERASED_BOOKMARKS.append(deepcopy(bookmark))
			BOOKMARKS.remove(bookmark)

			#decrement global_bookmark_index so goto_next will not skip anything
			if index <= self.global_bookmark_index:
				self.global_bookmark_index = self.global_bookmark_index - 1

		self._updateBufferStatus()
		#File IO Here!--------------------
		self._Save()


	#Save-Load----------------------------------------------------------------
	def _Load(self):
		global BOOKMARKS
		global BOOKMARKS_MODE
		global UID

		Log("LOADING BOOKMARKS")
		try:
			savefile = open(self.SAVE_PATH, "rb")

			BOOKMARKS_MODE = load(savefile)
			UID = load(savefile)
			BOOKMARKS = load(savefile)
	
		except (OSError, IOError, UnpicklingError, EOFError) as e:
			print (e)
			print("\nUNABLE TO LOAD BOOKMARKS. NUKING LOAD FILE")
			#clear the load file :]
			open(self.SAVE_PATH, "wb").close()
			#if you can't load, try and save a "default" state
			self._Save()
		
	def _Save(self):
		global BOOKMARKS
		global BOOKMARKS_MODE
		global UID

		Log("SAVING BOOKMARKS")

		try:
			savefile = open(self.SAVE_PATH, "wb")

			dump(BOOKMARKS_MODE, savefile)
			dump(UID, savefile)
			dump(BOOKMARKS, savefile)

			savefile.close()
		except (OSError, IOError, PicklingError) as e:
			print (e)
			print("\nUNABLE TO SAVE BOOKMARKS. PLEASE CONTACT DEV")
