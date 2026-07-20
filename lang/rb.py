import re

# Declaration extractor for the code line that follows a doc comment.
# Ruby doc blocks use =begin / =end (which must sit at column 0), e.g.:
#
#   =begin
#   @description does a thing
#   @param {Integer} x a number
#   =end
#   def thing(x); end
#
# Recognises classes/modules, methods, attr_* accessors, require/load
# dependencies, constants, and instance/class variables.

_ID = r'[A-Za-z_][A-Za-z0-9_]*[?!=]?'
_CONST = r'[A-Z][A-Za-z0-9_]*'
_PATH = r'[A-Za-z_][\w:]*'  # Foo::Bar


def rbExtract(s):
	s = s.strip()
	if not s:
		return
	if re.match(r'^#', s):
		return

	res = {'doc': {}}

	# class Foo [< Bar]
	m = re.match(r'^class\s+(?P<name>' + _PATH + r')', s)
	if m:
		res['type'] = 'class'
		res['name'] = m.group('name')
		ext = re.search(r'<\s*(?P<parent>' + _PATH + r')', s)
		if ext:
			res['parent'] = ext.group('parent')
		return res

	# module Foo
	m = re.match(r'^module\s+(?P<name>' + _PATH + r')', s)
	if m:
		res['type'] = 'class'
		res['name'] = m.group('name')
		return res

	# def [self.]name  |  def Klass.name
	m = re.match(r'^def\s+(?:self\.|' + _PATH + r'\.)?(?P<name>' + _ID + r')', s)
	if m:
		res['type'] = 'function'
		res['name'] = m.group('name')
		return res

	# require / require_relative / load / autoload  -> dependency
	m = re.match(r'^(?:require|require_relative|load|autoload)\s+[\'"]'
		r'(?P<id>[\w./]*)', s)
	if m and m.group('id'):
		res['type'] = 'dependency'
		res['name'] = m.group('id')
		return res

	# attr_accessor :a, :b   (first symbol wins)
	m = re.match(r'^attr_(?:accessor|reader|writer)\s+:(?P<name>' + _ID + r')', s)
	if m:
		res['type'] = 'field'
		res['name'] = m.group('name')
		return res

	# CONST = ...
	m = re.match(r'^(?P<name>' + _CONST + r')\s*=(?!=)', s)
	if m:
		res['type'] = 'field'
		res['name'] = m.group('name')
		return res

	# @ivar = ...  |  @@cvar = ...
	m = re.match(r'^@@?(?P<name>' + _ID + r')\s*=(?!=)', s)
	if m:
		res['type'] = 'field'
		res['name'] = m.group('name')
		return res

	return


fn = rbExtract

comments = {}
comments['pref'] = r'=begin'
comments['suf'] = r'=end'
comments['decor'] = r''
comments['single'] = r'#'
