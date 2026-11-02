/* Parapeet's main journeys, run inside the real app (Anvil App Server) by tools/ui_test.py through tools/live/drive.mjs.
   Resolves to {ok, log}. Keep log lines ASCII (the Windows console).
   Guest: landing demo card -> phrasebook (buttons, keys, a real drag, flip, got it, say it, compare moods, hands-free)
   -> the trail -> the story -> a whole lesson (one wrong answer on purpose) -> sign up (guest seeds move into the
   account) -> save a phrase -> My phrasebook + quiz -> daily goal -> profile -> dark mode -> sign out. */
(async function () {
  const log = [], t0 = Date.now();
  const say = (m) => log.push(((Date.now() - t0) / 1000).toFixed(1) + 's ' + m);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 20000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));
  const vis = (e) => !!(e && e.offsetParent);
  const txt = (e) => (e ? e.textContent.trim().replace(/\s+/g, ' ') : '');
  const byText = (sel, text) => $$(sel).filter(vis).find((e) => txt(e) === text);
  async function click(sel, text) {
    const el = await until(() => (text ? byText(sel, text) : $$(sel).find(vis)), sel + (text ? ' "' + text + '"' : ''));
    el.scrollIntoView({ block: 'center' });
    el.click();
    return el;
  }
  function type(input, value) {
    input.focus(); input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  function key(k) { document.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true })); }
  async function page(hash, ready, what) {
    if (location.hash !== hash) window.UI_READY = false;
    location.hash = hash;
    await until(() => window.UI_READY && location.hash.split('/')[0] === hash.split('/')[0] && ready(), what || hash, 30000);
    await sleep(400);
  }
  const ok = (cond, msg) => { if (!cond) throw new Error('FAILED: ' + msg); say('ok   ' + msg); };
  const mood = () => txt($$('.pc-chip.on').find(vis));
  const seeds = () => parseInt((txt($('.pp-stat-seeds')) || '0').replace(/,/g, ''), 10) || 0;
  async function drag(dx, dy) {
    const card = $$('.pc-card').find(vis);
    const r = card.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
    const ev = (type, px, py) => card.dispatchEvent(new PointerEvent(type, { clientX: px, clientY: py, pointerId: 7, bubbles: true, button: 0, isPrimary: true }));
    ev('pointerdown', x, y);
    for (let i = 1; i <= 6; i++) { ev('pointermove', x + dx * i / 6, y + dy * i / 6); await sleep(16); }
    ev('pointerup', x + dx, y + dy);
    await sleep(650);
  }
  window.PP_TEST = { silent: true };

  try {
    // ---- landing: a live card in the hero
    await page('#landing', () => $('.lp-hero .pc-card'), 'landing');
    ok($('.lp-hero a[href="#auth/signup"]'), 'landing: hero has a sign-up link');
    ok(mood() === 'Lover', 'landing: the demo card starts on the Lover mood');
    await drag(-200, 0);
    ok(mood() === 'Admiring', 'landing: dragging the card left shows the next mood (Admiring)');
    ok($$('.lp-mood').length === 10, 'landing: all ten moods explained');

    // ---- the phrasebook as a guest
    await page('#practice', () => $$('.pc-card').find(vis) && /Phrase 1 of 10/.test(document.body.textContent), 'practice');
    ok(mood() === 'Neutral', 'practice: starts on the neutral mood');
    ok(vis($('.anvil-role-moodnav')) && !vis($('.pr-dock')), 'practice (desktop): mood arrows beside the card, no phone dock');
    await click('.anvil-role-moodnav button');  // the first one = previous mood
    await sleep(600);
    ok(mood() === 'Silly', 'practice: the left arrow wraps round to Silly');
    $$('.anvil-role-moodnav button')[1].click(); await sleep(700);
    ok(mood() === 'Neutral', 'practice: the right arrow goes forward again');
    key('ArrowRight'); await sleep(700);
    ok(mood() === 'Colleague', 'practice: the right arrow key = next mood');
    ok(/practice\/1\/colleague/.test(location.hash), 'practice: the address follows the card (shareable link)');
    await drag(0, -220);
    await until(() => /Phrase 2 of 10/.test(document.body.textContent), 'swipe up = next phrase');
    ok(mood() === 'Neutral', 'practice: swiping up opens the next phrase on its neutral mood');
    key('ArrowUp'); await sleep(700);
    ok(/Phrase 1 of 10/.test(document.body.textContent), 'practice: the up arrow key goes back a phrase');
    key(' '); await sleep(700);
    ok($$('.pc-inner.flipped').find(vis), 'practice: Space flips the card to the English');
    const card = $$('.pc-card').find(vis);
    card.dispatchEvent(new PointerEvent('pointerdown', { clientX: 300, clientY: 300, pointerId: 9, bubbles: true, button: 0 }));
    card.dispatchEvent(new PointerEvent('pointerup', { clientX: 301, clientY: 300, pointerId: 9, bubbles: true, button: 0 }));
    await sleep(700);
    ok(!$$('.pc-inner.flipped').find(vis), 'practice: a tap flips it back');
    $$('.pc-chip').find((c) => txt(c) === 'Boss').click(); await sleep(800);
    ok(mood() === 'Boss' && /Talking to your boss/.test(txt($('.pr-mood'))), 'practice: tapping a mood chip jumps there, the side panel explains it');
    ok(/vous/.test(txt($('.pr-mood'))), 'practice: the register (vous) is shown');
    const s0 = seeds();
    await click('.anvil-role-tool button', 'Got it');
    await until(() => seeds() === s0 + 1, 'Got it earns a seed');
    ok($$('.pc-card.pc-known').find(vis), 'practice: Got it marks the card (+1 seed)');
    window.PP_TEST.heard = txt($$('.pc-front .pc-text').find(vis));
    await click('.anvil-role-tool button', 'Say it');
    await until(() => seeds() === s0 + 4, 'Say it earns 3 seeds');
    ok(true, 'practice: Say it with the right words earns 3 seeds');
    window.PP_TEST.heard = 'completely different words here';
    await click('.anvil-role-tool button', 'Say it');
    await sleep(1200);
    ok(seeds() === s0 + 4, 'practice: a wrong attempt earns nothing');
    await click('.anvil-role-tool button', 'All moods');
    await until(() => $$('.cm-row').length === 10, 'compare dialog');
    ok($$('.cm-row mark').length > 0, 'compare: the words that change are highlighted');
    const lover = $$('.cm-row').find((r) => /Lover/.test(txt(r)));
    lover.querySelectorAll('.anvil-role-btn button')[1].click();
    await until(() => !$('.cm-row') && mood() === 'Lover', 'Go jumps to that mood');
    ok(true, 'compare: Go opens that mood on the card');
    await click('.anvil-role-tool button', 'Save');
    await click('.anvil-modal-content button', 'Not now');
    ok(true, 'practice: Save asks a guest to join first');
    await click('.anvil-role-tool button', 'Hands-free');
    await until(() => $('.hf'), 'hands-free options');
    await click('.anvil-modal-content button', 'Start listening');
    await until(() => vis($('.pr-hf')), 'hands-free running');
    await sleep(1500);
    await click('.pr-hf button', 'Stop');
    await until(() => !vis($('.pr-hf')), 'hands-free stopped');
    ok(true, 'practice: a hands-free lesson starts and stops');

    // ---- the trail, the story, a whole lesson
    await page('#play', () => $$('.ln').length >= 2, 'play');
    ok($$('.un').length === 3, 'play: three units on the trail');
    ok($$('.ln.locked').length >= 1 && /Join free/.test(txt($('.ln.locked'))), 'play: member-only lessons are locked for guests');
    ok($('.ln.current'), 'play: the current lesson is highlighted');
    $('.ln.current .ln-btn').click();
    const name = await until(() => $$('.st input').find(vis), 'the story asks a name');
    type(name, 'Alex');
    await click('.anvil-modal-content button', 'Continue the story');
    await until(() => /Alex/.test(txt($('.st'))), 'the story uses the name');
    ok(true, 'story: told with the player name');
    await click('.anvil-modal-content button', 'Get my French back!');
    await until(() => location.hash.indexOf('#lesson/u1-1') === 0 && window.UI_READY && window.PP_EX, 'lesson opens', 30000);
    ok(!vis($('.ui-header')), 'lesson: full screen (no header)');
    let n = 0, wrongDone = false;
    const types = {};
    while (!vis($('.ls-end')) && n < 40) {
      n++;
      const ex = window.PP_EX;
      types[ex.type] = 1;
      say('     exercise ' + n + ': ' + ex.type + (wrongDone ? '' : ' (wrong on purpose)'));
      if (ex.type === 'say') {
        window.PP_TEST.heard = ex.answer;
        await click('.anvil-role-mic button');
        await until(() => $('.ls-foot.good') || $('.ls-foot.bad'), 'say checked');
      } else {
        if (ex.type === 'build') {
          const words = wrongDone ? ex.answer.split(' ') : ex.answer.split(' ').reverse();
          for (const w of words) {
            const tile = $$('.anvil-role-ls-bank .tl').filter((t) => vis(t) && !t.classList.contains('used')).find((t) => txt(t) === w);
            if (tile) { tile.click(); await sleep(300); }
          }
          wrongDone = true;
        } else {
          let pick = ex.options.find((o) => o.value === ex.answer);
          if (!wrongDone) { pick = ex.options.find((o) => o.value !== ex.answer); wrongDone = true; }
          const want = pick.text.trim().replace(/\s+/g, ' ');
          const btn = await until(() => $$('.ch').filter(vis).find((b) => txt(b.querySelector('.anvil-role-ch-text')) === want), 'choice ' + want);
          btn.click(); await sleep(300);
        }
        await click('.anvil-role-ls-go button', 'Check');
        try {
          await until(() => $('.ls-foot.good') || $('.ls-foot.bad'), 'answer checked', 8000);
        } catch (e) {
          const b = $$('.anvil-role-ls-go button').map((x) => txt(x) + (x.disabled ? '(off)' : '') + (vis(x) ? '' : '(hidden)')).join(',');
          throw new Error(e.message + ' | buttons ' + b + ' | picked ' + $$('.ch.picked').length + ' | answer tiles ' + $$('.anvil-role-ls-tiles:not(.anvil-role-ls-bank) .tl').length + ' | foot ' + ($('.ls-foot') || {}).className);
        }
      }
      await sleep(300);
      window.PP_EX = null;
      key('Enter');
      await until(() => vis($('.ls-end')) || window.PP_EX, 'next exercise', 30000);
      await sleep(300);
    }
    ok(vis($('.ls-end')), 'lesson: finished after ' + n + ' answers (one wrong on purpose came back): ' + Object.keys(types).sort().join(','));
    const earned = txt($('.anvil-role-ls-stat-num'));
    ok(/^\+\d+$/.test(earned) && parseInt(earned.slice(1), 10) > 10, 'lesson: ' + earned + ' seeds on the end screen');
    ok(/First flight/.test(txt($('.ls-end'))), 'lesson: the First flight badge');
    ok(vis($('.ls-guest')), 'lesson: guests are told their seeds live in this browser');
    await click('.ls-end .anvil-role-btn button', 'Continue');
    await until(() => location.hash === '#play' && window.UI_READY && $('.ln.done'), 'back on the trail');
    ok(/Bonjour, Alex/.test(document.body.textContent), 'play: greets the player by name');
    const guestSeeds = seeds();
    ok(guestSeeds > 15, 'play: the guest has ' + guestSeeds + ' seeds');

    // ---- sign up: the guest progress joins the account
    await page('#auth/signup', () => $$('.au-card input').length >= 3, 'sign-up');
    const inputs = $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]').filter(vis);
    type(inputs[0], 'Flow Tester'); type(inputs[1], 'flow' + Date.now() + '@example.com'); type(inputs[2], 'Hb-' + Math.random().toString(36).slice(2) + '-Kq7');
    const tick = $('.au-card input[type=checkbox]');
    if (tick && !tick.checked) tick.click();
    await click('.anvil-role-btn-block button', 'Create account');
    await until(() => location.hash === '#play' && window.UI_READY && $('.anvil-role-avatar button'), 'signed in on the trail', 40000);
    await until(() => seeds() >= guestSeeds, 'seeds carried over', 15000);
    ok(true, 'sign-up: lands on the trail with the guest seeds (' + seeds() + ')');
    ok(!$$('.ln.locked').some((l) => /Join free/.test(txt(l))), 'play: an account unlocks the member lessons');
    ok($$('.ln.done').length >= 1, 'play: the lesson played as a guest is still done');

    // ---- members: save a phrase, the phrasebook, the quiz
    await page('#practice/5/client', () => $$('.pc-card').find(vis) && mood() === 'Client', 'practice deep link');
    ok(/Phrase 2 of 11/.test(document.body.textContent), 'practice: a link opens that phrase and mood (11 phrases for members)');
    await click('.anvil-role-tool button', 'Save');
    await until(() => $$('.note-edit textarea').length === 2, 'save dialog');
    ok(/vos questions/.test($$('.note-edit textarea')[0].value), 'save: the French is filled in');
    await click('.note-edit .anvil-role-btn-primary button');
    await until(() => !$('.note-edit'), 'saved');
    await page('#saved', () => $$('.sv-row').length >= 1, 'saved');
    ok(/vos questions/.test(txt($('.sv-row'))), 'my phrasebook: the saved phrase is listed');
    await click('.anvil-role-btn button', 'Quiz me');
    const q = await until(() => $$('.sv-quiz input').find(vis), 'quiz');
    type(q, 'Je suis la pour repondre a toutes vos questions');
    await click('.sv-quiz button', 'Check');
    await until(() => /Très bien/.test(txt($('.sv-quiz'))), 'quiz: right answer');
    ok(true, 'my phrasebook: the quiz accepts the right French (accents optional)');

    // ---- progress: change the daily goal
    await page('#progress', () => $$('.mb').length === 10, 'progress');
    ok($$('.bd.earned').length >= 1, 'progress: earned badges in colour');
    await click('.pg-goals button', 'Serious · 40');
    await until(() => /\/40/.test(txt($('.pg-goal .anvil-role-ring-text'))), 'goal 40');
    ok(true, 'progress: the daily goal changes to 40');

    // ---- profile, theme, sign out
    await page('#profile', () => $('.pf-grid'), 'profile');
    type($('.pf-grid input'), 'Flow Tester Two');
    await click('.pf-grid .anvil-role-btn-primary button', 'Save');
    await until(() => /Flow Tester Two/.test(txt($('.pf-head'))), 'name saved');
    ok(vis($('.pf-danger')), 'profile: name saved; account deletion is offered');
    await click('.anvil-role-avatar button');
    await click('.ui-menu .ui-seg button', 'Dark');
    ok(document.documentElement.classList.contains('ui-dark'), 'menu: Dark switches the theme');
    await click('.ui-menu .ui-seg button', 'Auto');
    await click('.ui-menu button', 'Sign out');
    await until(() => location.hash === '#landing' && window.UI_READY && $('.ui-header .ui-btn.primary'), 'signed out');
    ok(true, 'sign out: back to the landing page');

    say('PASSED');
    return { ok: true, log: log };
  } catch (e) {
    say(String(e && e.message || e));
    return { ok: false, log: log };
  }
})();
