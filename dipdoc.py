#!/usr/bin/env python3
# DipDoc - documentation + inline unit tests extracted in one pass.
# Author: Nikola Stamatovic Stamat
#
# A comment block carries both docs (@ tags) and the unit test that proves
# them ($ tags), e.g.:
#   $prepare var m1 = ivar.data.Map({something: 1})
#   $assert equal this(m1) params('hello', 1) result(true) optional message

import sys
import os
import re
import json
import importlib.util

def importFromURI(uri, absl=False):
	if not absl:
		uri = os.path.normpath(os.path.join(os.path.dirname(__file__), uri))
	if not os.path.exists(uri):
		return None
	mname = os.path.splitext(os.path.basename(uri))[0]
	try:
		spec = importlib.util.spec_from_file_location(mname, uri)
		mod = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(mod)
		return mod
	except Exception:
		return None

def update(d1, d2):
	for k,v in d2.items():
		if k in d1 and type(d1[k]) is dict and type(v) is dict:
			update(d1[k], v)
		else:
			d1[k] = v
	return d1

tags = [{'pref':'@','name':'doc'},
  	{'pref':r'\$','name':'unit'}]

decl = {}
for tag in tags:
	decl[tag['name']] = {}
	

def asIs(s):
	return s
	
def stripNewline(s):
	return s.strip('\n\r')
	
def stripWhitespace(s):
	return s.strip()

def strip(s):
	return s.strip(' \t\n\r')

def stripCurlyBrackets(s):
	return s.strip('{}')
	
def parseParam(s):
	s = s.strip()
	res = {}
	prop = re.match(r'^(\{(?P<type>.*)\})(\s|\t)*(?P<name>(\[(\s|\t)*[a-zA-Z_$][a-zA-Z0-9_$.]*(\s|\t)*(=([0-9.]*|(true|false|undefined|null)|(\{.*\})|(\[.*\])|(".*")|(\'.*\')))?(\s|\t)*\])|([a-zA-Z_$][a-zA-Z0-9_$.]*(\s|\t)*(=([0-9.]*|(true|false|undefined|null)|(\{.*\})|(\[.*\])|(".*")|(\'.*\')))?))(\s|\t)*(?P<description>.*)$', s)
	if prop is not None:
		res['type'] = prop.group('type').split('|')
		res['name'] = prop.group('name').strip()
		res['mandatory'] = True
		mand = re.match(r'^\[(.*)\]$', res['name'])
		if mand is not None:
			res['mandatory'] = False
			res['name'] = mand.group(1)
		res['description'] = prop.group('description')
		return res
	return s
	
decl['doc']['param'] = parseParam

def parseReturn(s):
	s = s.strip()
	res = {}
	prop = re.match(r'^(\{(?P<type>.*)\})(\s|\t)*(?P<description>.*)$', s)
	if prop is not None:
		res['type'] = prop.group('type').split('|')
		res['description'] = prop.group('description')
		return res
	return s
		
decl['doc']['return'] = parseReturn
	
decl['doc']['property'] = parseParam
	
def parseThis(s):
	return stripCurlyBrackets(s.strip())
decl['doc']['this'] = parseThis

decl['doc']['example'] = asIs
decl['doc']['exampledesc'] = stripWhitespace

decl['doc']['description'] = stripWhitespace
decl['doc']['group'] = stripWhitespace
decl['doc']['constructor'] = stripWhitespace

decl['doc']['author'] = stripWhitespace
decl['doc']['copyright'] = stripWhitespace
decl['doc']['licence'] = stripWhitespace
decl['doc']['file'] = stripWhitespace
decl['doc']['namespace'] = stripWhitespace
decl['doc']['version'] = stripWhitespace

