![DipDoc - Ultimate Source code documentation and unit testing](logo.png)
======

**DipDoc** reads structured comments out of your source and, in a single pass,
extracts both **documentation** (JSDoc-style `@` tags) and **inline unit tests**
(`$` tags) — the idea being that the docs and the tests that prove them live in
the same comment block.

> Status: early / work in progress. The JavaScript parser, the JSON/Markdown
> extractors, and the `$assert` executor work; the browser reader and the non-JS
> language modules are unfinished (see [Limitations](#limitations)).

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
  parser module at `lang/X.py`.
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
dipdoc ivartech js                 # -> ivartech/dipdoc.json (var dipdoc = ...)
dipdoc ivartech js -f md -o docs.md
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

## Tests

```sh
python3 test_dipdoc.py
```

Framework-free smoke tests: parsing, JS extraction, `$assert` parsing/execution
(via Node, self-skipped if `node` is absent), and the Markdown emitter.

## Limitations

- Only `lang/js.py` exists; `java` / `php` / `py` modules are not implemented.
- `$assert` execution loads the module source verbatim, so the documented symbol
  must resolve at module top level. It runs against self-contained modules and
  fixtures, not code that needs a framework runtime.
- Single-line declaration extraction: the parser inspects the one line after a
  comment. It handles functions, arrow functions, classes, `const`/`let`,
  object methods, prototypes, and exports, but not multi-line signatures.
- The browser reader (`dipdoc_reader.js`, `template/`) is still incomplete; use
  `-f md` for viewable output in the meantime.

## Author

Nikola Stamatovic Stamat
