import sublime, sublime_plugin
from pickle import dump, load
from os.path import dirname, isfile

from . import fileLock
import sys

g_VERSION = "1.0.3"

#Holy crap Turing is rolling in his grave right now
#This is a monstrosity. Have to rewrite as an FSM or something.
#this is *worse* than spaghetti code.

g_SAVE_PATH = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'

def get_save_path():
	return dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'


g_REGION_TAG = "sublime_Bookmarks_"
g_SETTINGS_NAME = "SublimeBookmarks.sublime-settings"


g_BOOKMARK_LIST = None
g_BOOKMARK_COUNT = 0

g_SETTINGS_NAME = "SublimeBookmarks.sublime-settings" 

#settings
g_SETTINGS = {
	"show_free": True,
	"show_project": False
}


def g_log(str):
	if(True):
		#dear lord, I'm a monster
		print ("SublimeBookmarks: " + str)
 
#Initialization------------------------------------------
def init(window):
	g_log("***INIT BOOKMARKS!****")
	load_settings()
	_read_bookmarks_from_disk(window)

	#mark the gutters
	for bookmark in g_BOOKMARK_LIST:
			bookmark.mark_gutter(window)


#Bookmark related code-----------------------------------------------------
def _get_current_project_path(window):
	project = window.project_file_name()
	if project is None:
		return ""
		
	return project


class Bookmark:
	def __init__(self, window, name, visible=True):

		self.name = name
		self.visible = visible

		view = window.active_view()
		self.view = view

		#set up the unique ID part first :)
		global g_BOOKMARK_COUNT
		self.regionTag = g_REGION_TAG + str(g_BOOKMARK_COUNT)
		g_BOOKMARK_COUNT = g_BOOKMARK_COUNT + 1

		self.filePath = view.file_name()
		self.projectPath = _get_current_project_path(window)
		
		#caution: calculated from (0,0) NOT (1,1)
		(row, col) = view.rowcol(view.sel()[0].begin())

		pt = view.text_point(row, col)
		self.region =  view.line(pt)
		self.a = self.region.a
		self.b = self.region.b

		#mark gutter
		#self.mark_gutter(window)


	def _getMyView(self, window):

		#the view we've saved is our view
		if self.view is not None and self.view.file_name() == self.filePath:
			return self.view
			
		prevView = window.active_view()

		#the currently open view is our view
		if prevView.file_name() == self.get_file_path():
			self.view = prevView
			return prevView

		#none of our assumptions are true. We have to open our view and then return our
		#view
		myView = window.open_file(self.filePath, sublime.TRANSIENT)
		self.view = myView

		window.focus_view(prevView)

		return self.view

	def goto(self, window, useColumnInfo):
		view = window.open_file(self.filePath)

		#get your region 
		regions = view.get_regions(self.regionTag)

		#the region has been destroyed. recreate region and re-mark
		if not regions:
			g_log("*******unable to get my region!******")

			#inflate re-creates self.region
			myView = self._getMyView(window)
			self.region = sublime.Region(self.a, self.b)
			#self.mark_gutter(window)

			#recursion!
			view.show_at_center(self.region)

		else:
			view.show_at_center(regions[0])

	def remove(self, window):
		self._getMyView(window).erase_regions(self.regionTag)


	def mark_gutter(self, window):
		myView = self._getMyView(window)
		
		if self.visible and _should_display_bookmark(window, self):
			#overwrite the current region
			myView.add_regions(self.regionTag, [self.region], "text.plain", "bookmark", sublime.DRAW_NO_FILL)
		else:
			myView.add_regions(self.regionTag, [self.region], "text.plain",  "", sublime.HIDDEN)

	def get_line(self, window):
		myView = self._getMyView(window)

		lineText = myView.substr(self.region)
		line =  ' '.join(lineText.split())

		return line

	def get_name(self):
		return self.name


	def get_file_path(self):
		return self.filePath
	

	def get_project_path(self):
		return self.projectPath


	def print_dbg(self):
		g_log ("Bookmark: " + self.name + "| Project: " + self.projectPath)

	#Pickling Code (Copy pasted)---------------------------

	#I need a proper way to do this
	def update_row_column(self, window):

		#get my own point and update my row and column
		self.a = self.region.a
		self.b = self.region.b

	def inflate(self, window):
		myView = self._getMyView(window)
		self.region = sublime.Region(self.a, self.b)


