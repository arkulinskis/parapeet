/* pp-card.js: Parapeet's swipe card (window.PP.Card), wrapped by client_code/Components/PhraseCard.
   One phrase at a time in one of ten moods. The card follows the finger (or mouse):
     drag sideways -> the next / previous mood of the same phrase      drag up / down -> the next / previous phrase
     tap -> flip between French and English                            keys: arrows, Space (flip), Enter (listen)
   It also draws the mood strip above the card and the mood dots below it. Python gets told about every change
   through opts.onChange({index, tone, key, id, side, reason}). JavaScript because the card has to move with the finger
   every frame, which Anvil's in-browser Python is too slow for. */
(function () {
  'use strict';
  var PP = window.PP = window.PP || {};
  var TONES = [];   // [{key, label, icon, colour, ink}] from client_code/tones.py (PP.setTones)
  PP.setTones = function (list) { TONES = (list || []).map(function (t) { return Object.assign({}, t); }); };

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function icon(name) { return window.UI && UI.icon ? UI.icon(name) : ''; }
  function norm(w) {
    return String(w).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[’]/g, "'").replace(/[^a-z0-9']/g, '');
  }
  function words(s) { return String(s || '').split(/\s+/).filter(Boolean); }
  function tidy(s) { return String(s || '').replace(/\s*\/\s*/g, ' / ').replace(/\s+/g, ' ').trim(); }

  /* The words this mood adds compared with the neutral sentence, wrapped in <mark>. A completely different
     sentence (most words new) is left plain: there's nothing useful to compare then. */
  PP.diffHtml = function (text, base) {
    text = tidy(text);
    if (!base || text === tidy(base)) return esc(text);
    var seen = {};
    words(base).forEach(function (w) { var n = norm(w); if (n) seen[n] = 1; });
    var ws = words(text), fresh = 0;
    var parts = ws.map(function (w) { var n = norm(w), isNew = !!n && !seen[n]; if (isNew) fresh++; return { w: w, n: isNew }; });
    if (!ws.length || fresh / ws.length > 0.72) return esc(text);
    var out = [], run = [];
    parts.forEach(function (p) {
      if (p.n) { run.push(esc(p.w)); return; }
      if (run.length) { out.push('<mark>' + run.join(' ') + '</mark>'); run = []; }
      out.push(esc(p.w));
    });
    if (run.length) out.push('<mark>' + run.join(' ') + '</mark>');
    return out.join(' ');
  };

  PP.register = function (fr) {
    var tu = false, vous = false;
    words(String(fr || '').toLowerCase().replace(/[’]/g, "'").replace(/[.,;:!?()"«»“”…]/g, ' ')).forEach(function (w) {
      if (w === 'vous' || w === 'votre' || w === 'vos') vous = true;
      else if (['tu', 'te', 'toi', 'ton', 'ta', 'tes'].indexOf(w) >= 0 || w.indexOf("t'") === 0) tu = true;
    });
    return vous && !tu ? 'vous' : tu && !vous ? 'tu' : tu && vous ? 'mixed' : '';
  };
  var REG = { vous: 'vous · formal', tu: 'tu · familiar', mixed: 'tu + vous', '': '' };

  function reduced() { return !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches); }
  function typing(el) { return el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable); }
  function modalOpen() { return !!document.querySelector('.modal.in, .anvil-modal.in, .modal[style*="display: block"], .anvil-modal-dialog'); }

  function Card(root, opts) {
    this.root = root; this.opts = opts || {};
    this.cards = []; this.i = 0; this.t = 0; this.side = 'fr'; this.front = 'fr'; this.busy = false;
    this.root.innerHTML =
      '<div class="pc">' +
        '<div class="pc-strip" role="tablist" aria-label="Moods"></div>' +
        '<div class="pc-stage">' +
          '<div class="pc-hint" aria-hidden="true"></div>' +
          '<div class="pc-under" aria-hidden="true"></div><div class="pc-under two" aria-hidden="true"></div>' +
          '<div class="pc-card" tabindex="0" role="button" aria-roledescription="phrase card">' +
            '<div class="pc-inner"><div class="pc-face pc-front"></div><div class="pc-face pc-back"></div></div>' +
          '</div>' +
        '</div>' +
        '<div class="pc-dots" aria-label="Moods"></div>' +
      '</div>';
    this.el = {
      strip: root.querySelector('.pc-strip'), stage: root.querySelector('.pc-stage'), card: root.querySelector('.pc-card'),
      inner: root.querySelector('.pc-inner'), front: root.querySelector('.pc-front'), back: root.querySelector('.pc-back'),
      dots: root.querySelector('.pc-dots'), hint: root.querySelector('.pc-hint')
    };
    this._buildStrip();
    this._bind();
  }

  Card.prototype._buildStrip = function () {
    var self = this;
    this.el.strip.innerHTML = TONES.map(function (t, n) {
      return '<button type="button" class="pc-chip" role="tab" data-t="' + n + '" style="--tone:' + t.colour + ';--tone-ink:' + t.ink + '">' +
        icon(t.icon) + '<span>' + esc(t.label) + '</span></button>';
    }).join('');
    this.el.dots.innerHTML = TONES.map(function (t, n) {
      return '<button type="button" class="pc-dot" data-t="' + n + '" style="--tone:' + t.colour + '" aria-label="' + esc(t.label) + '"></button>';
    }).join('');
    [this.el.strip, this.el.dots].forEach(function (box) {
      box.addEventListener('click', function (e) {
        var b = e.target.closest('[data-t]');
        if (!b || self.busy) return;
        var n = +b.getAttribute('data-t');
        if (n !== self.t) self.go(self.i, n, n > self.t ? 'left' : 'right', 'chip');
      });
    });
  };

  Card.prototype.load = function (cards, index, tone, front) {
    this.cards = cards || [];
    this.front = front === 'en' ? 'en' : 'fr';
    this.i = Math.max(0, Math.min(index || 0, this.cards.length - 1));
    this.t = Math.max(0, Math.min(tone || 0, TONES.length - 1));
    this.side = this.front;
    this._render();
    this._changed('load');
  };

  Card.prototype.state = function () {
    var c = this.cards[this.i] || {}, t = TONES[this.t] || {};
    return { index: this.i, tone: this.t, key: t.key, id: c.id, side: this.side, count: this.cards.length };
  };

  Card.prototype._changed = function (reason) {
    var st = this.state(); st.reason = reason;
    if (this.opts.onChange) { try { this.opts.onChange(st); } catch (e) { console.error(e); } }
  };

  Card.prototype._face = function (lang) {
    var c = this.cards[this.i], t = TONES[this.t];
    if (!c || !t) return '<div class="pc-empty">No phrases here yet.</div>';
    var text = (c[lang] || {})[t.key] || '';
    var base = this.t > 0 ? (c[lang] || {})[TONES[0].key] : '';
    var reg = lang === 'fr' ? REG[PP.register(text)] : '';
    var who = t.label === 'Neutral' ? 'Neutral' : t.label;
    return '<div class="pc-head"><span class="pc-mood">' + icon(t.icon) + '<span>' + esc(who) + '</span></span>' +
      (reg ? '<span class="pc-reg">' + esc(reg) + '</span>' : '') +
      '<span class="pc-lang">' + (lang === 'fr' ? 'FR' : 'EN') + '</span></div>' +
      '<div class="pc-text" lang="' + lang + '"><span class="pc-words">' + (this.opts.diff === false ? esc(tidy(text)) : PP.diffHtml(text, base)) + '</span></div>' +
      '<div class="pc-foot">' + (lang === 'fr' ? 'Tap to see the English' : 'Tap for the French') + '</div>';
  };

  Card.prototype._render = function () {
    var t = TONES[this.t] || { colour: '#3f9a3a', ink: '#fff' };
    var other = this.front === 'fr' ? 'en' : 'fr';
    this.el.front.innerHTML = this._face(this.front);
    this.el.back.innerHTML = this._face(other);
    this.el.inner.classList.toggle('flipped', this.side !== this.front);
    this.root.style.setProperty('--tone', t.colour);
    this.root.style.setProperty('--tone-ink', t.ink);
    var c = this.cards[this.i];
    this.el.card.setAttribute('aria-label', (c ? (c[this.side] || {})[t.key] || '' : '') + '. ' + (t.label || '') + '. Tap to flip.');
    var self = this;
    Array.prototype.forEach.call(this.el.strip.children, function (b, n) {
      b.classList.toggle('on', n === self.t); b.setAttribute('aria-selected', n === self.t ? 'true' : 'false');
    });
    Array.prototype.forEach.call(this.el.dots.children, function (b, n) { b.classList.toggle('on', n === self.t); });
    var on = this.el.strip.children[this.t];
    if (on && on.scrollIntoView && this.el.strip.scrollWidth > this.el.strip.clientWidth) {
      var box = this.el.strip, left = on.offsetLeft - (box.clientWidth - on.offsetWidth) / 2;
      try { box.scrollTo({ left: left, behavior: reduced() ? 'auto' : 'smooth' }); } catch (e) { box.scrollLeft = left; }
    }
    this.root.classList.toggle('pc-has-prev', this.i > 0);
  };

  /* Move to phrase i, mood t. dir = which way the old card leaves: left, right, up, down (or none). */
  Card.prototype.go = function (i, t, dir, reason) {
    if (!this.cards.length) return;
    var n = this.cards.length;
    i = ((i % n) + n) % n; t = ((t % TONES.length) + TONES.length) % TONES.length;
    var self = this, card = this.el.card;
    if (!dir || reduced()) {
      this.i = i; this.t = t; this.side = this.front; this._render(); this._reset(true); this._changed(reason || 'go'); return;
    }
    this.busy = true;
    var out = { left: [-1, 0], right: [1, 0], up: [0, -1], down: [0, 1] }[dir] || [0, 0];
    var w = this.el.stage.clientWidth || 400, h = this.el.stage.clientHeight || 400;
    card.style.transition = 'transform .2s ease-in, opacity .2s ease-in';
    card.style.transform = 'translate(' + (out[0] * w * 1.15) + 'px,' + (out[1] * h * 0.9) + 'px) rotate(' + (out[0] * 14) + 'deg)';
    card.style.opacity = '0';
    setTimeout(function () {
      self.i = i; self.t = t; self.side = self.front; self._render();
      card.style.transition = 'none';
      card.style.transform = 'translate(' + (-out[0] * w * 0.6) + 'px,' + (-out[1] * h * 0.5) + 'px) scale(.92)';
      card.style.opacity = '0';
      void card.offsetWidth;
      card.style.transition = 'transform .26s cubic-bezier(.2,.9,.25,1.15), opacity .2s ease-out';
      card.style.transform = ''; card.style.opacity = '';
      setTimeout(function () { self.busy = false; card.style.transition = ''; }, 270);
      self._changed(reason || 'go');
    }, 200);
    if (navigator.vibrate && this.opts.haptics !== false) { try { navigator.vibrate(8); } catch (e) {} }
  };

  Card.prototype.nextTone = function () { this.go(this.i, this.t + 1, 'left', 'tone'); };
  Card.prototype.prevTone = function () { this.go(this.i, this.t - 1, 'right', 'tone'); };
  Card.prototype.nextPhrase = function () { this.go(this.i + 1, this.opts.keepTone ? this.t : 0, 'up', 'phrase'); };
  Card.prototype.prevPhrase = function () { this.go(this.i - 1, this.opts.keepTone ? this.t : 0, 'down', 'phrase'); };
  Card.prototype.flip = function () {
    this.side = this.side === 'fr' ? 'en' : 'fr';
    this.el.inner.classList.toggle('flipped', this.side !== this.front);
    this._changed('flip');
  };
  Card.prototype.setFront = function (lang) { this.front = lang === 'en' ? 'en' : 'fr'; this.side = this.front; this._render(); this._changed('front'); };
  Card.prototype.setDiff = function (on) { this.opts.diff = !!on; this._render(); };
  Card.prototype.flash = function (kind) {
    var c = this.el.card; c.classList.remove('pc-flash-good', 'pc-flash-bad'); void c.offsetWidth;
    c.classList.add(kind === 'bad' ? 'pc-flash-bad' : 'pc-flash-good');
  };
  Card.prototype.mark = function (cls, on) { this.el.card.classList.toggle(cls, !!on); };

  Card.prototype._reset = function (instant) {
    var c = this.el.card;
    c.style.transition = instant ? 'none' : 'transform .28s cubic-bezier(.2,.9,.25,1.2)';
    c.style.transform = ''; c.style.opacity = '';
    this.el.hint.className = 'pc-hint'; this.el.hint.style.opacity = '0';
  };

  Card.prototype._bind = function () {
    var self = this, card = this.el.card, drag = null;
    function hint(dx, dy, axis) {
      var h = self.el.hint, txt = '', cls = '';
      if (axis === 'x') {
        var t = TONES[((self.t + (dx < 0 ? 1 : -1)) % TONES.length + TONES.length) % TONES.length];
        txt = dx < 0 ? t.label + ' ›' : '‹ ' + t.label; cls = dx < 0 ? 'right' : 'left';
        h.style.setProperty('--hint', t.colour);
      } else if (axis === 'y') {
        txt = dy < 0 ? 'Next phrase' : 'Previous phrase'; cls = dy < 0 ? 'bottom' : 'top';
        h.style.setProperty('--hint', 'var(--c-brand)');
      }
      h.className = 'pc-hint ' + cls; h.textContent = txt;
      h.style.opacity = String(Math.min(1, Math.abs(axis === 'x' ? dx : dy) / 70));
    }
    card.addEventListener('pointerdown', function (e) {
      if (self.busy || (e.button != null && e.button !== 0)) return;
      drag = { x: e.clientX, y: e.clientY, t: Date.now(), axis: null, dx: 0, dy: 0, id: e.pointerId };
      try { card.setPointerCapture(e.pointerId); } catch (err) {}
      card.style.transition = 'none';
    });
    card.addEventListener('pointermove', function (e) {
      if (!drag || e.pointerId !== drag.id) return;
      drag.dx = e.clientX - drag.x; drag.dy = e.clientY - drag.y;
      if (!drag.axis && Math.abs(drag.dx) + Math.abs(drag.dy) > 9) drag.axis = Math.abs(drag.dx) >= Math.abs(drag.dy) ? 'x' : 'y';
      if (!drag.axis) return;
      e.preventDefault();
      var dx = drag.axis === 'x' ? drag.dx : drag.dx * 0.15, dy = drag.axis === 'y' ? drag.dy : drag.dy * 0.15;
      if (drag.axis === 'y' && dy > 0 && self.i === 0) dy = dy * 0.35;  // nothing before the first phrase: resist
      card.style.transform = 'translate(' + dx + 'px,' + dy + 'px) rotate(' + (dx / 22) + 'deg)';
      hint(dx, dy, drag.axis);
    });
    function end(e) {
      if (!drag || (e && e.pointerId !== drag.id)) return;
      var d = drag; drag = null;
      var dt = Math.max(1, Date.now() - d.t), dist = d.axis === 'x' ? d.dx : d.dy, v = Math.abs(dist) / dt;
      var w = self.el.stage.clientWidth || 360, need = Math.min(110, w * 0.22);
      if (!d.axis) {
        self._reset(true);
        if (e && e.type === 'pointerup' && dt < 450) self.flip();
        return;
      }
      if (Math.abs(dist) > need || (v > 0.55 && Math.abs(dist) > 30)) {
        self.el.hint.style.opacity = '0';
        if (d.axis === 'x') { if (dist < 0) self.nextTone(); else self.prevTone(); }
        else if (dist < 0) self.nextPhrase();
        else if (self.i > 0) self.prevPhrase();
        else self._reset(false);
      } else {
        self._reset(false);
      }
    }
    card.addEventListener('pointerup', end);
    card.addEventListener('pointercancel', function (e) { end(e); self._reset(false); });
    card.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); if (e.key === ' ') self.flip(); else if (self.opts.onListen) self.opts.onListen(); }
    });
    this._keys = function (e) {
      if (!self.opts.keys || e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey || typing(document.activeElement) || modalOpen()) return;
      if (!self.root.isConnected) return;
      var k = e.key;
      if (k === 'ArrowRight') self.nextTone();
      else if (k === 'ArrowLeft') self.prevTone();
      else if (k === 'ArrowDown') self.nextPhrase();
      else if (k === 'ArrowUp') { if (self.i > 0) self.prevPhrase(); }
      else if (k === ' ' && !(document.activeElement && /^(BUTTON|A)$/.test(document.activeElement.tagName))) self.flip();
      else if (k === 'Enter' && self.opts.onListen && !(document.activeElement && /^(BUTTON|A)$/.test(document.activeElement.tagName))) self.opts.onListen();
      else return;
      e.preventDefault();
    };
    document.addEventListener('keydown', this._keys);
  };

  Card.prototype.destroy = function () {
    document.removeEventListener('keydown', this._keys);
    this.root.innerHTML = '';
  };

  PP.Card = Card;
  PP.card = function (root, opts) { return new Card(root, opts); };
})();