decl['doc']['link'] = stripWhitespace
decl['doc']['see'] = stripWhitespace
decl['doc']['depends'] = stripWhitespace #should try to get imports/requires by itself
def parseToDo(s):
	s = s.strip()
	res = {}
	res['complete'] = False
	res['urgent'] = False
	todo = re.match(r'(\[(?P<complete>.*)\])?(\s|\t)*(?P<task>.*)',s)
	if todo is not None:
		res['task'] = todo.group('task')
		if todo.group('complete') is not None:
			c = todo.group('complete').strip()
			if c == 'x' or c == '+' or c == '*':
				res['complete'] = True
			elif c == '!':
				res['urgent'] = True
		return res
	return s
	
decl['doc']['todo'] = parseToDo

def _extractCall(s, key):
	"""Pull `key(...)` out of s with balanced-paren matching.
	Returns (inner_text_or_None, s_with_that_call_removed)."""
	m = re.search(r'\b' + key + r'\s*\(', s)
	if m is None:
		return None, s
	i = m.end()
	depth = 1
	while i < len(s) and depth:
		if s[i] == '(':
			depth += 1
		elif s[i] == ')':
			depth -= 1
		i += 1
	inner = s[m.end():i - 1].strip()
	return inner, (s[:m.start()] + ' ' + s[i:])

# $assert <op> [not] [this(recv)] [params(a, b)] [result(expected)] [message]
#   op = equal | strictEqual | deepEqual | true   ('not' negates)
# The documented symbol is called as `name.apply(recv, [params])` and the
# return value compared to `result` (true = just check truthiness).
def parseAssert(s):
	s = s.strip()
	if not s:
		return s
	res = {'raw': s, 'not': False, 'this': None, 'params': None,
		'result': None, 'message': None, 'op': 'true'}
	res['this'], s = _extractCall(s, 'this')
	res['params'], s = _extractCall(s, 'params')
	res['result'], s = _extractCall(s, 'result')

	words = s.split()
	if words:
		res['op'] = words[0]
		words = words[1:]
	if words and words[0] == 'not':
		res['not'] = True
		words = words[1:]
	if res['op'] == 'not' and words:  # allow `not equal` as well as `equal not`
		res['not'] = True
		res['op'] = words[0]
		words = words[1:]
	res['message'] = ' '.join(words).strip() or None
	return res

decl['unit']['prepare'] = asIs
decl['unit']['assert'] = parseAssert

#Access modifiers
decl['doc']['private'] = asIs
decl['doc']['public'] = asIs
decl['doc']['static'] = asIs
decl['doc']['protected'] = asIs
decl['doc']['class'] = stripWhitespace
decl['doc']['excerpt'] = stripWhitespace

lang = {}
comments = {}

def buildTagParsingRegexp(taglist):
	res = []
	for i in taglist:
		res.append('((?P<'+i['name']+'>'+i['pref']+r'[\w]+)(?P<'+i['name']+'_rest>.*))');
	return '|'.join(res)

