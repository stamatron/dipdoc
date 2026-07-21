// Headless smoke test for dipdoc_reader.js: a minimal DOM shim runs the reader
// against a generated `dipdoc.json` (js format) and asserts it renders the
// module, a function, the pass/fail summary, and a failing assert's error.
// Usage: node tests/reader_smoke.js <dipdoc.json>   (exit 0 = pass)
const fs = require('fs');
const path = require('path');

function Node(tag) { this.tag = tag; this.className = ''; this.children = []; this.attrs = {}; this._text = ''; }
Object.defineProperty(Node.prototype, 'textContent', {
	get() { return this._text || this.children.map(c => c.textContent).join(''); },
	set(v) { this._text = String(v); this.children = []; }
});
Object.defineProperty(Node.prototype, 'innerHTML', { get() { return ''; }, set() { this.children = []; this._text = ''; } });
Node.prototype.appendChild = function (c) { this.children.push(c); return c; };
Object.defineProperty(Node.prototype, 'href', { get() { return this.attrs.href; }, set(v) { this.attrs.href = v; } });

const app = new Node('main'), nav = new Node('nav');
global.document = {
	createElement: t => new Node(t),
	createTextNode: t => { const n = new Node('#text'); n._text = String(t); return n; },
	getElementById: id => id === 'app' ? app : nav
};
global.window = { addEventListener: () => {} };
global.location = { hash: '' };

const jsonPath = process.argv[2] || 'dipdoc.json';
const readerPath = path.join(__dirname, '..', 'dipdoc_reader.js');
eval(fs.readFileSync(jsonPath, 'utf8'));   // defines `var dipdoc`
global.dipdoc = dipdoc;
eval(fs.readFileSync(readerPath, 'utf8'));

const txt = app.textContent, navtxt = nav.textContent;
function must(c, m) { if (!c) { console.error('FAIL: ' + m); process.exit(1); } }
must(txt.includes('fixture'), 'module heading');
must(txt.includes('add'), 'function add rendered');
must(txt.includes('passed'), 'pass/fail summary');
must(txt.includes('undefined == 999'), 'failing assert error shown');
must(navtxt.includes('fixture'), 'nav lists module');
console.log('ok: reader smoke');
