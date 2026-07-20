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


if __name__ == '__main__':
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        test_file_header_block(tmp)
        test_function_content(tmp)
        test_js_extract()
        test_parse_assert()
        test_assert_execution()
    print('all passed')
