![DipDoc - Ultimate Source code documentation and unit testing](logo.png)
======

**DipDoc** reads structured comments out of your source and, in a single pass,
extracts both **documentation** (JSDoc-style `@` tags) and **inline unit tests**
(`$` tags) — the idea being that the docs and the tests that prove them live in
the same comment block.

> Status: early / work in progress. Parser modules ship for JavaScript, PHP,
> Python and Ruby; the JSON/Markdown extractors work, and the `$assert`
> executor runs JavaScript tests (see [Limitations](#limitations)).

## Install

```sh
pip install -e .
```

Installs a `dipdoc` command. (Editable install is the supported path; it keeps
the `lang/` parser modules reachable.) You can also just run `python3 dipdoc.py`
from a checkout.

## Usage

```sh
dipdoc <root-dir> [languages] [options]
```

- `<root-dir>` — directory to scan recursively.
- `languages` — comma-separated list, defaults to `js`. A language `X` requires a
  parser module at `lang/X.py` and scans files ending in `.X`. Shipped modules:
  `js`, `php`, `py`, `rb`.
- `--skip a,b` — paths (relative to `<root-dir>`) to exclude.
- `--include-hidden` — descend into dot-directories (skipped by default).
- `-f, --format {json,js,md}` — `js` (default) wraps JSON as `var dipdoc = {...}`
  for the browser reader; `json` is plain JSON; `md` renders Markdown.
- `-o, --output PATH` — output file, or `-` for stdout. Defaults to
  `<root-dir>/dipdoc.<json|md>`.
- `--test` — execute captured `$assert` blocks with Node and report pass/fail
  (exits non-zero on failure). Requires `node` on `PATH`.

Examples:

```sh
dipdoc examples/ivartech js        # -> examples/ivartech/dipdoc.json (var dipdoc = ...)
dipdoc examples/ivartech js -f md -o docs.md
dipdoc tests js --test             # run the inline unit tests
```

## Comment tags

Doc tags start with `@`, unit-test tags with `$`. Recognised doc tags include:

```
@file @namespace @class @constructor @description @excerpt @group
@param {type} name description        (wrap name in [ ] for optional)
@property {type} name description
@return {type} description
@this @author @copyright @licence @version @link @see @depends
@todo [x] task                        (x/+/* = done, ! = urgent)
@private @public @static @protected
```

Unit-test tags:

```
$prepare  var m1 = ivar.data.Map({...})
$assert   equal this(m1) params('hello', 1) result(true) message
```

A block containing `@file` is treated as the module header; other blocks are
attached to the code line (function / field / dependency) that follows them.

## Languages

Each language has a parser module at `lang/<ext>.py` that supplies the comment
delimiters and a single-line declaration extractor. The doc block always
**precedes** the declaration it documents (this is what "follows them" above
means), so per language:

| Lang | Ext   | Doc block            | Single-line |
|------|-------|----------------------|-------------|
| js   | `.js` | `/* … */`            | `//`        |
| php  | `.php`| `/* … */`            | `//` or `#` |
| py   | `.py` | `""" … """`          | `#`         |
| rb   | `.rb` | `=begin … =end`      | `#`         |

For Python the block is a triple-quoted string written *before* the `def` /
`class` (a bare string expression — valid Python), not the usual docstring
*inside* the body:

```python
"""
@description adds two numbers
@param {int} x first addend
@return {int} the sum
"""
def add(x, y):
    return x + y
```

## Tests

```sh
python3 test_dipdoc.py
```

Framework-free smoke tests: parsing, JS extraction, `$assert` parsing/execution
(via Node, self-skipped if `node` is absent), and the Markdown emitter.

## Limitations

- `$assert` execution is JavaScript-only (it runs the block with Node) and loads
  the module source verbatim, so the documented symbol must resolve at module
  top level. It runs against self-contained modules and fixtures, not code that
  needs a framework runtime. PHP / Python / Ruby extract docs but their
  `$assert` blocks are not executed.
- Single-line declaration extraction: the parser inspects the one line after a
  comment, so multi-line signatures and a declaration hidden behind a decorator
  line (Python `@decorator`, PHP attributes) are not attached. The doc block
  must sit directly above the declaration.
- `java` has no parser module.
- The browser reader (`dipdoc_reader.js`, `template/`) is still incomplete; use
  `-f md` for viewable output in the meantime.

## Author

Nikola Stamatovic Stamat
