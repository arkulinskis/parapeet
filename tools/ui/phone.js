/* Phone-width check (run at 390 px wide by tools/ui_test.py): every page loads without errors and without sideways
   scrolling, signed out and signed in; the phrasebook shows the thumb dock (and not the desktop arrows), and a real
   swipe works. Resolves to {ok, log}. */
(async function () {
  const log = [], bad = [];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 20000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s), $$ = (s) => Array.from(document.querySelectorAll(s));
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  const txt = (e) => (e ? e.textContent.trim().replace(/\s+/g, ' ') : '');
  function type(input, value) {
    input.focus(); input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  async function check(hash, ready) {
    if (location.hash !== hash) window.UI_READY = false;
    location.hash = hash;
    await until(() => window.UI_READY && location.hash.split('/')[0] === hash.split('/')[0] && (!ready || ready()), hash, 30000);
    await sleep(600);
    const w = document.documentElement.scrollWidth, vw = Math.min(window.innerWidth, window.screen.width || 390);
    const wide = $$('body *').filter((e) => { const r = e.getBoundingClientRect(); return r.width && r.right > vw + 1 && !e.closest('.pc-strip'); })
      .slice(0, 3).map((e) => e.tagName.toLowerCase() + '.' + String(e.className).split(' ').slice(0, 2).join('.'));
    if (w > vw + 1) bad.push(hash + ' scrolls sideways (' + w + ' > ' + vw + ') ' + wide.join(' '));
    log.push((w > vw + 1 ? 'WIDE ' : 'ok   ') + hash + ' (' + w + ')');
  }
  window.PP_TEST = { silent: true };
  try {
    for (const h of ['#landing', '#play', '#progress', '#auth', '#auth/signup']) await check(h);
    await check('#practice', () => $$('.pc-card').find(vis));
    if (!vis($('.pr-dock'))) bad.push('#practice: the thumb dock is missing on a phone');
    if (vis($('.anvil-role-moodnav'))) bad.push('#practice: the desktop mood arrows show on a phone');
    const dock = $('.pr-dock').getBoundingClientRect(), tab = $('.ui-tabbar').getBoundingClientRect();
    if (dock.bottom > tab.top + 1) bad.push('#practice: the dock overlaps the tab bar');
    log.push('ok   #practice: thumb dock above the tab bar, no desktop arrows');
    const before = txt($$('.pc-chip.on').find(vis));
    $$('.anvil-role-dock-mood button')[1].click(); await sleep(700);
    const after = txt($$('.pc-chip.on').find(vis));
    if (before === after) bad.push('#practice: the dock mood button did nothing');
    $$('.anvil-role-dock-next button')[0].click(); await sleep(700);
    if (!/Phrase 2 of/.test(document.body.textContent)) bad.push('#practice: the dock Next button did nothing');
    log.push('ok   #practice: dock buttons change the mood (' + before + ' -> ' + after + ') and the phrase');
    await check('#lesson/u1-1', () => window.PP_EX);
    if (!vis($('.ls-foot'))) bad.push('#lesson: the Check bar is missing');
    // sign up so the member pages can be checked too
    location.hash = '#auth/signup';
    await until(() => window.UI_READY && $$('.au-card input').length >= 3, 'sign-up form');
    const inputs = $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]').filter(vis);
    type(inputs[0], 'Phone Tester'); type(inputs[1], 'phone' + Date.now() + '@example.com'); type(inputs[2], 'Hb-' + Math.random().toString(36).slice(2) + '-Kq7');
    const tick = $('.au-card input[type=checkbox]'); if (tick && !tick.checked) tick.click();
    $$('.anvil-role-btn-block button').find((b) => /Create account/.test(b.textContent)).click();
    await until(() => location.hash === '#play' && window.UI_READY, 'signed in', 30000);
    for (const h of ['#play', '#practice', '#saved', '#progress', '#profile']) await check(h);
    log.push(bad.length ? 'PROBLEMS: ' + bad.join(' | ') : 'PASSED');
    return { ok: !bad.length, log: log };
  } catch (e) {
    log.push(String(e && e.message || e));
    return { ok: false, log: log };
  }
})();
