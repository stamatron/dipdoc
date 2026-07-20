import re

# Declaration extractor for the code line that follows a doc comment.
# It still only looks at a single line, but recognises the common modern
# JS shapes: function declarations, arrow functions, classes, const/let,
# object-literal methods, prototype methods, exports, and imports.

_ID = r'[A-Za-z_$][\w$]*'


def jsExtract(s):
	s = s.strip()
	if not s:
		return
	if re.match(r'^(/\*|//)', s):
		return

	# Peel a leading `export` / `export default` so the patterns below see
	# the bare declaration (e.g. `export const foo = () => {}`).
	s = re.sub(r'^export\s+default\s+', '', s)
	s = re.sub(r'^export\s+', '', s)
	s = re.sub(r'^module\.exports\s*=\s*', '', s)

	res = {'doc': {}}

	# class Foo [extends Bar]
	m = re.match(r'^class\s+(?P<name>' + _ID + r')', s)
	if m:
		res['type'] = 'class'
		res['name'] = m.group('name')
		ext = re.search(r'extends\s+(?P<parent>[\w$.]+)', s)
		if ext:
			res['parent'] = ext.group('parent')
		return res

	# X.prototype.y = function ...
	m = re.match(r'^(?P<parent>.+?)\.prototype\.(?P<name>' + _ID + r')\s*=', s)
	if m and 'function' in s:
		res['type'] = 'function'
		res['name'] = m.group('name')
		res['parent'] = m.group('parent')
		return res

	# function name(...) / async function* name(...)
	m = re.match(r'^(?:async\s+)?function\s*\*?\s*(?P<name>' + _ID + r')\s*\(', s)
	if m:
		res['type'] = 'function'
		res['name'] = m.group('name')
		return res

	# const/let/var name = (...) =>  |  name = arg =>   (arrow function)
	arrow = r'\s*=\s*(?:async\s+)?(?:\([^)]*\)|' + _ID + r')\s*=>'
	m = re.match(r'^(?:const|let|var)\s+(?P<name>' + _ID + r')' + arrow, s)
	if m:
		res['type'] = 'function'
		res['name'] = m.group('name')
		return res

	# parent.name = (...) =>   |   name = (...) =>   (arrow assigned, no decl)
	m = re.match(r'^(?P<parent>(?:' + _ID + r'\.)*)(?P<name>' + _ID + r')' + arrow, s)
	if m:
		res['type'] = 'function'
		res['name'] = m.group('name')
		if m.group('parent'):
			res['parent'] = m.group('parent').rstrip('.')
		return res

	# name: function(...)  |  name: (...) =>   (object-literal method)
	m = re.match(r'^(?P<name>' + _ID + r')\s*:\s*(?:async\s+)?'
		r'(?:function|\([^)]*\)\s*=>|' + _ID + r'\s*=>)', s)
	if m:
		res['type'] = 'function'
		res['name'] = m.group('name')
		return res

	# import / include / require
	m = re.match(r'^.*(?:import|include|require)\s*\(?[\'"]?'
		r'(?P<id>[\w.$/]*)[\'"]?\)?;?$', s)
	if m and m.group('id'):
		res['type'] = 'dependency'
		res['name'] = m.group('id')
		return res

	# this.name =
	m = re.match(r'^this\.(?P<name>' + _ID + r')\s*=(?!=)', s)
	if m:
		res['type'] = 'field'
		res['name'] = m.group('name')
		res['parent'] = 'this'
		return res

	# const/let/var name =   (plain field)
	m = re.match(r'^(?:const|let|var)\s+(?P<name>' + _ID + r')\s*=(?!=)', s)
	if m:
		res['type'] = 'field'
		res['name'] = m.group('name')
		return res

	# parent.name =  |  name =   (plain assignment field)
	m = re.match(r'^(?P<parent>(?:' + _ID + r'\.)*)(?P<name>' + _ID + r')\s*=(?!=)', s)
	if m:
		res['type'] = 'field'
		res['name'] = m.group('name')
		if m.group('parent'):
			res['parent'] = m.group('parent').rstrip('.')
		return res


fn = jsExtract

comments = {}
comments['pref'] = r'/\*'
comments['suf'] = r'\*/'
comments['decor'] = r'\*'
comments['single'] = '//'
