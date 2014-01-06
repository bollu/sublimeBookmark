import sublime, sublime_plugin
from . import common

class bookmarkWatcher(sublime_plugin.EventListener):
	def on_activated_async(self, view):
		sublime.run_command("sublime_bookmark", {"type": "mark_buffer" } )


	def on_modified_async(self, view):
		sublime.run_command("sublime_bookmark", {"type": "move_bookmarks" } )


	def on_deactivated_async(self, view):
		sublime.run_command("sublime_bookmark", {"type": "unmark_buffer" } )

	def on_pre_save_async(self, view):
		sublime.run_command("sublime_bookmark", {"type": "save_data" } )