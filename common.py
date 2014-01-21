import sublime
import sublime_plugin

#if someone names their project this, we're boned
NO_PROJECT = "___NO_PROJECT_PRESENT____"


REGION_BASE_TAG = int(11001001000011111101)
SETTINGS_NAME = "SublimeBookmarks.sublime-settings"

VERSION = "2.0.0"



def Log(string):
	if True:
		print (string)

def getViewByBufferID(window, bufferID):
	for view in window.views():
		if view.buffer_id() == int(bufferID):
			return view
		else:
			continue
		
	Log("NO VIEW. BUFFER ID: " + str(bufferID))
	return None


def getCurrentLineRegion(view):
	assert (len(view.sel()) > 0)
	selectedRegion = view.sel()[0]
	region =  view.line(selectedRegion)

	return region 


def getCurrentProjectPath(window):
	projectPath = window.project_file_name()
	if projectPath is None or projectPath is "":
		projectPath = NO_PROJECT

	return projectPath	


def getCurrentActiveGroup(window):
	view = window.active_view()
	#(viewGroup, viewIndex) = window.get_view_index(view)

	return 0#viewGroup


def isLineEmpty(line):
	return len(line.strip()) == 0



def isViewTemporary(view):
	return (view is None) or (view.file_name() is None)



import os.path
def getSavePath():
	#bookmark that represents the file from which the panel was activated
	currentDir = os.path.dirname(sublime.packages_path())
	return currentDir + '/sublimeBookmarks.pickle'


#MESSAGES
def MESSAGE_NoBookmarkToGoto():
	sublime.status_message("SublimeBookmarks: NO ACCEPTABLE BOOKMARKS TO GOTO. CHECK CURRENT MODE")

def MESSAGE_BookmarkEmpty():
	sublime.status_message("SublimeBookmarks: BOOKMARK EMPTY. NOT CREATING BOOKMARK")