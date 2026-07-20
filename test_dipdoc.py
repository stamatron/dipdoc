#!/usr/bin/env python3
# Minimal, framework-free smoke test for the parser.
# Run: python3 test_dipdoc.py   (exit 0 = pass)
#
# Guards the deadlock regression: a comment block carrying an @file tag
# used to null the working entry and then crash on the following code
# line, which hung the whole threaded run.

import importlib.util
import shutil
import dipdoc


def _load_lang(ext):
    spec = importlib.util.spec_from_file_location(ext, 'lang/%s.py' % ext)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    dipdoc.lang[ext] = mod.fn
    dipdoc.comments[ext] = mod.comments
    return mod


def _parse(path, ext='js'):
    c = _load_lang(ext).comments
    return dipdoc.getCommentData(path, dipdoc.tags, dipdoc.decl, ext,
                                 c['pref'], c['suf'], c['decor'], c['single'])


def test_file_header_block(tmp):
    src = tmp + '/hdr.js'
    with open(src, 'w') as f:
        f.write('/**\n'
                ' * @file demo\n'
                ' * @description hello\n'
                ' * @param {string} x the name\n'
                ' */\n'
                'function foo(x) {}\n')
    # Must not raise (this is the deadlock root cause).
    res = _parse(src)
    hdr = res['header']
    assert 'file' in hdr, 'header missing @file'
    assert 'param' in hdr and hdr['param'][0]['name'] == 'x', 'param not parsed'
    assert hdr['param'][0]['type'] == ['string'], 'param type not parsed'
    print('ok: file header block')


def test_function_content(tmp):
    src = tmp + '/fn.js'
    with open(src, 'w') as f:
        f.write('/**\n'
                ' * @description does a thing\n'
                ' */\n'
                'function bar() {}\n')
    res = _parse(src)
    names = [c.get('name') for c in res['content']]
    assert 'bar' in names, 'function name not extracted, got %r' % names
    print('ok: function content')


def test_js_extract():
    ex = _load_lang('js').jsExtract
    cases = [
        ('function foo(x) {}',              'function', 'foo'),
        ('async function bar() {}',         'function', 'bar'),
        ('const baz = (a, b) => a + b;',    'function', 'baz'),
        ('let qux = x => x;',               'function', 'qux'),
        ('export function exported() {}',   'function', 'exported'),
        ('export const arrowExp = () => 1', 'function', 'arrowExp'),
        ('class Widget extends Base {',     'class',    'Widget'),
        ('render: function() {}',           'function', 'render'),
        ('Foo.prototype.bar = function()', 'function', 'bar'),
        ('const N = 42;',                   'field',    'N'),
        ('this.count = 0;',                 'field',    'count'),
    ]
    for line, typ, name in cases:
        r = ex(line)
        assert r is not None, 'no match for %r' % line
        assert r['type'] == typ, '%r: type %r != %r' % (line, r['type'], typ)
        assert r['name'] == name, '%r: name %r != %r' % (line, r['name'], name)
    assert ex('a == b') is None, 'equality mis-parsed as assignment'
    print('ok: js extraction')


def test_back_to_back_blocks(tmp):
    # An @file header block immediately followed by another doc block (no code
    # line between) used to null the entry and crash on the next line. Must
    # parse without raising, for any language, incl. same-delimiter ones.
    src = tmp + '/b2b.py'
    with open(src, 'w') as f:
        f.write('"""\n@file mod\n"""\n'
                '"""\n@description foo\n"""\n'
                'def foo():\n    pass\n')
    _parse(src, 'py')  # must not raise
    print('ok: back-to-back blocks')


def test_php_extract():
    ex = _load_lang('php').fn
    cases = [
        ('class Foo extends Bar {',            'class',      'Foo'),
        ('interface Shape {',                  'class',      'Shape'),
        ('public function doThing($x) {',      'function',   'doThing'),
        ('private static function helper() {', 'function',   'helper'),
        ('require_once "lib.php";',            'dependency', 'lib.php'),
        ('const MAX = 10;',                    'field',      'MAX'),
        ('protected $count = 0;',              'field',      'count'),
    ]
    for line, typ, name in cases:
        r = ex(line)
        assert r is not None, 'no match for %r' % line
        assert r['type'] == typ and r['name'] == name, \
            '%r: got %r/%r' % (line, r.get('type'), r.get('name'))
    assert ex('$this->x == $y') is None, 'equality mis-parsed'
    print('ok: php extraction')


def test_php_content(tmp):
    src = tmp + '/x.php'
    with open(src, 'w') as f:
        f.write('/**\n'
                ' * @description adds numbers\n'
                ' * @param {int} x first\n'
                ' */\n'
                'function add($x, $y) {}\n')
    res = _parse(src, 'php')
    assert 'add' in [c.get('name') for c in res['content']], 'php fn not extracted'
    print('ok: php content')