# Long, but deliberately single-pass: docs + code line parsed in one walk.
def getCommentData(uri, tags, decl, extension='js',pref=r'/\*', suf=r'\*/', decor=r'\*', sing='//'):
	eset = {'header':{}, 'content':[]}
	reg_str = buildTagParsingRegexp(tags)
	tag_re = re.compile(reg_str)
	# Group the decor so languages with no line decoration can pass decor=''
	# (a bare '^?' is "nothing to repeat" on Python 3.11+).
	strip_re = re.compile("^(?:"+decor+r")?\s?(?P<stripped>.*)")

	flag = False
	one_more = False
	first = None
	e = {}
	lines = 0
	sloc = 0
	# In-body doc blocks (Python docstrings): a block whose *preceding* line is
	# a compound declaration (`def`/`class ...:`) documents THAT line, not the
	# one after it. prev_stripped remembers the immediately previous source
	# line; pre_decl holds it parsed as a declaration when it qualifies.
	prev_stripped = ''
	pre_decl = None

	f = open(uri, 'r')
	for line in f:
		lines += 1

		stripped = line.strip()
		line_raw = stripped

		# Only look for a block-comment opener when not inside a comment body.
		# Languages like Python use the same delimiter (""") to open and
		# close; without this guard the closing line re-matches as a new open.
		# `one_more` is the code-line pass (the block already closed), where a
		# fresh block may legitimately open, so allow the match there.
		start = re.match('^'+pref+'(.*)', stripped) if (not flag or one_more) else None
		if start is not None:
			flag = True;
			e = {}
			for tag in tags:
				e[tag['name']] = {}

			# Docstring style: if the line just above the block is a compound
			# declaration header (ends with ':' and the lang extractor reads it
			# as a class/function), the block documents it. The ':' keeps this
			# to suite-opening headers, so an unrelated preceding one-liner
			# (`def f(): pass`) doesn't get falsely claimed.
			# ponytail: ':' encodes the Python docstring position; other langs
			#   (rb/php docs sit above) simply never match, so no forward-path
			#   regression. Revisit if a colon-suite language needs excluding.
			pre_decl = None
			if prev_stripped.rstrip().endswith(':'):
				cand = lang[extension](prev_stripped)
				if (cand is not None and cand.get('name')
						and cand.get('type') in ('class', 'function')):
					pre_decl = cand

			tag_name = None
			tp = None
			stripped = start.group(1)
		
		#each code line
		single = re.match('^'+sing, stripped)
		if single is None:
			if flag and one_more:
				sloc += 1
			elif not flag and stripped != '':
				sloc += 1

		end = re.match('(.*)'+suf+'$', stripped)
		if end is not None:
			stripped = end.group(1)
			
		#each multiline comment line
		if flag and not one_more:
			
			st = strip_re.match(stripped)
			if st is not None:
				stripped = st.group('stripped')
			else:
				if start is not None:
					stripped = start.group(1)
				elif end is not None:
					stripped = end.group(1)
				else:
					stripped = line
			
			if tag_name is None:
				tag_name = 'description'
				tp = 'doc'

			tag_data = parseCommentLine(stripped, tags, tag_re)

			if tag_data is not None and type(tag_data) is dict:
				tp = tag_data['type']
				tag_name = tag_data['name']	

			if tag_name not in e[tp] and tag_name in decl[tp]:
				e[tp][tag_name] = []
			if tag_data is not None and type(tag_data) is dict:
				res = None
				if tag_name in decl[tp]:
					res = decl[tp][tag_name](tag_data['rest'])
				if res is not None:
					e[tp][tag_name].append(res)

			else:
				if tag_name in decl[tp]:
					stripped = decl[tp][tag_name](stripped)
					ln = len(e[tp][tag_name])
					if stripped is not None:
						if ln > 0:
							dtype = type(e[tp][tag_name][ln-1])
							if dtype is dict and 'description' in e[tp][tag_name][ln-1] and e[tp][tag_name][ln-1]['description'] is not None:
								e[tp][tag_name][ln-1]['description']+='\n'+stripped
							elif dtype is str:	
								e[tp][tag_name][ln-1]+= '\n'+stripped
						else:
							e[tp][tag_name].append(stripped)

		#On last line, that usualy contains the function, class or field related to the documentation
		if one_more:

			if e is not None and 'doc' in e and 'description' in e['doc']:
				for i, el in enumerate(e['doc']['description']):
					e['doc']['description'][i] = e['doc']['description'][i].strip('\n')
				if 'excerpt' not in e['doc']:
					e['doc']['excerpt'] = [e['doc']['description'][0].split('\n')[0]]	

			if first is None and e is not None and 'doc' in e and e['doc'] is not None:
				first = e['doc']
			if not eset['header']:
				if e is not None and 'doc' in e:
					for tag in e['doc']:
						if 'file' in tag:
							eset['header'] = e['doc'];
							e = None
							break

			# Prefer the preceding declaration (docstring style); otherwise
			# the block documents the following code line (the default).
			fn_info = pre_decl if pre_decl is not None else lang[extension](stripped)
			# e is None when this block was consumed as the file header
			# above; nothing to attach it to, so skip it as content
			if e is not None and fn_info is not None and 'name' in fn_info:
				update(e, fn_info)
			else:
				e = None

			if flag and e is not None:
				eset['content'].append(e)

			one_more = False
			flag = False
			pre_decl = None


		if end is not None:
			one_more = True;

		prev_stripped = line_raw

	if not eset['header'] and first is not None:
		if 'file' not in first and 'name' not in first:
			first['file'] = []
		eset['header'] = first
	
	if 'file' in eset['header']:
		eset['header']['lines'] = lines
		eset['header']['sloc'] = sloc-1
	return eset

