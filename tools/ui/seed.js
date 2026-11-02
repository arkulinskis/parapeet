/* For screenshots of member pages: sign up a fresh account, earn a few seeds in the phrasebook and save a phrase.
   Resolves to window.SEED. */
(async function () {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 30000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s), $$ = (s) => Array.from(document.querySelectorAll(s));
  const vis = (e) => !!(e && e.offsetParent);
  const txt = (e) => (e ? e.textContent.trim().replace(/\s+/g, ' ') : '');
  function type(input, value) {
    input.focus(); input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  window.PP_TEST = { silent: true };
  try {
    if (location.hash !== '#auth/signup') window.UI_READY = false;
    location.hash = '#auth/signup';
    await until(() => window.UI_READY && $$('.au-card input').length >= 3, 'sign-up');
    const inputs = $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]').filter(vis);
    type(inputs[0], 'Sam Rivera'); type(inputs[1], 'shots' + Date.now() + '@example.com'); type(inputs[2], 'Hb-' + Math.random().toString(36).slice(2) + '-Kq7');
    const tick = $('.au-card input[type=checkbox]'); if (tick && !tick.checked) tick.click();
    $$('.anvil-role-btn-block button').find((b) => /Create account/.test(b.textContent)).click();
    await until(() => location.hash === '#play' && window.UI_READY, 'play', 60000);
    window.UI_READY = false; location.hash = '#practice/1/boss';
    await until(() => window.UI_READY && $$('.pc-card').find(vis), 'practice', 30000);
    await sleep(800);
    for (const label of ['Got it']) { $$('.anvil-role-tool button').find((b) => txt(b) === label).click(); await sleep(1500); }
    window.PP_TEST.heard = txt($$('.pc-front .pc-text').find(vis));
    $$('.anvil-role-tool button').find((b) => txt(b) === 'Say it').click(); await sleep(2500);
    $$('.anvil-role-tool button').find((b) => txt(b) === 'Save').click();
    await until(() => $('.note-edit'), 'save dialog');
    $('.note-edit .anvil-role-btn-primary button').click();
    await until(() => !$('.note-edit'), 'saved');
    window.SEED = { home: '#play' };
    return window.SEED;
  } catch (e) {
    return { error: String(e && e.message || e) };
  }
})();
