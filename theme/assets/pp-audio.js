/* pp-audio.js: Parapeet's sound and speech engine (window.PP), used through client_code/pp.py.
   - PP.play(url) / PP.say(text, lang, mood): the phrase's recorded voice file, or the browser's own voice with a
     different pace and pitch per mood. Both return a Promise that resolves when the sound has finished.
   - PP.rec: record yourself (stays in this browser) and play it back.
   - PP.listen(lang): speech recognition (Chrome, Edge, Safari), for "Say it". PP.similarity scores the attempt.
   - PP.sfx(kind), PP.confetti(), PP.wake(on) (keep the screen on during hands-free lessons).
   Test hooks: window.PP_TEST = {heard: "text"} makes PP.listen answer at once; {silent: true} skips real audio. */
(function () {
  'use strict';
  var PP = window.PP = window.PP || {};
  var current = null, lastMs = 0, store = function () { return window.UI && UI.store; };

  PP.settings = function () {
    var s = store();
    return { sfx: s ? s.get('sfx', true) : true, speed: s ? s.get('speed', 1) : 1 };
  };

  var PROSODY = {
    Basic: [1, 1], Colleague: [1.03, 1.02], Client: [0.97, 1.06], Boss: [0.94, 0.97], Agressive: [0.93, 0.93],
    Frustrated: [1.08, 0.9], Sad: [0.84, 0.86], Lover: [0.88, 1.1], Impressed: [1.06, 1.16], Stupid: [1.12, 1.28]
  };

  function test() { return window.PP_TEST || {}; }
  function voices() { try { return window.speechSynthesis ? speechSynthesis.getVoices() : []; } catch (e) { return []; } }
  if (window.speechSynthesis && speechSynthesis.addEventListener) { try { speechSynthesis.addEventListener('voiceschanged', voices); } catch (e) {} }
  function pickVoice(lang) {
    var vs = voices(), want = lang.toLowerCase(), base = want.slice(0, 2);
    var exact = vs.filter(function (v) { return (v.lang || '').toLowerCase().replace('_', '-') === want; });
    var near = vs.filter(function (v) { return (v.lang || '').toLowerCase().slice(0, 2) === base; });
    var list = exact.length ? exact : near;
    var nice = list.filter(function (v) { return /natural|neural|google|premium|enhanced|amelie|thomas|audrey|monica|paulina|jorge|alice|luca|federica/i.test(v.name); });
    return (nice[0] || list[0]) || null;
  }
  /* 'en' = English; 'fr' (the card's learning side) = the language being learned (PP.LANG, pp-card.js);
     anything else is already a full tag like 'es-ES'. */
  function ttsTag(lang) {
    if (lang === 'en') return 'en-US';
    if (!lang || lang === 'fr') return (PP.LANG && PP.LANG.tts) || 'fr-FR';
    return lang;
  }
  PP.hasVoice = function (lang) { return !!pickVoice(ttsTag(lang)); };

  PP.stop = function () {
    var was = current;
    current = null;
    try { if (was) { was.pause(); if (was._end) was._end('stopped'); } } catch (e) {}
    try { if (window.speechSynthesis) speechSynthesis.cancel(); } catch (e) {}
  };

  PP.say = function (text, lang, mood, speed) {
    return new Promise(function (resolve) {
      var t0 = Date.now();
      function fin(r) { lastMs = Date.now() - t0; resolve(r); }
      if (test().silent || !window.speechSynthesis || !text) return setTimeout(function () { fin('silent'); }, test().silent ? 30 : 0);
      PP.stop();
      var u = new SpeechSynthesisUtterance(String(text));
      u.lang = ttsTag(lang);
      var v = pickVoice(u.lang); if (v) u.voice = v;
      var p = PROSODY[mood] || [1, 1];
      u.rate = Math.max(0.5, Math.min(1.6, p[0] * (speed || PP.settings().speed || 1)));
      u.pitch = p[1];
      var done = false, guard = setTimeout(function () { end('timeout'); }, 2500 + String(text).length * 110 / u.rate);
      function end(r) { if (!done) { done = true; clearTimeout(guard); fin(r); } }
      u.onend = function () { end('ok'); };
      u.onerror = function () { end('error'); };
      try { speechSynthesis.speak(u); } catch (e) { end('error'); }
    });
  };

  PP.play = function (url, volume, speed) {
    return new Promise(function (resolve) {
      var t0 = Date.now();
      if (test().silent || !url) return setTimeout(function () { lastMs = Date.now() - t0; resolve(url ? 'silent' : 'error'); }, 30);
      PP.stop();
      var a = new Audio(url); current = a;
      a.volume = volume == null ? 1 : volume;
      a.playbackRate = speed || PP.settings().speed || 1;
      var done = false;
      function end(r) { if (!done) { done = true; lastMs = Date.now() - t0; if (current === a) current = null; resolve(r); } }
      a._end = end;
      a.onended = function () { end('ok'); };
      a.onerror = function () { end('error'); };
      var guard = setTimeout(function () { end('timeout'); }, 30000);
      a.addEventListener('ended', function () { clearTimeout(guard); });
      var pr = a.play(); if (pr && pr.catch) pr.catch(function () { end('error'); });
    });
  };
  PP.lastMs = function () { return lastMs; };
  /* Start PP[name](...args) without making Python wait (Anvil waits for a returned Promise); done(result) after. */
  PP.fire = function (name, args, done) {
    var p;
    try { p = PP[name].apply(PP, args || []); } catch (e) { if (done) done('error'); return; }
    if (p && p.then) p.then(function (r) { if (done) done(r); }, function () { if (done) done('error'); });
    else if (done) done(p);
  };
  PP.wait = function (ms) { return new Promise(function (r) { setTimeout(r, Math.max(0, ms || 0)); }); };

  /* ---- record yourself: the recording never leaves this browser */
  var R = PP.rec = { url: null, stream: null, mr: null, chunks: [], on: false };
  R.start = function () {
    if (!navigator.mediaDevices || !window.MediaRecorder) return Promise.resolve('unsupported');
    PP.stop();
    return navigator.mediaDevices.getUserMedia({ audio: true }).then(function (s) {
      R.stream = s; R.chunks = []; R.mr = new MediaRecorder(s); R.on = true;
      R.mr.ondataavailable = function (e) { if (e.data && e.data.size) R.chunks.push(e.data); };
      R.mr.start();
      return 'ok';
    }).catch(function (e) { return (e && e.name === 'NotAllowedError') ? 'denied' : 'error'; });
  };
  R.stop = function () {
    return new Promise(function (resolve) {
      if (!R.mr || R.mr.state === 'inactive') { R.on = false; return resolve(!!R.url); }
      R.mr.onstop = function () {
        var b = new Blob(R.chunks, { type: R.mr.mimeType || 'audio/webm' });
        if (R.url) URL.revokeObjectURL(R.url);
        R.url = b.size ? URL.createObjectURL(b) : null;
        try { R.stream.getTracks().forEach(function (t) { t.stop(); }); } catch (e) {}
        R.stream = null; R.on = false;
        resolve(!!R.url);
      };
      try { R.mr.stop(); } catch (e) { R.on = false; resolve(!!R.url); }
    });
  };
  R.play = function () { return R.url ? PP.play(R.url) : Promise.resolve('none'); };
  PP.playRecording = function () { return R.play(); };

  /* ---- soft background music for hands-free lessons (the app's own tracks from the Music table) */
  var bg = null;
  PP.music = function (urls) {
    PP.musicStop();
    urls = (urls || []).filter(Boolean);
    if (!urls.length || test().silent) return false;
    var n = 0;
    bg = new Audio(urls[0]); bg.volume = 0.13;
    bg.onended = function () { n = (n + 1) % urls.length; bg.src = urls[n]; bg.play().catch(function () {}); };
    bg.play().catch(function () {});
    return true;
  };
  PP.musicStop = function () { if (bg) { try { bg.pause(); } catch (e) {} bg = null; } };
  R.has = function () { return !!R.url; };
  R.clear = function () { if (R.url) URL.revokeObjectURL(R.url); R.url = null; };

  /* ---- speech recognition for "Say it" */
  PP.canListen = function () { return !!(test().heard != null || window.SpeechRecognition || window.webkitSpeechRecognition); };
  PP.listen = function (lang, ms) {
    return new Promise(function (done) {
      function resolve(v) { done({ transcript: v.transcript || '', alternatives: v.alternatives || [], error: v.error || '' }); }
      if (test().heard != null) return setTimeout(function () { resolve({ transcript: String(test().heard), alternatives: [String(test().heard)] }); }, 200);
      var C = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!C) return resolve({ error: 'unsupported' });
      PP.stop();
      var r = new C(); PP._rec = r;
      r.lang = lang && lang !== 'fr' ? lang : ((PP.LANG && PP.LANG.asr) || 'fr-CA'); r.interimResults = false; r.maxAlternatives = 5; r.continuous = false;
      var done = false, guard = setTimeout(function () { fin({ error: 'timeout' }); }, ms || 9000);
      function fin(v) { if (done) return; done = true; clearTimeout(guard); try { r.abort(); } catch (e) {} PP._rec = null; resolve(v); }
      r.onresult = function (e) {
        var alts = [], res = e.results && e.results[0];
        for (var i = 0; res && i < res.length; i++) alts.push(res[i].transcript);
        fin({ transcript: alts[0] || '', alternatives: alts });
      };
      r.onerror = function (e) { fin({ error: (e && e.error) || 'error' }); };
      r.onend = function () { setTimeout(function () { fin({ error: 'no-speech' }); }, 300); };
      try { r.start(); } catch (e) { fin({ error: 'start' }); }
    });
  };
  PP.stopListening = function () { if (PP._rec) { try { PP._rec.stop(); } catch (e) {} } };

  function plain(s) {
    return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[’']/g, ' ')
      .replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
  }
  function lev(a, b) {
    var m = a.length, n = b.length, prev = [], cur, i, j;
    for (j = 0; j <= n; j++) prev[j] = j;
    for (i = 1; i <= m; i++) {
      cur = [i];
      for (j = 1; j <= n; j++) cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      prev = cur;
    }
    return prev[n];
  }
  /* 0..1: how close two sentences are, ignoring case, accents and punctuation. */
  PP.similarity = function (a, b) {
    a = plain(a); b = plain(b);
    var L = Math.max(a.length, b.length);
    return L ? (L - lev(a, b)) / L : 1;
  };
  PP.bestSimilarity = function (target, alts) {
    var best = 0; (alts || []).forEach(function (t) { best = Math.max(best, PP.similarity(target, t)); }); return best;
  };
  PP.plain = plain;

  /* ---- little sounds (made on the fly: no files), haptics, keep the screen awake */
  var ctx = null;
  function tone(freq, start, dur, type, gain) {
    var o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type || 'sine'; o.frequency.value = freq;
    g.gain.setValueAtTime(0.0001, ctx.currentTime + start);
    g.gain.exponentialRampToValueAtTime(gain || 0.16, ctx.currentTime + start + 0.015);
    g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + start + dur);
    o.connect(g); g.connect(ctx.destination); o.start(ctx.currentTime + start); o.stop(ctx.currentTime + start + dur + 0.05);
  }
  PP.sfx = function (kind) {
    if (!PP.settings().sfx || test().silent) return;
    try {
      ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
      if (ctx.state === 'suspended') ctx.resume();
      if (kind === 'good') { tone(660, 0, 0.12, 'triangle'); tone(990, 0.09, 0.2, 'triangle'); }
      else if (kind === 'bad') { tone(220, 0, 0.18, 'sawtooth', 0.07); tone(180, 0.12, 0.22, 'sawtooth', 0.06); }
      else if (kind === 'done') { [523, 659, 784, 1046].forEach(function (f, i) { tone(f, i * 0.1, 0.25, 'triangle'); }); }
      else if (kind === 'seed') { tone(1200, 0, 0.08, 'sine', 0.1); }
      else { tone(440, 0, 0.06, 'sine', 0.08); }
    } catch (e) {}
    if (navigator.vibrate && (kind === 'good' || kind === 'bad')) { try { navigator.vibrate(kind === 'bad' ? [20, 40, 20] : 12); } catch (e) {} }
  };

  var lock = null;
  PP.wake = function (on) {
    try {
      if (on && navigator.wakeLock && !lock) navigator.wakeLock.request('screen').then(function (l) { lock = l; }).catch(function () {});
      if (!on && lock) { lock.release(); lock = null; }
    } catch (e) {}
  };

  PP.confetti = function () {
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var c = document.createElement('canvas'), d = window.devicePixelRatio || 1;
    c.className = 'pp-confetti'; c.width = innerWidth * d; c.height = innerHeight * d;
    document.body.appendChild(c);
    var g = c.getContext('2d'), cols = ['#2e9e4f', '#36bfda', '#ffc83d', '#e0559b', '#8a55d6', '#ff8a3d'], bits = [];
    for (var i = 0; i < 140; i++) {
      bits.push({ x: innerWidth / 2 + (Math.random() - 0.5) * 120, y: innerHeight * 0.38, vx: (Math.random() - 0.5) * 13,
        vy: -Math.random() * 13 - 4, r: Math.random() * 6 + 4, a: Math.random() * 6, va: (Math.random() - 0.5) * 0.4,
        c: cols[i % cols.length], leaf: i % 3 === 0 });
    }
    var t0 = performance.now();
    (function frame(now) {
      var t = now - t0;
      g.setTransform(d, 0, 0, d, 0, 0); g.clearRect(0, 0, innerWidth, innerHeight);
      bits.forEach(function (b) {
        b.vy += 0.38; b.vx *= 0.99; b.x += b.vx; b.y += b.vy; b.a += b.va;
        g.save(); g.translate(b.x, b.y); g.rotate(b.a); g.globalAlpha = Math.max(0, 1 - t / 1900); g.fillStyle = b.c;
        if (b.leaf) { g.beginPath(); g.ellipse(0, 0, b.r * 1.3, b.r * 0.55, 0, 0, Math.PI * 2); g.fill(); }
        else g.fillRect(-b.r / 2, -b.r / 3, b.r, b.r * 0.66);
        g.restore();
      });
      if (t < 1900) requestAnimationFrame(frame); else c.remove();
    })(t0);
  };
})();