def parseCommentLine(line, tags, tag_re):
	res = {
		'type': None,
		'name': None,
		'rest': None
	}
	s = tag_re.match(line)
	if s is not None:
		for tag in tags:
			if s.group(tag['name']) is not None:
				res['type'] = tag['name']
				break
		res['name'] = s.group(res['type'])[1:]
		res['rest'] = s.group(res['type']+'_rest')
		
		return res
	return line

def doFile(root, uri, collector, extension='js'):
	ext = '.'+extension
	if uri.endswith(ext):
		if not root.endswith(os.sep):
			root += os.sep
		iden = '.'.join(uri[len(root):-len(ext)].split(os.sep))
		result = getCommentData(uri, tags, decl, extension, comments[extension]['pref'], comments[extension]['suf'], comments[extension]['decor'], comments[extension]['single'])
		if not result['content'] and not result['header']:
			return
		result['header']['uri'] = uri
		result['header']['id'] = iden
		collector[iden] = result

def doForAllLangs(res, url, ex, skip=[], exclude_hidden=True):

	data = {}
	errors = 0

	# Serial walk. Parsing is I/O + regex under the GIL, so threads bought
	# nothing here and the old q.join()-per-directory turned one parse error
	# into a hang. A plain loop is simpler and just as fast.
	for root, dirs, files in os.walk(url):
		if exclude_hidden:
			# slice-assign: mutating dirs in place prunes the walk, but
			# removing during iteration skips elements
			dirs[:] = [d for d in dirs if not d.startswith('.')]

		if root in skip:
			dirs[:] = []
			continue

		for f in files:
			fpath = os.path.join(root, f)
			if fpath in skip:
				continue

			try:
				doFile(url, fpath, data, ex)
			except Exception as e:
				errors += 1
				print('error parsing %s: %s' % (fpath, e))

	print('%s: %d module(s) parsed, %d error(s)' % (ex, len(data), errors))
	res[ex] = {
		'data': data,
		'details': {'lang': ex, 'root': url},
	}

def _slug(s):
	"""GitHub-flavoured heading anchor: lowercase, punctuation dropped,
	spaces to hyphens. Good enough for in-doc Contents links."""
	s = s.lower().replace(' ', '-')
	return re.sub(r'[^a-z0-9\-_]', '', s)

def _first(v):
	return v[0] if isinstance(v, list) and v else v

def _ownerOf(entry):
	"""Which class/group an entry belongs to: explicit @this/@group/@class
	wins, else the extractor-supplied parent (e.g. Foo.prototype.bar)."""
	doc = entry.get('doc') or {}
	for key in ('this', 'group', 'class'):
		v = _first(doc.get(key))
		if isinstance(v, str) and v.strip():
			return v.strip()
	return entry.get('parent')

def _groupModule(module):
	"""Bucket a module's content by class. Classes are the type=='class'
	entries; a function/field is nested under a class when its owner matches,
	otherwise it stays module-level. Dependencies are always module-level.
	(Scope isn't tracked across the single-line extractor, so a method only
	nests when @this/@group/@parent names its class.)"""
	from collections import OrderedDict
	classes = OrderedDict()
	top = {'function': [], 'field': [], 'dependency': []}
	content = module.get('content') or []
	for e in content:
		if e.get('type') == 'class':
			classes.setdefault(e.get('name'), {'entry': e, 'function': [], 'field': []})
	for e in content:
		t = e.get('type')
		if t == 'class':
			continue
		owner = _ownerOf(e)
		if t in ('function', 'field') and owner in classes:
			classes[owner][t].append(e)
		elif t in top:
			top[t].append(e)
	return classes, top