def test_py_extract():
    ex = _load_lang('py').fn
    cases = [
        ('class Foo(Base):',        'class',      'Foo'),
        ('def thing(x):',           'function',   'thing'),
        ('async def fetch(url):',   'function',   'fetch'),
        ('from os import path',     'dependency', 'os'),
        ('import json',             'dependency', 'json'),
        ('MAX = 10',                'field',      'MAX'),
        ('total: int = 0',          'field',      'total'),
    ]
    for line, typ, name in cases:
        r = ex(line)
        assert r is not None, 'no match for %r' % line
        assert r['type'] == typ and r['name'] == name, \
            '%r: got %r/%r' % (line, r.get('type'), r.get('name'))
    assert ex('a == b') is None, 'equality mis-parsed'
    print('ok: py extraction')


def test_py_content(tmp):
    # Doc block precedes the declaration; triple-quote opens and closes it.
    src = tmp + '/x.py'
    with open(src, 'w') as f:
        f.write('"""\n'
                '@description adds numbers\n'
                '@param {int} x first\n'
                '"""\n'
                'def add(x, y):\n'
                '    return x + y\n')
    res = _parse(src, 'py')
    names = [c.get('name') for c in res['content']]
    assert 'add' in names, 'py fn not extracted, got %r' % names
    print('ok: py content')


def test_py_content_inbody(tmp):
    # Idiomatic docstring: the block sits *inside* the def/class body, so it
    # documents the preceding declaration, not the line after the block.
    src = tmp + '/inbody.py'
    with open(src, 'w') as f:
        f.write('def add(x, y):\n'
                '\t"""\n'
                '\t@description adds numbers\n'
                '\t@param {int} x first\n'
                '\t"""\n'
                '\treturn x + y\n'
                '\n'
                'class Widget:\n'
                '\t"""\n'
                '\t@description a widget\n'
                '\t"""\n'
                '\tcount = 0\n'
                '\n'
                '\tdef draw(self):\n'
                '\t\t"""\n'
                '\t\t@description draws it\n'
                '\t\t"""\n'
                '\t\treturn True\n')
    res = _parse(src, 'py')
    by = {c.get('name'): c for c in res['content']}
    assert 'add' in by and by['add'].get('type') == 'function', \
        'in-body def not attached, got %r' % list(by)
    assert by['add']['doc']['description'][-1] == 'adds numbers', \
        'in-body doc mis-attached: %r' % by['add']['doc'].get('description')
    assert 'Widget' in by and by['Widget'].get('type') == 'class', \
        'in-body class docstring not attached, got %r' % list(by)
    assert 'draw' in by and by['draw'].get('type') == 'function', \
        'in-body method docstring not attached, got %r' % list(by)
    # The field on the body line after the class docstring must NOT steal it.
    assert by['Widget']['doc']['description'][-1] == 'a widget', \
        'class docstring lost to following field: %r' % by['Widget']['doc'].get('description')
    print('ok: py content in-body')


def test_rb_extract():
    ex = _load_lang('rb').fn
    cases = [
        ('class Foo < Bar',              'class',      'Foo'),
        ('module Helpers',               'class',      'Helpers'),
        ('def thing(x)',                 'function',   'thing'),
        ('def self.build',              'function',   'build'),
        ('def valid?',                   'function',   'valid?'),
        ("require 'json'",               'dependency', 'json'),
        ('attr_accessor :count, :name', 'field',      'count'),
        ('MAX = 10',                     'field',      'MAX'),
    ]
    for line, typ, name in cases:
        r = ex(line)
        assert r is not None, 'no match for %r' % line
        assert r['type'] == typ and r['name'] == name, \
            '%r: got %r/%r' % (line, r.get('type'), r.get('name'))
    assert ex('a == b') is None, 'equality mis-parsed'
    print('ok: rb extraction')


def test_rb_content(tmp):
    src = tmp + '/x.rb'
    with open(src, 'w') as f:
        f.write('=begin\n'
                '@description adds numbers\n'
                '@param {Integer} x first\n'
                '=end\n'
                'def add(x, y)\n'
                '  x + y\n'
                'end\n')
    res = _parse(src, 'rb')
    names = [c.get('name') for c in res['content']]
    assert 'add' in names, 'rb fn not extracted, got %r' % names
    print('ok: rb content')


def test_parse_assert():
    a = dipdoc.parseAssert('equal this(ctx) params(2, 3) result(5) two plus three')
    assert a['op'] == 'equal' and not a['not']
    assert a['this'] == 'ctx' and a['params'] == '2, 3' and a['result'] == '5'
    assert a['message'] == 'two plus three'
    n = dipdoc.parseAssert('not equal params(1) result(2)')
    assert n['op'] == 'equal' and n['not'] is True
    print('ok: parse assert')


