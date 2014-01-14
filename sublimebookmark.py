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
SHOW_ALL_BOOKMARKS = True

class OptionsSelector:
	def __init__(self, window, panelItems, onDone, onHighlight):
		self.window = window
		self.panelItems = panelItems
		self.onDone = onDone
		self.onHighlight = onHighlight

		
	def start(self):
		view = self.window.active_view()
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
		print ("DATA: " + inputPanelView.substr(selectionRegion))
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

	#the view is in the required group,
	#so we don't need to do anything.
	if group == viewGroup:
		pass
	#we have to move the view to the other group and give it a new index
	else:
		print("DIFFERENT")
		#if there are 0 views, then the moved view will have index 0
		#similarly, if there are n views, the last view will have index (n-1), and
		#so the new view will have index n  
		newIndex = len (window.views_in_group(group))
		#move the view to the highlighted group and assign a
		#correct index
		window.set_view_index(view, group, newIndex)


def gotoBookmark(bookmark, window):
	filePath = bookmark.getFilePath()
	lineNumber = bookmark.getLineNumber()

	#Okay, so there's a bug in sublime text.
	#if you open a file *before* opening the options menu,
	#the options menu gets created where the file is opened
	#Yes, this is stupid.

	#This happens in this plugin, since the _AutoMove() callback
	#seems to be called before the options menu is shown
	#So, if I open the file in another group, the options menu
	#opens in the *other* group, and not the current group.
	#I don't know if it's my bug or sublime text's but I have
	#a feeling it's sublime text's bug. Will have to report
	#this. This is a pain...

	#this line's order is important. This needs to be done first
	#since opening a file will cause the active group to change
	activeGroup = window.active_group()
	

	view = window.open_file(filePath)
	#move the view to the currently active group
	moveViewToGroup(window, view, activeGroup)

	#focus on the active group to avoid the panel problem as described
	window.focus_group(activeGroup)	
	window.focus_view(view)
	#show bookmark :)
	view.show_at_center(bookmark.getRegion())
		
	#move cursor to the middle of the bookmark's region
	bookmarkRegionMid = 0.5 * (bookmark.getRegion().begin() +  bookmark.getRegion().end())
	moveRegion = sublime.Region(bookmarkRegionMid, bookmarkRegionMid)
	view.sel().clear()
	view.sel().add(moveRegion)


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