def _emitEntry(out, entry, level):
	name = entry.get('name') or '(anonymous)'
	out.append('')
	out.append('%s `%s`' % ('#' * level, name))
	doc = entry.get('doc') or {}
	for d in doc.get('description') or []:
		out.append('')
		out.append(d)
	for prm in doc.get('param') or []:
		if isinstance(prm, dict):
			t = '|'.join(prm.get('type') or [])
			out.append('- **param** `%s`%s — %s' % (
				prm.get('name', ''), ' {%s}' % t if t else '',
				prm.get('description', '')))
	for ret in doc.get('return') or []:
		if isinstance(ret, dict):
			t = '|'.join(ret.get('type') or [])
			out.append('- **returns**%s — %s' % (
				' {%s}' % t if t else '', ret.get('description', '')))
	for a in (entry.get('unit') or {}).get('assert') or []:
		if isinstance(a, dict):
			out.append('- _assert_: `%s`' % a.get('raw', ''))

def emitMarkdown(collector):
	"""Render the collector as Markdown: a per-module header, a Contents
	sidebar (functions grouped under their class/module), then the sections."""
	out = []
	for lang, container in collector.items():
		data = container.get('data', {})
		for mid in sorted(data):
			module = data[mid]
			classes, top = _groupModule(module)
			out.append('# %s' % mid)
			hdr = module.get('header') or {}
			for d in hdr.get('description') or []:
				out.append('')
				out.append(d)
			for key, label in (('author', 'Author'), ('version', 'Version'),
					('licence', 'Licence')):
				vals = hdr.get(key)
				if vals:
					out.append('')
					out.append('**%s:** %s' % (label, ', '.join(vals)))

			# Contents sidebar — classes (with their members), then top-level.
			toc = []
			for nm, grp in classes.items():
				toc.append('- [`%s`](#%s)' % (nm, _slug(nm)))
				for e in grp['function'] + grp['field']:
					en = e.get('name') or ''
					toc.append('  - [`%s`](#%s)' % (en, _slug(nm + '.' + en)))
			for e in top['function']:
				en = e.get('name') or ''
				toc.append('- [`%s`](#%s)' % (en, _slug(en)))
			if toc:
				out.append('')
				out.append('## Contents')
				out.append('')
				out.extend(toc)

			# Classes and their members.
			for nm, grp in classes.items():
				ce = grp['entry']
				out.append('')
				parent = ce.get('parent')
				out.append('## `%s`%s' % (nm, ' extends `%s`' % parent if parent else ''))
				for d in (ce.get('doc') or {}).get('description') or []:
					out.append('')
					out.append(d)
				for e in grp['function'] + grp['field']:
					# nest anchor under the class: heading `Class.member`
					e2 = dict(e)
					e2['name'] = '%s.%s' % (nm, e.get('name'))
					_emitEntry(out, e2, 3)

			# Top-level functions and fields.
			if top['function']:
				out.append('')
				out.append('## Functions')
				for e in top['function']:
					_emitEntry(out, e, 3)
			if top['field']:
				out.append('')
				out.append('## Fields')
				for e in top['field']:
					_emitEntry(out, e, 3)
			if top['dependency']:
				out.append('')
				out.append('## Dependencies')
				out.append('')
				for e in top['dependency']:
					out.append('- `%s`' % (e.get('name') or ''))
			out.append('')
	return '\n'.join(out).strip() + '\n'

def outputResult(collector, out=None, fmt='js'):
	if fmt == 'md':
		body = emitMarkdown(collector)
	else:
		body = json.dumps(collector, indent=4)
		if fmt == 'js':
			# 'js' wraps the JSON so the browser reader can <script src> it
			body = 'var dipdoc = ' + body
	if out is None or out == '-':
		sys.stdout.write(body + '\n')
	else:
		with open(out, 'w') as f:
			f.write(body)

