import sublime
import sublime_plugin
import threading 
import os.path
from pickle import dump, load, UnpicklingError, PicklingError
from copy import deepcopy


from .common import *
from .bookmark import *
from .visibilityHandler import *
from .ui import *

REGION_BASE_TAG = int(11001001000011111101)
SETTINGS_NAME = "SublimeBookmarks.sublime-settings"

BOOKMARKS = []
UID = None

#list of bookmarks that have ben deleted. 
#This is used to remove bookmarks' buffer highlights. Without this, if a bookmark is removed,
#when a file is revisited, the buffer will still be marked. This will keep track of bookmarks
#that have been removed.
ERASED_BOOKMARKS = []
  
#whether all bookmarks (even unrelated) should be shown
BOOKMARKS_MODE = SHOW_ALL_BOOKMARKS()


def removeBookmark(bookmark):
	global BOOKMARKS
	global ERASED_BOOKMARKS
	ERASED_BOOKMARKS.append(deepcopy(bookmark))
	BOOKMARKS.remove(bookmark)

def addBookmark(bookmark):
	global BOOKMARKS
	BOOKMARKS.append(deepcopy(bookmark))

class SublimeBookmarkCommand(sublime_plugin.WindowCommand):
	def __init__(self, window):
		self.window = window
		self.activeGroup = self.window.active_group()	
		self.activeView = self.window.active_view()

		global BOOKMARKS
		global UID 

		BOOKMARKS = []		
		#initialize to 0
		UID = 0

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


	def run(self, type):
		global BOOKMARKS_MODE

		self.activeGroup = self.window.active_group()	
		self.activeView = self.window.active_view()

		#update bookmark positions. We need to do it anyway...
		self._UpdateBookmarkPosition()

		#delete any temp bookmarks that have been since destroyed
		self._UpdateTemporaryBookmarks()

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
			self._UpdateBookmarkPosition()

		elif type == "update_temporary":
			self._UpdateTemporaryBookmarks()

	def _createBookmarkPanel(self, onHighlight, onDone):

		def moveBookmarksToActiveGroup(activeGroup):	
			#move all open bookmark tabs to one group so that group switching does not
			#occur.
			for bookmark in BOOKMARKS:
				moveBookmarkToGroup(self.window, bookmark, self.activeGroup)
			
		def createPanel():
			self.displayedBookmarks = getVisibleBookmarks(BOOKMARKS, self.window, self.activeView, BOOKMARKS_MODE)
			bookmarkPanelItems = createBookmarkPanelItems(self.window, self.displayedBookmarks)

			#if no bookmarks are acceptable, don't show bookmarks
			if len(self.displayedBookmarks) == 0:
				return False

			#create a selection panel and launch it
			selector = OptionsSelector(self.window, bookmarkPanelItems, onHighlight, onDone)
			selector.start()

			return True

		#create a revert bookmark to go back if the user cancels
		self._createRevertBookmark(self.activeView)
		
		#move all active bookmarks to the currently active group
		moveBookmarksToActiveGroup(self.activeGroup)

		#create the selection panel
		panelCreated = createPanel()
		if not panelCreated:
			MESSAGE_NoBookmarkToGoto()
			return False
	

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
			self._addBookmark()



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

		if self.active_view is None:
			return
			
		filePath = self.activeView.file_name()
		bufferID = self.activeView.buffer_id()
		
		#mark all bookmarks that are visible, and unmark invisible bookmarks
		for bookmark in BOOKMARKS:
			#if the bookmark should be shown according to the current bookmark mode
			shouldShow = shouldShowBookmark(self.window, self.activeView, bookmark, BOOKMARKS_MODE)

			#only mark if we are in the right view.
			validContext = bookmark.isMyView(self.window, self.activeView)

			if validContext and shouldShow:
				markBuffer(self.activeView, bookmark)
			else:
				unmarkBuffer(self.activeView, bookmark)
				
		#unmark all erased bookmarks
		for bookmark in ERASED_BOOKMARKS:
			validContext = bookmark.isMyView(self.window, self.activeView)

			if validContext:
				unmarkBuffer(self.activeView, bookmark)


	#move bookmarks and update their regions when text is entered into the buffer
	def _UpdateBookmarkPosition(self):
		#this bookmark (might) have been changed since it's in the current file
		#We're on a thread anyway so update it.
		for bookmark in BOOKMARKS:

			#if the activeView is the bookmark's view, update r
			if bookmark.isMyView(self.window, self.activeView):
				
				bookmark.updateData(self.window, self.activeView)

				#the bookmark is empty - it has no data in it.
				if bookmark.isEmpty(self.activeView):
					Log("EMPTY BOOKMARK. NAME: " + bookmark.getName())
					removeBookmark(bookmark)

		#we've moved regions around so update the buffer
		self._updateBufferStatus()
		#we've moved bookmarks around and may also have deleted them. So, save
		self._Save()



	def _UpdateTemporaryBookmarks(self):
		for bookmark in BOOKMARKS:
			#if the bookmark is a temporary bookmark and the bookmark has been deleted, remove the bookmark
			if bookmark.isTemporary() and shouldRemoveTempBookmark(self.window, bookmark):

				Log("BOOKMARK IS TEMP AND BUFFER HAS BEEN REMOVED. REMOVING. " + \
					"BUFFER: " + \
					str(bookmark.getBufferID()) + \
					"; NAME: " + str(bookmark.getName()))

				removeBookmark(bookmark)


	#helpers-------------------------------------------
	#creates a bookmark that keeps track of where we were before opening
	#an options menu. 
	def _createRevertBookmark(self, activeView):
		#there's no file open. return None 'cause there's no place to return TO
		if isViewTemporary(activeView):
			self.revertBookmark = None
			return

		uid = -1
		name = ""

		self.revertBookmark = Bookmark(uid, name, self.window, activeView)

	#goes to the revert bookmark
	def _gotoRevertBookmark(self):
		if self.revertBookmark is None:
			return
		self.revertBookmark.goto(self.window)
		self.revertBookmark = None
		
	
	def _restoreFiles(self):
		views = self.window.views()
		for bookmark in BOOKMARKS:
			moveBookmarkToGroup(self.window, bookmark, bookmark.getGroup())

	#callbacks---------------------------------------------------
	def _AddBookmarkCallback(self, name):
		
		global UID
		assert UID is not None

		myUID = UID
		myUID = REGION_BASE_TAG + myUID
		UID = UID + 1

		#get region and line data
		region = getCurrentLineRegion(self.activeView)
		lineStr = self.activeView.substr(region)
		
		#there's no content
		if isLineEmpty(lineStr):
			MESSAGE_BookmarkEmpty()
			return

		bookmark = Bookmark(UID, name, self.window, self.activeView)
		addBookmark(bookmark)

		self._updateBufferStatus()
		self._Save()

	#display highlighted bookmark
	def _AutoMoveToBookmarkCallback(self, index):
		assert index < len(self.displayedBookmarks)
		bookmark = self.displayedBookmarks[index]
		assert bookmark is not None

		#goto highlighted bookmark
		bookmark.goto(self.window)
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

			#move the correct bookmark back to the active group - since all fails
			#including the bookmark have been restored, we have to move the bookmark back
			#ARRGH! this is __so__ hacky :( 
			bookmark = self.displayedBookmarks[index]
			moveBookmarkToGroup(self.window, bookmark, self.activeGroup)
			
			#IMPORTANT - not doing this will cause bookmark to think it is
			#still in it's previous group.
			bookmark.updateData(self.window, self.activeView)

		self._updateBufferStatus()


	#remove the selected bookmark or go back if user cancelled
	def _RemoveDoneCallback(self, index):
		#restore all files back to their original places
		self._restoreFiles()

		#if the user canceled, then goto the revert bookmark
		if index == -1:
			self._gotoRevertBookmark()
		#otherwise, goto the selected bookmark
		else:
			assert index < len(self.displayedBookmarks)
			bookmark = self.displayedBookmarks[index]
			assert bookmark is not None

			#goto the removed bookmark
			bookmark.goto(self.window)
			removeBookmark(bookmark)


		self._updateBufferStatus()
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
	
		except (OSError, IOError, UnpicklingError, EOFError, BaseException) as e:
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

		
		try:
			savefile = open(self.SAVE_PATH, "wb")

			dump(BOOKMARKS_MODE, savefile)
			dump(UID, savefile)
			dump(BOOKMARKS, savefile)

			savefile.close()
		except (OSError, IOError, PicklingError) as e:
			print (e)
			print("\nUNABLE TO SAVE BOOKMARKS. PLEASE CONTACT DEV")
