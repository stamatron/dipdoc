![DipDoc - Ultimate Source code documentation and unit testing](logo.png)
======

**DipDoc** reads structured comments out of your source and, in a single pass,
extracts both **documentation** (JSDoc-style `@` tags) and **inline unit tests**
(`$` tags) — the idea being that the docs and the tests that prove them live in
the same comment block.

> Status: early / work in progress. Parser modules ship for JavaScript, PHP,
> Python and Ruby; the JSON/Markdown extractors work, and the `$assert`
> executor runs tests in each of those languages (see
> [Running the tests](#running-the-inline-unit-tests) and
> [Limitations](#limitations)).

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
- `--test` — execute captured `$assert` blocks in the module's own language and
  report pass/fail (exits non-zero on failure). Needs that language's
  interpreter (`node` / `python3` / `ruby` / `php`) on `PATH`.
- `--bin LANG=PATH` — interpreter path for a language (repeatable), e.g.
  `--bin py=/usr/bin/python3`. Also read from `DIPDOC_<LANG>_BIN` (e.g.
  `DIPDOC_PHP_BIN`). Defaults to whatever is found on `PATH`.

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

- **`$prepare`** is setup code run before the assertion, written in the module's
  own language. It **can span multiple lines** — continuation lines (that don't
  start a new tag) are appended to the current `$prepare`. Keep each line a flat
  statement (leading indentation is stripped when the harness re-indents it).
- **`$assert`** is one logical assertion: `<op> [not] [this(recv)] [params(...)]
  [result(expected)] [message]`, where `op` is `equal` / `strictEqual` /
  `deepEqual` / `true`. It **may wrap across lines** — continuation lines (that
  don't start a new tag) are joined back into the one assertion and re-parsed, so
  a long `params(...)` or message can span lines. Still one assertion per
  `$assert`; write a new `$assert` for the next one.
- `this(recv)` binds the receiver: JS calls `name.apply(recv, params)`; Python
  and Ruby pass `recv` as the leading argument (`name(recv, ...)`, matching an
  explicit `self` / receiver param); PHP calls `$recv->name(...)`.
- `params(...)` and `result(...)` are copied verbatim, so write the literals in
  the target language (`result(true)` in JS, `result(True)` in Python, etc.).

A block containing `@file` is treated as the module header; other blocks are
attached to the code line (function / field / dependency) that follows them.

### Running the inline unit tests

`dipdoc <root> <langs> --test` extracts every `$assert` and runs it **in the
language of the module it came from** — no framework needed. Per language the
tool writes a temporary program that loads the module source verbatim (PHP
`require`s it), runs each assertion, and reports pass/fail:

```sh
dipdoc tests js --test                 # runs the JS fixture with node
dipdoc tests py,rb --test              # Python + Ruby fixtures
dipdoc src php --test --bin php=/usr/local/bin/php
```

Because the source is loaded verbatim, **the documented symbol must resolve at
module top level** — this runs against self-contained modules and fixtures, not
code that needs a framework runtime. A language whose interpreter isn't on
`PATH` (and has no `--bin` / `DIPDOC_<LANG>_BIN` override) is skipped with a
notice. See `tests/fixture.{js,py,rb}` for the shape.

`--test` also **bakes each assertion's result** (`ok` / `error`) back into the
generated output, so combining it with `-o` / `-f` carries pass/fail into the
JSON, Markdown, and browser reader — one command produces docs *and* their proof:

```sh
dipdoc tests js --test -o dipdoc.json -f js   # data + baked pass/fail for the reader
dipdoc tests js --test -f md -o docs.md       # Markdown with ✅ / ❌ per assert
```

## Languages

Each language has a parser module at `lang/<ext>.py` that supplies the comment
delimiters and a single-line declaration extractor. The doc block normally
**precedes** the declaration it documents (this is what "follows them" above
means); Python additionally supports an in-body docstring that documents the
`def` / `class` header directly above it. Per language:

| Lang | Ext   | Doc block            | Single-line |
|------|-------|----------------------|-------------|
| js   | `.js` | `/* … */`            | `//`        |
| php  | `.php`| `/* … */`            | `//` or `#` |
| py   | `.py` | `""" … """`          | `#`         |
| rb   | `.rb` | `=begin … =end`      | `#`         |

For Python the block may be written **either** *before* the `def` / `class`
(a bare triple-quoted string expression — valid Python) **or** *inside* the
body as an idiomatic docstring. DipDoc picks the target automatically: a block
whose immediately preceding line is a `def` / `class` header documents that
declaration; otherwise it documents the line that follows. This means you can
point DipDoc at existing code that already uses docstrings.

```python
# above the declaration
"""
@description adds two numbers
@param {int} x first addend
@return {int} the sum
"""
def add(x, y):
    return x + y

# or as an in-body docstring (documents the def above it)
def mul(a, b):
    """
    @description multiplies two numbers
    @param {int} a first factor
    @return {int} the product
    """
    return a * b
```

## Tests

```sh
python3 test_dipdoc.py
```

Framework-free smoke tests: parsing, per-language extraction, `$assert`
parsing and execution for JS / Python / Ruby (each self-skipped if its
interpreter is absent), multiline `$prepare` and `$assert`, baked pass/fail
results, the Markdown emitter, and a headless render of the browser reader
(`tests/reader_smoke.js`, run via `node`, skipped if absent).

## Output structure

`-f md` renders each module as: a header (description + `@author` / `@version` /
`@licence`), a **Contents** sidebar, then sections. Functions and fields are
grouped under a class when the block names it (`@this` / `@group` / `@class`, or
an extractor-supplied parent such as `Foo.prototype.bar`); everything else is
listed module-level under **Functions** / **Fields** / **Dependencies**. Classes
are detected for all four languages (`class` in JS/PHP/Python/Ruby, plus PHP
`interface`/`trait` and Ruby `module`); a source *file* is itself a module.

### Browser reader

`template.html` + `dipdoc_reader.js` are a dependency-free (no jQuery/Bootstrap)
HTML reader for the `-f js` output. Point them at a generated `dipdoc.json` and
open the page: a module sidebar on the left, and per module the classes,
functions, params/returns, and — when generated with `--test` — every `$assert`
rendered green (✓) or red (✗) with its error, so the docs and the proof they
still hold sit together on the page (the `@example`-style goal). Generate with:

```sh
dipdoc <root> <langs> --test -o dipdoc.json -f js   # then open template.html
```

## Limitations

- `$assert` execution loads the module source verbatim (PHP `require`s it), so
  the documented symbol must resolve at module top level. It runs against
  self-contained modules and fixtures, not code that needs a framework runtime.
  The built-in runners are simple in-language harnesses (assertion + try/catch),
  not pytest / PHPUnit / minitest — those would be a follow-up.
- Members only nest under their class when the block names the class (`@this` /
  `@group` / a `parent`); the single-line extractor doesn't track lexical scope,
  so a method written plainly inside a class body lists module-level.
- Single-line declaration extraction: the parser inspects the one line after a
  comment (or, for a Python in-body docstring, the one line before the block),
  so multi-line signatures and a declaration hidden behind a decorator line
  (Python `@decorator`, PHP attributes) are not attached. The doc block must sit
  directly above the declaration, or — for a Python docstring — directly below
  its `def` / `class` header.
- `$assert` executes only via the built-in in-language harness; there is no
  framework runner (pytest / PHPUnit / minitest / jest) yet. The harness already
  produces the pass/fail the reader needs, so a framework runner is a follow-up,
  not a blocker.
- `java` has no parser module.

## Author

Nikola Stamatovic Stamat
