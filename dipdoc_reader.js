// DipDoc browser reader — vanilla JS, no dependencies.
// Renders the `var dipdoc = {...}` produced by `dipdoc ... -o dipdoc.json -f js`.
// With `--test`, each $assert carries a baked `ok`/`error`, shown pass/fail
// (the point: docs and their proof live in one place, like an @example).
(function () {
	'use strict';
	var appEl = document.getElementById('app');
	var navEl = document.getElementById('nav');

	if (typeof dipdoc === 'undefined') {
		appEl.textContent = 'No dipdoc data. Generate with: ' +
			'dipdoc <root> <langs> --test -o dipdoc.json -f js';
		return;
	}

	function el(tag, cls, text) {
		var n = document.createElement(tag);
		if (cls) n.className = cls;
		if (text != null) n.textContent = text;
		return n;
	}
	function first(v) { return Array.isArray(v) ? v[0] : v; }
	function list(v) { return Array.isArray(v) ? v : (v == null ? [] : [v]); }

	// Flatten every language's modules into one ordered list.
	var modules = [];
	Object.keys(dipdoc).sort().forEach(function (lang) {
		var data = (dipdoc[lang] && dipdoc[lang].data) || {};
		Object.keys(data).sort().forEach(function (id) {
			modules.push({ lang: lang, id: id, module: data[id] });
		});
	});

	// Which class/group an entry belongs to (mirror _ownerOf in dipdoc.py).
	function ownerOf(e) {
		var doc = e.doc || {};
		var keys = ['this', 'group', 'class'];
		for (var i = 0; i < keys.length; i++) {
			var v = first(doc[keys[i]]);
			if (typeof v === 'string' && v.trim()) return v.trim();
		}
		return e.parent || null;
	}

	// Bucket content by class (mirror _groupModule in dipdoc.py).
	function groupModule(module) {
		var classes = {}, order = [];
		var top = { 'function': [], 'field': [], 'dependency': [] };
		var content = module.content || [];
		content.forEach(function (e) {
			if (e.type === 'class' && !classes[e.name]) {
				classes[e.name] = { entry: e, 'function': [], 'field': [] };
				order.push(e.name);
			}
		});
		content.forEach(function (e) {
			if (e.type === 'class') return;
			var owner = ownerOf(e);
			if ((e.type === 'function' || e.type === 'field') && owner && classes[owner]) {
				classes[owner][e.type].push(e);
			} else if (top[e.type]) {
				top[e.type].push(e);
			}
		});
		return { classes: classes, order: order, top: top };
	}

	// Count baked asserts across a module: {pass, fail, total}.
	function assertStats(module) {
		var s = { pass: 0, fail: 0, total: 0 };
		(module.content || []).forEach(function (e) {
			var as = ((e.unit || {}).assert) || [];
			as.forEach(function (a) {
				if (!a || typeof a !== 'object') return;
				s.total++;
				if ('ok' in a) { a.ok ? s.pass++ : s.fail++; }
			});
		});
		return s;
	}

	function renderAsserts(parent, entry) {
		var as = ((entry.unit || {}).assert) || [];
		if (!as.length) return;
		var box = el('div', 'asserts');
		as.forEach(function (a) {
			if (!a || typeof a !== 'object') return;
			var cls = 'assert';
			var mark = '';
			if ('ok' in a) { cls += a.ok ? ' pass' : ' fail'; mark = a.ok ? '✓' : '✗'; }
			var row = el('div', cls);
			if (mark) row.appendChild(el('span', 'mark', mark));
			row.appendChild(el('code', 'raw', a.raw || ''));
			if ('ok' in a && !a.ok && a.error) row.appendChild(el('span', 'err', a.error));
			box.appendChild(row);
		});
		parent.appendChild(box);
	}

	function renderEntry(parent, entry, headingTag) {
		var wrap = el('div', 'entry');
		var h = el(headingTag);
		h.appendChild(el('code', null, entry.name || '(anonymous)'));
		if (entry.type) h.appendChild(el('span', 'tag', entry.type));
		wrap.appendChild(h);

		var doc = entry.doc || {};
		list(doc.description).forEach(function (d) {
			if (d) wrap.appendChild(el('p', 'desc', d));
		});

		var params = list(doc.param).filter(function (p) { return p && typeof p === 'object'; });
		var returns = list(doc['return']).filter(function (r) { return r && typeof r === 'object'; });
		if (params.length || returns.length) {
			var ul = el('ul', 'params');
			params.forEach(function (p) {
				var t = (p.type || []).join('|');
				var li = el('li');
				li.appendChild(el('strong', null, 'param '));
				li.appendChild(el('code', null, p.name || ''));
				li.appendChild(document.createTextNode((t ? ' {' + t + '} ' : ' ') + (p.description || '')));
				ul.appendChild(li);
			});
			returns.forEach(function (r) {
				var t = (r.type || []).join('|');
				var li = el('li');
				li.appendChild(el('strong', null, 'returns '));
				li.appendChild(document.createTextNode((t ? '{' + t + '} ' : '') + (r.description || '')));
				ul.appendChild(li);
			});
			wrap.appendChild(ul);
		}

		list(doc.example).forEach(function (ex) {
			if (!ex) return;
			var pre = el('pre'); pre.appendChild(el('code', null, ex));
			wrap.appendChild(el('p', 'meta', 'Example'));
			wrap.appendChild(pre);
		});

		renderAsserts(wrap, entry);
		parent.appendChild(wrap);
	}

	function renderModule(entry) {
		appEl.innerHTML = '';
		var module = entry.module;
		var hdr = module.header || {};
		var grp = groupModule(module);

		appEl.appendChild(el('h1', null, entry.id));

		var stats = assertStats(module);
		if (stats.total) {
			var sum = el('p', 'summary');
			sum.appendChild(el('span', 'ok', stats.pass + ' passed'));
			sum.appendChild(document.createTextNode(', '));
			sum.appendChild(el('span', stats.fail ? 'no' : null, stats.fail + ' failed'));
			appEl.appendChild(sum);
		}

		list(hdr.description).forEach(function (d) { if (d) appEl.appendChild(el('p', 'desc', d)); });
		[['author', 'Author'], ['version', 'Version'], ['licence', 'Licence']].forEach(function (kv) {
			var vals = list(hdr[kv[0]]);
			if (vals.length) appEl.appendChild(el('p', 'meta', kv[1] + ': ' + vals.join(', ')));
		});

		grp.order.forEach(function (nm) {
			var g = grp.classes[nm];
			var parent = g.entry.parent;
			appEl.appendChild(el('h2', null, nm + (parent ? ' extends ' + parent : '')));
			list((g.entry.doc || {}).description).forEach(function (d) {
				if (d) appEl.appendChild(el('p', 'desc', d));
			});
			g['function'].concat(g.field).forEach(function (e) {
				var e2 = Object.assign({}, e, { name: nm + '.' + (e.name || '') });
				renderEntry(appEl, e2, 'h3');
			});
		});

		if (grp.top['function'].length) {
			appEl.appendChild(el('h2', null, 'Functions'));
			grp.top['function'].forEach(function (e) { renderEntry(appEl, e, 'h3'); });
		}
		if (grp.top.field.length) {
			appEl.appendChild(el('h2', null, 'Fields'));
			grp.top.field.forEach(function (e) { renderEntry(appEl, e, 'h3'); });
		}
		if (grp.top.dependency.length) {
			appEl.appendChild(el('h2', null, 'Dependencies'));
			var ul = el('ul');
			grp.top.dependency.forEach(function (e) {
				var li = el('li'); li.appendChild(el('code', null, e.name || '')); ul.appendChild(li);
			});
			appEl.appendChild(ul);
		}
	}

	function renderNav(activeId) {
		navEl.innerHTML = '';
		navEl.appendChild(el('h2', null, 'Modules'));
		modules.forEach(function (m) {
			var a = el('a', m.id === activeId ? 'active' : null, m.id);
			a.href = '#!' + m.id;
			var stats = assertStats(m.module);
			if (stats.total) {
				var badge = el('span', 'summary', '  ' +
					(stats.fail ? '✗' + stats.fail : '✓' + stats.pass));
				a.appendChild(badge);
			}
			navEl.appendChild(a);
		});
	}

	function show() {
		var id = decodeURIComponent((location.hash || '').replace(/^#!?/, ''));
		var entry = modules.filter(function (m) { return m.id === id; })[0] || modules[0];
		if (!entry) { appEl.textContent = 'No modules found.'; return; }
		renderNav(entry.id);
		renderModule(entry);
	}

	window.addEventListener('hashchange', show);
	show();
})();