def createBookmarkPanelItems(window, bookmarks, shouldShowAllBookmarks):	
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
	
	for bookmark in bookmarks:
		if shouldShowBookmark(bookmark, window, shouldShowAllBookmarks):

			bookmarkName = bookmark.getName()

			lineStrRaw = bookmark.getLineStr()
			bookmarkLine = ellipsisStringEnd(lineStrRaw.strip(), 55)

			bookmarkFile = ellipsisStringBegin(bookmark.getFilePath(), 55)

			bookmarkItems.append( [bookmarkName, bookmarkLine, bookmarkFile] )
		else:
			continue

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
		
		#bookmark that represents the file from which the panel was activated
		currentDir = os.path.dirname(sublime.packages_path())
		self.SAVE_PATH = currentDir + '/sublimeBookmarks.pickle'
		Log(currentDir)

		self._Load()
		


	def run(self, type):
		global SHOW_ALL_BOOKMARKS

		if type == "add":
			self._addBookmark()

		elif type == "goto":
			#on highlighting, goto the current bookmark
			#on option select, just center the selected item
			self._createBookmarkPanel(self._HilightDoneCallback, self._AutoMoveToBookmarkCallback)

		elif type == "remove":
			#on highlighting, goto the current bookmark
			#on option select, remove the selected item
			self._createBookmarkPanel(self._RemoveDoneCallback, self._AutoMoveToBookmarkCallback)

		elif type == "show_all_bookmarks":
			SHOW_ALL_BOOKMARKS = True
			self._Save()

			#update buffer to show all bookmarks
			self._updateBufferStatus()

		elif type == "show_project_bookmarks":
			SHOW_ALL_BOOKMARKS = False
			self._Save()

			#update buffer to show only project bookmarks
			self._updateBufferStatus()

		elif type == "remove_all":
			self._removeAllBookmarks()

		elif type == "mark_buffer":
			self._updateBufferStatus()

		elif type == "move_bookmarks":
			self._UpdateBookmarkPosition();


	def _createBookmarkPanel(self, onHighlight, onDone):
		self.revertBookmark = None

		window = self.window
		#create a revert bookmark to go back if the user cancels
		self._createRevertBookmark(window.active_view())

		#create a list of acceptable bookmarks based on settings
		bookmarkItems = createBookmarkPanelItems(window, BOOKMARKS, SHOW_ALL_BOOKMARKS)

		#if no bookmarks are acceptable, don't show bookmarks
		if len(bookmarkItems) == 0:
			return
		#create a selection panel and launch it
		selector = OptionsSelector(window, bookmarkItems, onHighlight, onDone)
		selector.start()

	#event handlers----------------------------
	def _addBookmark(self):
		Log ("add")

		window = self.window
		view = window.active_view()
		region = getCurrentLineRegion(view)

		#copy whatever is on the line for the bookmark name
		initialText = view.substr(region).strip()

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
		if view is None:
			return

		filePath = view.file_name()
		
		#mark all bookmarks that are visible, and unmark invisible bookmarks
		for bookmark in BOOKMARKS:
			shouldShow = shouldShowBookmark(bookmark, window, SHOW_ALL_BOOKMARKS)

			if bookmark.getFilePath() == filePath and shouldShow:
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
					self._Save()

		#we've moved regions around so update the buffer
		self._updateBufferStatus()
					
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
		group = self.window.active_group()

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

		gotoBookmark(self.revertBookmark, self.window)
		self.revertBookmark = None
		
	#callbacks---------------------------------------------------
	def _AddBookmarkCallback(self, name):
		window = self.window
		view = window.active_view()
		filePath = view.file_name()

		#if the view is a temporary view, it can be none
		if view is None:
			return

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
		group = self.window.active_group()
		lineStr = view.substr(region)
		lineNumber = view.rowcol(view.sel()[0].begin())[0]

		#create a bookmark and add it to the global list
		global BOOKMARKS

		bookmark = Bookmark(myUID, name, filePath, projectPath, region, group, lineNumber, lineStr)
		BOOKMARKS.append(bookmark)

		self._updateBufferStatus()
		#File IO Here!--------------------
		self._Save()

	#display highlighted bookmark
	def _AutoMoveToBookmarkCallback(self, index):
		assert index < len(BOOKMARKS)
		bookmark = BOOKMARKS[index]
		assert bookmark is not None

		#goto highlighted bookmark
		gotoBookmark(bookmark, self.window)
		self._updateBufferStatus()
	


	#if the user canceled, go back to the original file
	def _HilightDoneCallback(self, index):
		#if we started from a blank window, self.revertBookmark CAN be None
		if index == -1:
			self._gotoRevertBookmark()
		#otherwise, just goto the selected bookmark
		else:
			#hacky but hey...
			self._AutoMoveToBookmarkCallback(index)

		self._updateBufferStatus()


	#remove the selected bookmark or go back if user cancelled
	def _RemoveDoneCallback(self, index):
		#if we started from a blank window, self.revertBookmark CAN be None
		if index == -1:
			self._gotoRevertBookmark()
		else:

			global BOOKMARKS
			global ERASED_BOOKMARKS

			assert index < len(BOOKMARKS)

			#remove the mark from the bookmark
			window = self.window
			bookmark = BOOKMARKS[index]
			assert bookmark is not None

			#goto the removed bookmark
			gotoBookmark(bookmark, window)

			#add to list of erased bookmarks
			ERASED_BOOKMARKS.append(deepcopy(bookmark))
			del BOOKMARKS[index]

		self._updateBufferStatus()

		#File IO Here!--------------------
		self._Save()


	#Save-Load----------------------------------------------------------------
	def _Load(self):
		global BOOKMARKS
		global SHOW_ALL_BOOKMARKS
		global UID

		Log("LOADING BOOKMARKS")
		try:
			savefile = open(self.SAVE_PATH, "rb")

			SHOW_ALL_BOOKMARKS = load(savefile)
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
		global SHOW_ALL_BOOKMARKS
		global UID

		Log("SAVING BOOKMARKS")

		try:
			savefile = open(self.SAVE_PATH, "wb")

			dump(SHOW_ALL_BOOKMARKS, savefile)
			dump(UID, savefile)
			dump(BOOKMARKS, savefile)

			savefile.close()
		except (OSError, IOError, PicklingError) as e:
			print (e)
			print("\nUNABLE TO SAVE BOOKMARKS. PLEASE CONTACT DEV")
