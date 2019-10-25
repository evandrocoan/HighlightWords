import sublime, sublime_plugin
import time
import sys
import re
import functools

import pushdown
import threading

from debug_tools import getLogger

SCOPES = ['string', 'entity.name.class', 'variable.parameter', 'invalid.deprecated', 'invalid', 'support.function']

ST3 = False if sys.version_info < (3, 0) else True
USE_REGEX = False
IGNORE_CASE = False
WHOLE_WORD = False # only effective when USE_REGEX is True
UNDER_THE_CURSOR = True
CLEAR_ON_ESCAPE = False
KEYWORD_MAP = []


# Debugger settings: 0 - disabled, 127 - enabled
log = getLogger( 1, __name__ )

_parser = pushdown.Lark( r"""
start: SEARCH* | WORDS* | SEARCH+ WORDS+

WORDS: /[^\/].*/
SEARCH: / *(?<!\\)\/[^\/]+(?<!\\)\/ */
SPACES: /[\t \f]+/

%ignore SPACES
""", start='start', parser='lalr', lexer='contextual' )

g_view_selections = {}
g_regionkey = "HighlightWords"

class Data(object):

	def __init__(self, view):
		self.view = view
		self.added_regions = []
		self.added_regions_set = []
		self.last_caret_begin = 0
		self.selected_region_index = 0

	def add_regions_set(self, regions_set):
		self.added_regions = list( sorted( regions_set, key=lambda item: item[0] ) )

	def actual_caret_begin(self):
		selections = self.view.sel()
		target_position = 0

		if len( selections ):
			target_position = selections[0].begin()

		return target_position

	def _reset_counter(self, backwards):

		if backwards:
			self.selected_region_index = len( self.added_regions ) - 1

		else:
			self.selected_region_index = 0

	@staticmethod
	def _compare(backwards, first, second):

		if backwards:
			return first < second

		return first >= second

	def target_points(self, backwards=False):
		increment_size = -1 if backwards else 1
		actual_caret_begin = self.actual_caret_begin()
		has_selection_changed = actual_caret_begin != self.last_caret_begin

		if has_selection_changed:
			has_reached_end = 0
			has_incremented = False
			has_decremented = False

			while True:

				try:
					target_points = self.added_regions[self.selected_region_index]

					if self._compare( backwards, target_points[0], actual_caret_begin ):
						has_incremented = True
						if has_decremented: break
						self.selected_region_index -= increment_size

					else:
						has_decremented = True
						if has_incremented: break
						self.selected_region_index += increment_size

				except IndexError:
					has_reached_end += 1
					self._reset_counter( backwards )

				if has_reached_end > 1:
					break

		else:
			self.selected_region_index += increment_size

			try:
				target_points = self.added_regions[self.selected_region_index]

			except IndexError:
				self._reset_counter( backwards )
				target_points = self.added_regions[self.selected_region_index]

		self.last_caret_begin = actual_caret_begin
		return target_points


def State(view):

	if view.id() in g_view_selections:
		return view, g_view_selections.get( view.id() )

	else:
		window = view.window() or sublime.active_window()
		active_view = window.active_view()
		return active_view, g_view_selections.setdefault( active_view.id(), Data( active_view ) )


class HighlightWordsGarbageCollector(sublime_plugin.EventListener):

	def on_pre_close(self, view):
		if view.id() in g_view_selections:
			view.run_command( 'unhighlight_words' )
			del g_view_selections[view.id()]