def run(url, langs=['js'], skip=[], exclude_hidden=True):
	res = {}

	modskip = []
	for i in skip:
		modskip.append(os.path.join(url, i))
	skip = modskip

	for ex in langs:
		mod = importFromURI('lang/'+ex+'.py')
		if mod is None:
			print('warning: no parser module for language %r (lang/%s.py); skipping' % (ex, ex))
			continue
		lang[ex] = mod.fn
		comments[ex] = mod.comments
		doForAllLangs(res, url, ex, skip, exclude_hidden)

	return res

_ASSERT_OPS = {
	'equal': ('equal', 'notEqual'),
	'strictEqual': ('strictEqual', 'notStrictEqual'),
	'deepEqual': ('deepEqual', 'notDeepEqual'),
}

def _assertStmt(a):
	op = a.get('op')
	neg = bool(a.get('not'))
	if op == 'true':
		return 'assert.ok(%s__actual);' % ('!' if neg else '')
	if op not in _ASSERT_OPS:
		return 'throw new Error(%s);' % json.dumps('unknown assert op: ' + str(op))
	fn = _ASSERT_OPS[op][1 if neg else 0]
	expected = a.get('result')
	return 'assert.%s(__actual, %s);' % (fn, expected if expected is not None else 'undefined')

def _checkBlock(label, a, name, prepares):
	recv = a.get('this') or 'null'
	args = '[' + (a.get('params') or '') + ']'
	body = list(prepares)
	body.append('var __actual = %s.apply(%s, %s);' % (name, recv, args))
	body.append(_assertStmt(a))
	return '__check(%s, function(){\n%s\n});' % (
		json.dumps(label), '\n'.join('  ' + line for line in body))

_HARNESS_HEAD = '''const assert = require('assert');
const __results = [];
function __check(label, fn){
  try { fn(); __results.push({label: label, ok: true}); }
  catch (e) { __results.push({label: label, ok: false, error: String((e && e.message) || e)}); }
}
'''

def _js_script(source, checks, uri):
	body = '\n'.join(_checkBlock(*c) for c in checks)
	return _HARNESS_HEAD + source + '\n' + body + \
		'\nconsole.log(JSON.stringify(__results));\n'

# --- Python / Ruby share the same shape: run the source verbatim, then a
# try/except (begin/rescue) per assertion that records {label, ok, error}.
# `this(recv)` binds the receiver by passing it as the leading argument
# (self / the explicit receiver), so a documented `def f(self, ...)` /
# `def f(obj, ...)` is exercised as `f(recv, ...)`.

# $prepare lines are treated as flat, statement-level setup: each line is
# left-stripped so it re-indents cleanly under the harness's try/begin block.
# ponytail: no nested-indentation prepares; keep setup to single statements.
def _flatLines(prepares):
	out = []
	for p in prepares:
		out.extend(ln.strip() for ln in p.split('\n'))
	return out

def _freeCall(a, name):
	args = (a.get('params') or '').strip()
	recv = a.get('this')
	if recv:
		args = recv + (', ' + args if args else '')
	return '%s(%s)' % (name, args)

def _py_assert(a):
	op = a.get('op')
	neg = bool(a.get('not'))
	if op == 'true':
		return 'assert (not __actual)' if neg else 'assert __actual'
	expected = a.get('result')
	expected = expected if expected is not None else 'None'
	return 'assert __actual %s %s' % ('!=' if neg else '==', expected)

def _py_script(source, checks, uri):
	parts = ['import json\n__results = []\n', source, '']
	for label, a, name, prepares in checks:
		block = ['try:']
		block += ['\t' + ln for ln in _flatLines(prepares)]
		block.append('\t__actual = %s' % _freeCall(a, name))
		block.append('\t' + _py_assert(a))
		block.append('\t__results.append({"label": %s, "ok": True})' % json.dumps(label))
		block.append('except Exception as __e:')
		block.append('\t__results.append({"label": %s, "ok": False, "error": str(__e)})' % json.dumps(label))
		parts.append('\n'.join(block))
	parts.append('print(json.dumps(__results))')
	return '\n'.join(parts) + '\n'