#BaseBookmarkCommand-------------------------------------
class BaseBookmarkCommand:
	def __init__(self, window):
		self.window = window


	def _save(self):
		set_bookmarks(self.bookmarks, self.window)
	

	def _load(self):
		self.bookmarks = get_bookmarks(self.window)
		load_settings()

#save / load code----------------------------------------
def get_bookmarks(window, shouldFilter=True):
	
	if g_BOOKMARK_LIST is None:
		_read_bookmarks_from_disk(window)

	filteredBookmarkList = None
	if shouldFilter:
		#return the list of *permissible* bookmarks. 
		filteredBookmarkList =  _create_bookmarks_list(window, g_BOOKMARK_LIST)
	else:
		filteredBookmarkList = g_BOOKMARK_LIST


	for bookmark in filteredBookmarkList:
		bookmark.mark_gutter(window)

	return filteredBookmarkList

def set_bookmarks(bookmarks, window):
	g_log("set global bookmarks")
	
	global g_BOOKMARK_LIST

	assert bookmarks != None, "trying to write  *None* bookmarks."

	g_BOOKMARK_LIST = bookmarks

	for bookamrk in g_BOOKMARK_LIST:
		bookmark.mark_gutter(window)
	#_write_bookmarks_to_disk(window)

	

#IO-------------------------------------------------------------
def _write_bookmarks_to_disk(window):
	global g_BOOKMARK_LIST
	global g_SAVE_PATH
	global g_BOOKMARK_COUNT

	#if the bookmarks haven't been loaded yet - 2 possibilities
	#1) no pickle file exists (this is the first execution EVER. So chill)
	#2) _read_bookmarks_from_disk() hasn't been called yet (bookmarks have not
	# been loaded for the first time)
	#both are solved by calling _read_bookmarks_from_disk()
	if g_BOOKMARK_LIST == None:
		g_log("**************************************************")
		g_log("trying to write *None* bookmarks to disk. Reloading bookmarks")
		g_log("**************************************************")
		_read_bookmarks_from_disk(window)
		return

	g_SAVE_PATH = get_save_path()
	
	with fileLock.FileLock(g_SAVE_PATH):

		try:
			pickleFile = open(g_SAVE_PATH, "wb")
		except  Exception:
			g_log('Error when opening pickle')
			_load_defaults()

		dump(g_VERSION, pickleFile)
		dump(g_BOOKMARK_LIST, pickleFile)
		dump(g_BOOKMARK_COUNT, pickleFile)

		g_log("wrote bookmarks to disk. Path: " + g_SAVE_PATH)

def _read_bookmarks_from_disk(window):
	global g_BOOKMARK_LIST
	global g_SAVE_PATH
	global g_BOOKMARK_COUNT

	g_SAVE_PATH = get_save_path()

	if not isfile(g_SAVE_PATH):
		g_log("no bookmark load file found. Path:" + g_SAVE_PATH)
		_load_defaults()
		return

	g_log("loading bookmarks from disk. Path: " + g_SAVE_PATH)

	with fileLock.FileLock(g_SAVE_PATH):
		
		try:
			pickleFile = open(g_SAVE_PATH, "rb")

			pickleVersion = load(pickleFile)
			g_BOOKMARK_LIST = load(pickleFile)
			g_BOOKMARK_COUNT = load(pickleFile)

			if pickleVersion != g_VERSION:
				g_log("Older pickle Present:" + g_SAVE_PATH + ".Loading Defaults")
				_load_defaults()

			
			if g_BOOKMARK_LIST is None or g_BOOKMARK_COUNT is None:
				g_log("Unable to load pickle correctly:" + g_SAVE_PATH)
				_load_defaults()

		except  Exception:
			g_log('Error when opening pickle')
			_load_defaults()



	for bookmark in g_BOOKMARK_LIST:
		bookmark.inflate(window)

		
