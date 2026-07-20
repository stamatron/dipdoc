import re

# Declaration extractor for the code line that follows a doc comment.
# Single-line, mirroring lang/js.py: recognises the common PHP shapes —
# classes/interfaces/traits, functions/methods, const/define, properties,
# and require/include/use dependencies.

_ID = r'[A-Za-z_][A-Za-z0-9_]*'
_MODS = r'(?:public|protected|private|static|abstract|final|var)\s+'


def phpExtract(s):
	s = s.strip()
	if not s:
		return
	if re.match(r'^(/\*|//|#|\*)', s):
		return

	res = {'doc': {}}

	# [abstract|final] class Foo [extends Bar]  |  interface/trait Foo
	m = re.match(r'^(?:abstract\s+|final\s+)*(?:class|interface|trait)\s+(?P<name>' + _ID + r')', s)
	if m:
		res['type'] = 'class'
		res['name'] = m.group('name')
		ext = re.search(r'extends\s+(?P<parent>[\w\\]+)', s)
		if ext:
			res['parent'] = ext.group('parent')
		return res

	# [visibility] [static] function [&]name(...)
	m = re.match(r'^(?:' + _MODS + r')*function\s+&?\s*(?P<name>' + _ID + r')\s*\(', s)
	if m:
		res['type'] = 'function'
		res['name'] = m.group('name')
		return res

	# require / include / use  -> dependency
	m = re.match(r'^(?:require|require_once|include|include_once|use)\s+[\'"]?'
		r'(?P<id>[\w.\\/]*)', s)
	if m and m.group('id'):
		res['type'] = 'dependency'
		res['name'] = m.group('id')
		return res

	# [visibility] const NAME = ...  |  define('NAME', ...)
	m = re.match(r'^(?:' + _MODS + r')*const\s+(?P<name>' + _ID + r')\s*=(?!=)', s)
	if m:
		res['type'] = 'field'
		res['name'] = m.group('name')
		return res
	m = re.match(r'^define\s*\(\s*[\'"](?P<name>' + _ID + r')[\'"]', s)
	if m:
		res['type'] = 'field'
		res['name'] = m.group('name')
		return res

	# [visibility] [static] $name = ...   (property / field)
	m = re.match(r'^(?:' + _MODS + r')*\$(?P<name>' + _ID + r')\s*=(?!=)', s)
	if m:
		res['type'] = 'field'
		res['name'] = m.group('name')
		return res

	return


fn = phpExtract

comments = {}
comments['pref'] = r'/\*'
comments['suf'] = r'\*/'
comments['decor'] = r'\*'
comments['single'] = r'(?://|#)'