def _rb_assert(a):
	op = a.get('op')
	neg = bool(a.get('not'))
	if op == 'true':
		return 'raise "not truthy" unless %s__actual' % ('!' if neg else '')
	expected = a.get('result')
	expected = expected if expected is not None else 'nil'
	return 'raise "got #{__actual.inspect}" unless __actual %s %s' % (
		'!=' if neg else '==', expected)

def _rb_script(source, checks, uri):
	parts = ["require 'json'\n__results = []\n", source, '']
	for label, a, name, prepares in checks:
		block = ['begin']
		block += ['\t' + ln for ln in _flatLines(prepares)]
		block.append('\t__actual = %s' % _freeCall(a, name))
		block.append('\t' + _rb_assert(a))
		block.append('\t__results << {label: %s, ok: true}' % json.dumps(label))
		block.append('rescue => __e')
		block.append('\t__results << {label: %s, ok: false, error: __e.message}' % json.dumps(label))
		block.append('end')
		parts.append('\n'.join(block))
	parts.append('puts __results.to_json')
	return '\n'.join(parts) + '\n'

# PHP source carries its own `<?php` tag, so require the file rather than
# inlining it; the receiver binds as a method call `$recv->name(...)`.
def _php_assert(a):
	op = a.get('op')
	neg = bool(a.get('not'))
	if op == 'true':
		return 'if (%s$__actual) {} else { throw new Exception("not truthy"); }' % (
			'!' if neg else '')
	cmp = {'equal': '==', 'strictEqual': '===', 'deepEqual': '=='}.get(op, '==')
	if neg:
		cmp = '!=' if cmp == '==' else '!=='
	expected = a.get('result')
	expected = expected if expected is not None else 'null'
	return 'if ($__actual %s %s) {} else { throw new Exception("mismatch"); }' % (cmp, expected)

def _php_script(source, checks, uri):
	parts = ['<?php', '$__results = array();', 'require %s;' % json.dumps(uri)]
	for label, a, name, prepares in checks:
		recv = a.get('this')
		args = (a.get('params') or '').strip()
		call = '$%s->%s(%s)' % (recv, name, args) if recv else '%s(%s)' % (name, args)
		block = ['try {']
		block += ['\t' + ln for ln in _flatLines(prepares)]
		block.append('\t$__actual = %s;' % call)
		block.append('\t' + _php_assert(a))
		block.append('\t$__results[] = array("label" => %s, "ok" => true);' % json.dumps(label))
		block.append('} catch (Throwable $__e) {')
		block.append('\t$__results[] = array("label" => %s, "ok" => false, "error" => $__e->getMessage());' % json.dumps(label))
		block.append('}')
		parts.append('\n'.join(block))
	parts.append('echo json_encode($__results);')
	return '\n'.join(parts) + '\n'

# Per-language test runners. Adding a language = one entry (interpreter binary,
# temp-file suffix, script builder). Each builder emits a self-contained program
# that loads the module source, runs every captured $assert, and prints a JSON
# array of {label, ok, error} on stdout.
_RUNNERS = {
	'js':  {'bin': 'node',    'suffix': '.js',  'script': _js_script},
	'py':  {'bin': 'python3', 'suffix': '.py',  'script': _py_script},
	'rb':  {'bin': 'ruby',    'suffix': '.rb',  'script': _rb_script},
	'php': {'bin': 'php',     'suffix': '.php', 'script': _php_script},
}

