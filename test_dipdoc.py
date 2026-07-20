#!/usr/bin/env python3
# Minimal, framework-free smoke test for the parser.
# Run: python3 test_dipdoc.py   (exit 0 = pass)
#
# Guards the deadlock regression: a comment block carrying an @file tag
# used to null the working entry and then crash on the following code
# line, which hung the whole threaded run.

import importlib.util
import dipdoc


def _load_lang(ext):
    spec = importlib.util.spec_from_file_location(ext, 'lang/%s.py' % ext)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    dipdoc.lang[ext] = mod.fn
    dipdoc.comments[ext] = mod.comments
    return mod.comments


def _parse(path, ext='js'):
    c = _load_lang(ext)
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


if __name__ == '__main__':
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        test_file_header_block(tmp)
        test_function_content(tmp)
    print('all passed')