class HighlightWordsCommand(sublime_plugin.TextCommand):
	def get_words(self, text, skip_search=False):
		if USE_REGEX:

			try:
				filtered_words = []
				unfiltered_words = []
				tree = _parser.parse(text)

				for token in tree.children:
					# print( 'token', token.pretty() )
					if token.type == 'SEARCH':
						regex = token.strip(' ')

						if skip_search:
							filtered_words.append( regex )

						else:
							regex = regex.strip('/')

							# print('regex', regex)
							new = list( re.finditer(regex, self.view_text) )

							# print('new', [ item.groups() for item in new ] )
							if new: filtered_words.append( new )

					elif token.type == 'WORDS':
						unfiltered_words.append(token)

				other_words = list( filter( lambda x: x and x != ' ', re.split( r'((?:\\ |[^ ])+)', " ".join( unfiltered_words ) ) ) )
				filtered_words.extend( other_words )
				return filtered_words

			except Exception as e:
				log( "regex message:", e )
				return text.split()

		else:
			return text.split()

	def run(self, edit):
		view = self.view
		window = view.window() or sublime.active_window()

		self.view_text = view.substr( sublime.Region( 0, view.size() ) )
		highlight_text = view.settings().get('highlight_text', '')
		# print('highlight_text', highlight_text)

		word_list = self.get_words(highlight_text, skip_search=True)
		for region in view.sel():

			if UNDER_THE_CURSOR:
				region = region.empty() and view.word(region) or region

			else:
				if region.empty(): continue

			cursor_word = view.substr(region).strip()
			# print('cursor_word', cursor_word)
			if not cursor_word: continue

			if USE_REGEX:
				# ST uses perl regular expression syntax, escape all special characters
				cursor_word = re.sub(r'([ \\.\[{}()\*+?|^$])', r'\\\1', cursor_word).replace('\t', '\\t').replace('\n', '\\n')
				if WHOLE_WORD:
					cursor_word = "\\b" + cursor_word + "\\b"
			if cursor_word in word_list:
				word_list.remove(cursor_word)
			else:
				word_list.append(cursor_word)
			break

		display_list = ' '.join(word_list)
		prompt = 'Highlight words '
		if USE_REGEX:
			prompt += '(RegEx, '
		else:
			prompt += '(Literal, '
		if IGNORE_CASE:
			prompt += 'Ignore Case'
		else:
			prompt += 'Case Sensitive'
		prompt += '):'


		prompt_view = window.show_input_panel(prompt, display_list, None, self.on_change, self.on_cancel)
		sel = prompt_view.sel()
		sel.clear()
		sel.add(sublime.Region(0, prompt_view.size()))

	def on_change(self, text):
		stamp = time.time()
		self.stamp = stamp
		sublime.set_timeout(lambda: self.highlight(text, stamp), 500)

	def highlight(self, text, stamp):
		# print('highlight text', text)
		# print('highlight stamp', stamp)
		if self.stamp != stamp:
			return

		view = self.view
		words = self.get_words(text)
		# print('highlight words', words)

		size = 0
		flag = 0
		color_switch = 0

		if not USE_REGEX:
			flag |= sublime.LITERAL
		if IGNORE_CASE:
			flag |= sublime.IGNORECASE

		word_set = set()
		added_regions = set()

		for word in words:
			if isinstance( word, list ):
				for regexmatch in word:
					regions = []

					# print('color_switch', color_switch, )
					try:
						for index in range(1, 100):
							region = regexmatch.span( index )
							if region[0] == -1 and region[1] == -1:
								continue
							regions.append( sublime.Region( region[0], region[1] ) )
					except IndexError:
						pass

					added_regions.update( [ (region.begin(), region.end()) for region in regions] )
					view.add_regions(
							'%s%d' % ( g_regionkey, size ),
							regions,
							SCOPES[color_switch % len(SCOPES)] ,
							'',
							sublime.HIDE_ON_MINIMAP
						)
					size += 1
					color_switch += 1
			else:
				if len(word) < 2: continue
				if word in word_set: continue
				word_set.add(word)

				regions = view.find_all(word, flag)
				added_regions.update( [ (region.begin(), region.end()) for region in regions] )

				view.add_regions(
						'%s%d' % ( g_regionkey, size ),
						regions,
						SCOPES[color_switch % len(SCOPES)] ,
						'',
						sublime.HIDE_ON_MINIMAP
					)
				size += 1
				color_switch += 1

		# trim extra/unrequired regions
		highlight_size = view.settings().get('highlight_size', 0)

		if size < highlight_size:
			for index in range(size, highlight_size):
				view.erase_regions('%s%d' % ( g_regionkey, index ) )

		view.settings().set('highlight_size', size)
		view.settings().set('highlight_text', text)

		state = g_view_selections.setdefault( view.id(), Data( view ) )
		state.add_regions_set( added_regions )

		if state.selected_region_index < len( state.added_regions ):
			active_region = view.get_regions( '%s_active_selection' % g_regionkey )

			if active_region:
				region_borders = (active_region[0].begin(), active_region[0].end())

				if region_borders not in added_regions:
					erase_active_region( view )

		else:
			erase_active_region( view )

		# print('highlight end')

	def on_cancel(self):
		view = self.view
		view, state = State( view )
		view.run_command('unhighlight_words')

		if CLEAR_ON_ESCAPE:
			view.settings().erase('highlight_text')


def erase_active_region(view):
	view.erase_regions( '%s_active_selection' % g_regionkey )
	view.erase_regions( '%s_active_selection_a' % g_regionkey )
	view.erase_regions( '%s_active_selection_b' % g_regionkey )


class SelectNextHighlightedWordCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		view = self.view
		view, state = State( view )
		erase_active_region( view )

		# print("highlight_size", highlight_size)
		if state.added_regions:
			target_points = state.target_points( backwards=False )
			show_regions( view, target_points )


class SelectPreviousHighlightedWordCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		view = self.view
		view, state = State( view )
		erase_active_region( view )

		# print("highlight_size", highlight_size)
		if state.added_regions:
			target_points = state.target_points( backwards=True )
			show_regions( view, target_points )