def test_assert_execution():
    if shutil.which('node') is None:
        print('skip: node not on PATH, cannot run $assert executor')
        return
    res = _parse('tests/fixture.js')
    res['header']['uri'] = 'tests/fixture.js'
    collector = {'js': {'data': {'fixture': res}}}
    passed, failed, tested = dipdoc.runAsserts(collector)
    assert tested == 1, 'expected 1 module tested, got %d' % tested
    assert passed == 4, 'expected 4 passing asserts, got %d' % passed
    assert failed == 1, 'expected 1 failing assert, got %d' % failed
    print('ok: assert execution')


def test_assert_execution_py():
    if shutil.which('python3') is None:
        print('skip: python3 not on PATH')
        return
    res = _parse('tests/fixture.py', 'py')
    res['header']['uri'] = 'tests/fixture.py'
    collector = {'py': {'data': {'fixture': res}}}
    passed, failed, tested = dipdoc.runAsserts(collector)
    assert tested == 1, 'expected 1 module tested, got %d' % tested
    # add(3) + get_value(1) + mul(2, documented in-body) = 6
    assert passed == 6 and failed == 0, 'py asserts: %d passed, %d failed' % (passed, failed)
    print('ok: py assert execution')


def test_assert_execution_rb():
    if shutil.which('ruby') is None:
        print('skip: ruby not on PATH')
        return
    res = _parse('tests/fixture.rb', 'rb')
    res['header']['uri'] = 'tests/fixture.rb'
    collector = {'rb': {'data': {'fixture': res}}}
    passed, failed, tested = dipdoc.runAsserts(collector)
    assert tested == 1, 'expected 1 module tested, got %d' % tested
    assert passed == 4 and failed == 0, 'rb asserts: %d passed, %d failed' % (passed, failed)
    print('ok: rb assert execution')


def test_multiline_prepare(tmp):
    # $prepare spans lines: continuation lines (no tag) append to the prepare
    # body. $assert is one logical line by design.
    src = tmp + '/mp.js'
    with open(src, 'w') as f:
        f.write('/**\n'
                ' * @description exercises a multiline prepare\n'
                ' * $prepare var ctx = {\n'
                ' *   value: 7\n'
                ' * };\n'
                ' * $assert equal this(ctx) result(7)\n'
                ' */\n'
                'function getV() { return this.value; }\n')
    res = _parse(src)
    prep = res['content'][0]['unit']['prepare']
    assert any('value: 7' in p for p in prep), 'multiline prepare lost: %r' % prep
    print('ok: multiline prepare')


def test_emit_markdown(tmp):
    src = tmp + '/md.js'
    with open(src, 'w') as f:
        f.write('/**\n'
                ' * @description does a thing\n'
                ' * @param {string} x the name\n'
                ' * @return {number} a count\n'
                ' */\n'
                'function thing(x) {}\n')
    res = _parse(src)
    collector = {'js': {'data': {'md': res}}}
    out = dipdoc.emitMarkdown(collector)
    assert '## Contents' in out, 'Contents sidebar missing:\n%s' % out
    assert '## Functions' in out, 'Functions section missing:\n%s' % out
    assert '### `thing`' in out, 'function heading missing:\n%s' % out
    assert '**param** `x`' in out, 'param missing:\n%s' % out
    assert '**returns**' in out, 'return missing:\n%s' % out
    print('ok: emit markdown')


def test_emit_markdown_classes(tmp):
    # A class plus a prototype method that names its parent should nest the
    # method under the class in the Contents sidebar and body.
    src = tmp + '/cls.js'
    with open(src, 'w') as f:
        f.write('/**\n * @description a widget\n */\n'
                'class Widget {}\n'
                '/**\n * @description render it\n * @this Widget\n */\n'
                'function draw() {}\n')
    res = _parse(src)
    collector = {'js': {'data': {'cls': res}}}
    out = dipdoc.emitMarkdown(collector)
    assert '## `Widget`' in out, 'class heading missing:\n%s' % out
    assert '### `Widget.draw`' in out, 'method not nested under class:\n%s' % out
    assert '(#widgetdraw)' in out, 'nested TOC anchor missing:\n%s' % out
    print('ok: emit markdown classes')


if __name__ == '__main__':
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        test_file_header_block(tmp)
        test_function_content(tmp)
        test_js_extract()
        test_back_to_back_blocks(tmp)
        test_php_extract()
        test_php_content(tmp)
        test_py_extract()
        test_py_content(tmp)
        test_py_content_inbody(tmp)
        test_rb_extract()
        test_rb_content(tmp)
        test_parse_assert()
        test_assert_execution()
        test_assert_execution_py()
        test_assert_execution_rb()
        test_multiline_prepare(tmp)
        test_emit_markdown(tmp)
        test_emit_markdown_classes(tmp)
    print('all passed')