def _load_defaults():
	global g_BOOKMARK_LIST
	global g_BOOKMARK_COUNT

	g_BOOKMARK_LIST = []
	g_BOOKMARK_COUNT = 0


#Settings----------------------------------------------------------------------
def save_settings(window):
	pass

def load_settings():
	g_log("**loading bookmarks**")
	global g_SETTINGS

	g_log("loading settings")
	settings = sublime.load_settings(g_SETTINGS_NAME)

	#not a fan of hardcoding this
	g_SETTINGS["show_free"]  = settings.get("always_show_free_bookmarks", False)
	g_SETTINGS["show_project"] = settings.get("always_show_project_bookmarks", True)


	#settings.add_on_change('always_show_free_bookmarks', load_settings)
	#settings.add_on_change('always_show_project_bookmarks', load_settings)


#panel creation code----------------------------
def _ellipsis_string_end(string, length):
		#I have NO idea why the hell this would happen. But it's happening.
		if string is None:
			return ""
		else:
			return string if len(string) <= length else string[ 0 : length - 3] + '...'


def _ellipsis_string_begin(string, length):
		if string is None:
			return ""
		else:	
			return string if len(string) <= length else '...' + string[ len(string) + 3 - (length)  : len(string) ] 


def create_bookmarks_panel_items(window, bookmarks):	
		bookmarkItems = []

		for bookmark in bookmarks:

			bookmarkName = bookmark.get_name()
			bookmarkLine = _ellipsis_string_end(bookmark.get_line(window), 55)
			bookmarkFile = _ellipsis_string_begin(bookmark.get_file_path(), 55)

			bookmarkItems.append( [bookmarkName, bookmarkLine, bookmarkFile] )

		return bookmarkItems

		# bookmarkItems = []
		# g_log("currentProject: " + currentProject)

		# for bookmark in bookmarks:
		# 	bookmarkProject = bookmark.get_project_path()
		
		# 	bookmark.print_dbg()

		# 	#this is not yet perfect. will have to revise this
		# 	if True or (currentProject == "") or (currentProject.lower() == bookmarkProject.lower()):
				
		# 		bookmarkName = bookmark.get_name()
				
		# 		bookmarkLine = _ellipsis_string_end(bookmark.get_line(), 55)
		# 		bookmarkFile = _ellipsis_string_begin(bookmark.get_file_path(), 55)

		# 		bookmarkItems.append( [bookmarkName, bookmarkLine, bookmarkFile] )
				
		# return bookmarkItems


def _should_display_bookmark(window, bookmark):
	#HACK!!!
	#return True
	#----------------------------------------------------------
	
	currentProject = _get_current_project_path(window)
	bookmarkProject = bookmark.get_project_path()

	#if the bookmark has a project and *that project is open*,
	#show it.
	# 	(or)
	#if the bookmark was free and the editor *is now free*,
	#show it
	if currentProject == bookmarkProject:
		return True

	# #if you should always free bookmarks and this bookmark
	# #is free, add it
	elif g_SETTINGS["show_free"] == True and bookmarkProject == "":
		return True

	# #if you should always show project related bookmarks and this bookmark
	# #has a project, add it
	elif g_SETTINGS["show_project"] == True and bookmarkProject != "":
		return True

	#it reached here => bookmark and project don't match
	g_log("Failed " + bookmark.get_name() + " | " + _ellipsis_string_begin(bookmark.get_project_path(), 55))
	return False


def _create_bookmarks_list(window, bookmarks):
	currentProject = _get_current_project_path(window)
	bookmarksList = []

	for bookmark in g_BOOKMARK_LIST:
		g_log("seeing if |" + bookmark.get_name() + "| is applicable in list")
		bookmarkProject = bookmark.get_project_path()

		if _should_display_bookmark(window, bookmark):
			bookmarksList.append(bookmark)

			
	return bookmarksList

