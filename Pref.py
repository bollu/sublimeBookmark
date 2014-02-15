import sublime

class Pref:
	def load(self, settings):
		Pref.color_scope_name = settings.get('color_scope_name', "comment")
		Pref.draw_outlined = bool(settings.get('draw_outlined', True)) * sublime.DRAW_OUTLINED
		Pref.enabled = True