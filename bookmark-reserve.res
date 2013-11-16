

# class ExampleCommand(sublime_plugin.WindowCommand):
# 	def __init__(self, window):
# 		self.window = window;
# 		self.bookmarks = []
# 		self.dbg = True

# 	def run(self):
# 		self.addBookmark("bollu")

# 		self.save()
# 		self.load()

# 		self.log ("hey!")


# 	def save(self):
# 		self.log ("saving")

# 		try:
# 			pickleFile = open(savePath, 'wb')
# 			pickle.dump(self.bookmarks, pickleFile)
# 		except IOError:
# 			self.log ("Error: can\'t find file or read data")


# 	def load(self):
# 		self.log ("loading")

# 		try:
# 			pickleFile = open(savePath, 'rb')
# 			self.bookmarks = pickle.load(pickleFile)

# 			#print all bookmarks
# 			if self.dbg:
# 				for bookmark in self.bookmarks:
# 					bookmark.printDbg()

# 		except IOError:
# 			self.log ("Error: can\'t find file or read data")


# 	def addBookmark(self, name):
# 		bookmark = Bookmark(self.window, name)
# 		self.bookmarks.append(bookmark)


# 	def log(self, str):
# 		if self.dbg:
# 			print (str)