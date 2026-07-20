![DipDoc - Ultimate Source code documentation and unit testing](logo.png)
======

**DipDoc** reads structured comments out of your source and, in a single pass,
extracts both **documentation** (JSDoc-style `@` tags) and **inline unit tests**
(`$` tags) — the idea being that the docs and the tests that prove them live in
the same comment block.

> Status: early / work in progress. The JavaScript parser and the JSON
> extractor work; the HTML reader and the non-JS language modules are unfinished
> (see [Limitations](#limitations)).

## Usage

```sh
python3 dipdoc.py <root-dir> [languages] [skip]
```

- `<root-dir>` — directory to scan recursively.
- `languages` — comma-separated list, defaults to `js`. A language `X` requires a
  parser module at `lang/X.py`.
- `skip` — comma-separated paths (relative to `<root-dir>`) to exclude.

Example — scan the bundled library for JavaScript docs:

```sh
python3 dipdoc.py ivartech js
```

Output is written to `<root-dir>/dipdoc.json`. Despite the name it is a small
JavaScript file (`var dipdoc = { ... }`) so the browser reader can load it with
a plain `<script>` tag.

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

## Limitations

- Only `lang/js.py` exists; `java` / `php` / `py` modules are not implemented.
- The browser reader (`dipdoc_reader.js`, `template/`) is incomplete — the
  `template/js/*.js` files are empty.
- `$assert` / `$prepare` blocks are captured verbatim but not yet executed as
  tests.
- Output path and the `var dipdoc =` wrapper are hard-coded (marked `XXX` in the
  source).

## Author

Nikola Stamatovic Stamat
