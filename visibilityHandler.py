from .common import *

#whether all bookmarks (even unrelated) should be shown
def SHOW_ALL_BOOKMARKS():
	return "Show All Bookmarks"

def SHOW_ONLY_PROJECT_BOOKMARKS():
	return "Show Only Project Bookmarks"

def SHOW_ONLY_FILE_BOOKMARKS():
	return "Show Only File Bookmarks"


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
		#there are no bookmarks in the current file
		return False

	return False





def ___sortBookmarks(visibleBookmarks, currentFile):
	from collections import defaultdict

	def lineSortFn(bookmark):
		return bookmark.getLineNumber()

	def sortByLineNumber(bookmarks):
		return sorted (bookmarks, key = lineSortFn)

	fileBookmarks = defaultdict(list)
	sortedBookmarks = []

	for bookmark in visibleBookmarks:
		filePath = bookmark.getFilePath()
		fileBookmarks[filePath].append(bookmark)


	#take all bookmarks in current file, sort then 1st and then remove the current file from the 
	#list of files
	currentFileBookmarks = fileBookmarks[currentFile]
	sortedBookmarks = sortedBookmarks + sortByLineNumber(currentFileBookmarks)
	
	del fileBookmarks[currentFile]
		
	#iterate over all list of bookmarks in each file and sort them according to line number
	for bookmarkList in fileBookmarks.values():
		sortedBookmarkList = sortByLineNumber(bookmarkList)
		sortedBookmarks = sortedBookmarks + sortedBookmarkList


	return sortedBookmarks



def getVisibleBookmarks(bookmarks, window, activeView, bookmarkMode, activeFileFirst):
	visibleBookmarks = []
	for bookmark in bookmarks:
		if shouldShowBookmark(window, activeView, bookmark, bookmarkMode):
			visibleBookmarks.append(bookmark)

	if activeFileFirst:
		visibleBookmarks = ___sortBookmarks(visibleBookmarks, activeView.file_name())
	return visibleBookmarks