def show_regions(view, target_points):
	target_region = sublime.Region( target_points[0], target_points[1] )

	border_region_a = sublime.Region( target_points[0] - 1, target_points[0] )
	border_region_b = sublime.Region( target_points[1], target_points[1] + 1 )

	view.add_regions(
			'%s_active_selection' % g_regionkey,
			[target_region],
			ACTIVE_SELECTION_WORD,
			'',
			sublime.DRAW_NO_FILL
		)

	view.add_regions(
			'%s_active_selection_a' % g_regionkey,
			[border_region_a],
			ACTIVE_SELECTION_WORD,
			'',
			0
		)

	view.add_regions(
			'%s_active_selection_b' % g_regionkey,
			[border_region_b],
			ACTIVE_SELECTION_WORD,
			'',
			0
		)

	# print('Showing', target_region)
	view.show( target_region )


class UnhighlightWordsCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		view = self.view
		view, state = State( view )
		erase_active_region( view )

		highlight_size = view.settings().get('highlight_size', 0)
		for index in range(highlight_size):
			view.erase_regions('%s_%d' % ( g_regionkey, index ) )

		view.settings().set('highlight_size', 0)


class HighlightSettingsCommand(sublime_plugin.WindowCommand):
	def run(self):
		names = [
			'Turn [Regular Expression] ' + ('OFF' if USE_REGEX else 'ON'),
			'Turn [Case Sensitive] ' + ('ON' if IGNORE_CASE else 'OFF'),
			'Turn [Whole Word] ' + ('OFF' if WHOLE_WORD else 'ON')
		]
		self.window.show_quick_panel(names, self.on_done)

	def on_done(self, selected):
		if selected == -1:
			return
		settings = sublime.load_settings('HighlightWords.sublime-settings')
		if selected == 0:
			settings.set('use_regex', not USE_REGEX)
		elif selected == 1:
			settings.set('ignore_case', not IGNORE_CASE)
		else:
			settings.set('whole_word', not WHOLE_WORD)
		settings.set('colors_by_scope', SCOPES)
		sublime.save_settings('HighlightWords.sublime-settings')


def highlightGlobalKeywords(view):
	""" See the setting `permanent_highlight_keyword_color_mappings` """
	size = 0
	word_set = set()
	for pair in KEYWORD_MAP:
		word = pair['keyword']
		color = pair['color']
		flag = pair.get('flag', sublime.LITERAL)
		if (word and color):
			if word in word_set:
				continue
			word_set.add(word)
			regions = view.find_all(word, flag)
			view.add_regions('highlight_keyword_%d' % size, regions, color, '', sublime.HIDE_ON_MINIMAP)
			size += 1


def delayedFix():
	time.sleep(0.1)

	window = sublime.active_window()
	view = window.active_view()

	# print('delayedFix running...')
	highlightGlobalKeywords( view )

	highlighter = HighlightWordsCommand( window )
	highlighter.view = view
	highlighter.view_text = view.substr( sublime.Region( 0, view.size() ) )

	highlight_text = view.settings().get('highlight_text', '')
	# print('highlight_text', highlight_text)

	highlighter.stamp = 1
	highlighter.highlight( highlight_text, 1 )


class HighlightKeywordsCommand(sublime_plugin.EventListener):

	def handleTimeout(self, view, stamp):
		if self.stamp != stamp:
			return
		threading.Thread( target=delayedFix ).start()

	def on_modified(self, view):
		stamp = time.time()
		self.stamp = stamp
		sublime.set_timeout(functools.partial(self.handleTimeout, view, stamp), 500)


def get_settings():
	global USE_REGEX
	global IGNORE_CASE
	global WHOLE_WORD
	global UNDER_THE_CURSOR
	global CLEAR_ON_ESCAPE
	global SCOPES
	global KEYWORD_MAP
	global ACTIVE_SELECTION_WORD

	setting = sublime.load_settings('HighlightWords.sublime-settings')
	USE_REGEX = setting.get('use_regex', False)
	IGNORE_CASE = setting.get('ignore_case', False)
	WHOLE_WORD = setting.get('whole_word', False)
	UNDER_THE_CURSOR = setting.get('under_the_cursor', True)
	CLEAR_ON_ESCAPE = setting.get('clear_on_escape', False)
	SCOPES = setting.get('colors_by_scope', SCOPES)
	KEYWORD_MAP = setting.get('permanent_highlight_keyword_color_mappings', [])
	ACTIVE_SELECTION_WORD = setting.get('active_selection_word', "comment")
	return setting

def plugin_loaded():
	get_settings().add_on_change('HighlightWords', get_settings)

def plugin_unloaded():
	get_settings().clear_on_change('HighlightWords')

if not ST3:
	plugin_loaded()
