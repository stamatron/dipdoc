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

def buildTagParsingRegexp(l):
	res = []
	for i in l:
		res.append('((?P<'+i['name']+'>'+i['pref']+r'[\w]+)(?P<'+i['name']+'_rest>.*))');
	return '|'.join(res)

# Long, but deliberately single-pass: docs + code line parsed in one walk.
def getCommentData(uri, tags, decl, extension='js',pref=r'/\*', suf=r'\*/', decor=r'\*', sing='//'):
	eset = {'header':{}, 'content':[]}
	reg_str = buildTagParsingRegexp(tags)
	tag_re = re.compile(reg_str)
	strip_re = re.compile("^"+decor+r"?\s?(?P<stripped>.*)")

	flag = False
	one_more = False
	first = None
	e = {}
	lines = 0
	sloc = 0

	f = open(uri, 'r')
	for line in f:
		lines += 1
		
		stripped = line.strip()

		start = re.match('^'+pref+'(.*)', stripped)
		if start is not None:
			flag = True;
			e = {}
			for tag in tags:
				e[tag['name']] = {}

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

			if 'doc' in e and 'description' in e['doc']:
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

			fn_info = lang[extension](stripped)
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


		if end is not None:
			one_more = True;

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

def emitMarkdown(collector):
	"""Render the collector as plain Markdown so output is viewable without
	the (unfinished) browser reader."""
	out = []
	for lang, container in collector.items():
		data = container.get('data', {})
		for mid in sorted(data):
			module = data[mid]
			out.append('# %s' % mid)
			hdr = module.get('header') or {}
			for d in hdr.get('description') or []:
				out.append('')
				out.append(d)

			for entry in module.get('content') or []:
				name = entry.get('name') or '(anonymous)'
				typ = entry.get('type') or ''
				out.append('')
				out.append('## `%s`%s' % (name, ' — %s' % typ if typ else ''))
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

# Execute captured $assert blocks with Node. The documented symbol must be
# resolvable at module top level (the source file is loaded verbatim), so this
# runs against self-contained modules / fixtures, not framework code that needs
# a runtime. Returns (passed, failed, modules_tested).
def runAsserts(collector):
	import subprocess
	import tempfile
	import shutil

	node = shutil.which('node')
	if node is None:
		print('node not found on PATH; cannot execute $assert blocks')
		return (0, 0, 0)

	passed = failed = tested = 0
	for lang, container in collector.items():
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
					checks.append(_checkBlock('%s::%s#%d' % (mid, name, j), a, name, prepares))

			uri = (module.get('header') or {}).get('uri')
			if not checks or not uri or not os.path.exists(uri):
				continue
			tested += 1

			with open(uri) as f:
				source = f.read()
			js = _HARNESS_HEAD + source + '\n' + '\n'.join(checks) + \
				'\nconsole.log(JSON.stringify(__results));\n'

			path = None
			try:
				with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as tf:
					tf.write(js)
					path = tf.name
				proc = subprocess.run([node, path], capture_output=True,
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
		help='execute captured $assert blocks with Node and report pass/fail')
	args = p.parse_args(argv)

	if not os.path.isdir(args.root):
		p.error('root %r is not a directory' % args.root)

	langs = [x for x in args.languages.split(',') if x]
	skip = [x for x in args.skip.split(',') if x]
	res = run(args.root, langs, skip, exclude_hidden=not args.include_hidden)

	if args.test:
		passed, failed, tested = runAsserts(res)
		sys.exit(1 if failed else 0)

	if args.output is not None:
		out = args.output
	else:
		ext = 'md' if args.format == 'md' else 'json'
		out = os.path.join(args.root, 'dipdoc.' + ext)
	outputResult(res, out, args.format)

if __name__ == "__main__":
	main()