# Execute captured $assert blocks in the module's own language. The documented
# symbol must be resolvable at module top level (the source file is loaded
# verbatim / required), so this runs against self-contained modules / fixtures,
# not framework code that needs a runtime. `bins` maps a language to an
# interpreter path, overriding the PATH lookup. Returns (passed, failed,
# modules_tested).
def runAsserts(collector, bins=None):
	import subprocess
	import tempfile
	import shutil

	bins = bins or {}
	passed = failed = tested = 0
	for lang, container in collector.items():
		runner = _RUNNERS.get(lang)
		if runner is None:
			print('no $assert runner for language %r; skipping' % lang)
			continue
		binpath = (bins.get(lang) or os.environ.get('DIPDOC_%s_BIN' % lang.upper())
			or shutil.which(runner['bin']))
		if binpath is None:
			print('%s not found on PATH; cannot execute %s $assert blocks'
				% (runner['bin'], lang))
			continue

		for mid, module in container.get('data', {}).items():
			checks = []
			for entry in module.get('content', []):
				unit = entry.get('unit') or {}
				asserts = [a for a in (unit.get('assert') or []) if isinstance(a, dict)]
				name = entry.get('name')
				if not asserts or not name:
					continue
				prepares = unit.get('prepare') or []
				for j, a in enumerate(asserts):
					checks.append(('%s::%s#%d' % (mid, name, j), a, name, prepares))

			uri = (module.get('header') or {}).get('uri')
			if not checks or not uri or not os.path.exists(uri):
				continue
			tested += 1

			with open(uri) as f:
				source = f.read()
			script = runner['script'](source, checks, os.path.abspath(uri))

			path = None
			try:
				with tempfile.NamedTemporaryFile('w', suffix=runner['suffix'], delete=False) as tf:
					tf.write(script)
					path = tf.name
				proc = subprocess.run([binpath, path], capture_output=True,
					text=True, timeout=30)
			finally:
				if path:
					os.unlink(path)

			out = proc.stdout.strip().splitlines()
			if proc.returncode != 0 and not out:
				tail = proc.stderr.strip().splitlines()
				print('  FAIL %s (load): %s' % (mid, tail[-1] if tail else 'exit %d' % proc.returncode))
				failed += 1
				continue
			try:
				results = json.loads(out[-1])
			except Exception:
				print('  FAIL %s: could not read test results' % mid)
				failed += 1
				continue
			for r in results:
				if r.get('ok'):
					passed += 1
					print('  PASS %s' % r['label'])
				else:
					failed += 1
					print('  FAIL %s: %s' % (r['label'], r.get('error')))

	print('asserts: %d passed, %d failed (%d module(s) with tests)' % (passed, failed, tested))
	return (passed, failed, tested)

def main(argv=None):
	import argparse
	if argv is None:
		argv = sys.argv[1:]
	p = argparse.ArgumentParser(
		prog='dipdoc',
		description='Extract JSDoc-style docs and inline unit tests from source.')
	p.add_argument('root', help='directory to scan recursively')
	p.add_argument('languages', nargs='?', default='js',
		help='comma-separated languages (default: js); needs lang/<X>.py')
	p.add_argument('--skip', default='',
		help='comma-separated paths (relative to root) to exclude')
	p.add_argument('--include-hidden', action='store_true',
		help='descend into dot-directories (excluded by default)')
	p.add_argument('-o', '--output',
		help='output path; "-" for stdout (default: <root>/dipdoc.json)')
	p.add_argument('-f', '--format', choices=['json', 'js', 'md'], default='js',
		help='json = plain JSON, js = "var dipdoc = {...}", md = Markdown (default: js)')
	p.add_argument('--test', action='store_true',
		help='execute captured $assert blocks in each language and report pass/fail')
	p.add_argument('--bin', action='append', default=[], metavar='LANG=PATH',
		help='interpreter path for a language, e.g. --bin py=/usr/bin/python3 '
		'(also read from DIPDOC_<LANG>_BIN); default is found on PATH')
	args = p.parse_args(argv)

	if not os.path.isdir(args.root):
		p.error('root %r is not a directory' % args.root)

	langs = [x for x in args.languages.split(',') if x]
	skip = [x for x in args.skip.split(',') if x]
	res = run(args.root, langs, skip, exclude_hidden=not args.include_hidden)

	if args.test:
		bins = {}
		for spec in args.bin:
			k, _, v = spec.partition('=')
			if v:
				bins[k] = v
		passed, failed, tested = runAsserts(res, bins)
		sys.exit(1 if failed else 0)

	if args.output is not None:
		out = args.output
	else:
		ext = 'md' if args.format == 'md' else 'json'
		out = os.path.join(args.root, 'dipdoc.' + ext)
	outputResult(res, out, args.format)

if __name__ == "__main__":
	main()

