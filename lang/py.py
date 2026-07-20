import re

# Declaration extractor for the code line that follows a doc comment.
# DipDoc attaches a doc block to the line that follows it, so — unlike an
# idiomatic Python docstring, which sits *inside* the def — the block is
# written *before* the declaration:
#
#   """
#   @description does a thing
#   @param {int} x a number
#   """
#   def thing(x): ...
#
# The triple-quoted string is a bare (unused) expression, which is valid
# Python. Single-line "#" comments are recognised too.

_ID = r'[A-Za-z_][A-Za-z0-9_]*'


def pyExtract(s):
	s = s.strip()
	if not s:
		return
	if re.match(r'^#', s):
		return

	res = {'doc': {}}

	# class Foo(Base):
	m = re.match(r'^class\s+(?P<name>' + _ID + r')\s*(?:\((?P<parent>[\w.,\s]*)\))?', s)
	if m:
		res['type'] = 'class'
		res['name'] = m.group('name')
		p = (m.group('parent') or '').strip()
		if p:
			res['parent'] = p.split(',')[0].strip()
		return res

	# [async] def name(...)
	m = re.match(r'^(?:async\s+)?def\s+(?P<name>' + _ID + r')\s*\(', s)
	if m:
		res['type'] = 'function'
		res['name'] = m.group('name')
		return res

	# from x import y  |  import x
	m = re.match(r'^from\s+(?P<id>[\w.]+)\s+import\b', s)
	if m:
		res['type'] = 'dependency'
		res['name'] = m.group('id')
		return res
	m = re.match(r'^import\s+(?P<id>[\w.]+)', s)
	if m:
		res['type'] = 'dependency'
		res['name'] = m.group('id')
		return res

	# self.name = ...   (instance attribute)
	m = re.match(r'^self\.(?P<name>' + _ID + r')\s*=(?!=)', s)
	if m:
		res['type'] = 'field'
		res['name'] = m.group('name')
		res['parent'] = 'self'
		return res

	# name [: type] = ...   (module / class field, optionally annotated)
	m = re.match(r'^(?P<name>' + _ID + r')\s*(?::\s*[\w.\[\], ]+)?\s*=(?!=)', s)
	if m:
		res['type'] = 'field'
		res['name'] = m.group('name')
		return res

	return


fn = pyExtract

comments = {}
comments['pref'] = r'(?:"""|\'\'\')'
comments['suf'] = r'(?:"""|\'\'\')'
comments['decor'] = r''
comments['single'] = r'#'
