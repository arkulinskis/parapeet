/* Admin pages (local App Server only: signs up the ADMIN_EMAILS address, which becomes admin there).
   Visits every tab, flips a user's Active switch twice, checks the phrase library numbers. Resolves to {ok, log}. */
(async function () {
  const log = [];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 30000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s), $$ = (s) => Array.from(document.querySelectorAll(s));
  const ok = (c, m) => { if (!c) throw new Error('FAILED: ' + m); log.push('ok   ' + m); };
  function type(input, value) {
    input.focus(); input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  async function page(hash, ready) {
    if (location.hash !== hash) window.UI_READY = false;
    location.hash = hash;
    await until(() => window.UI_READY && location.hash === hash && ready(), hash);
    await sleep(300);
  }
  try {
    await page('#auth', () => $$('.au-card input').length >= 2);
    const inputs = () => $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]').filter((i) => i.offsetParent);
    const pw = 'Hb-local-admin-Kq7-2026';
    type(inputs()[0], 'arkulinskis@gmail.com'); type(inputs()[1], pw);
    $$('.anvil-role-btn-block button').find((b) => /Sign in/.test(b.textContent)).click();
    await sleep(3500);
    if (location.hash !== '#play') {  // no account yet in this local database: create it
      $$('.ui-seg button').find((b) => /Create account/.test(b.textContent)).click();
      await sleep(500);
      const i = inputs(); type(i[0], 'Local Admin'); type(i[1], 'arkulinskis@gmail.com'); type(i[2], pw);
      const tick = $('.au-card input[type=checkbox]'); if (tick && !tick.checked) tick.click();
      $$('.anvil-role-btn-block button').find((b) => /Create account/.test(b.textContent)).click();
    }
    await until(() => location.hash === '#play' && window.UI_READY, 'signed in as admin', 40000);
    await page('#admin/overview', () => $$('.ad-stat').length >= 6);
    ok(/\d/.test($('.ad-stat').textContent), 'overview: the numbers');
    ok(/phrases in the library/.test(document.body.textContent), 'overview: phrase and learner numbers');
    await page('#admin/feedback', () => $('.ad-filter'));
    ok(/New \(\d+\)/.test($('.ad-filter').textContent), 'feedback: filter counts');
    await page('#admin/users', () => $$('.ad-user-row').length >= 1);
    const row = $$('.ad-user-row').find((r) => !/arkulinskis@gmail.com/.test(r.textContent));
    const box = row.querySelectorAll('input[type=checkbox]')[1];
    const was = box.checked;
    box.click(); await sleep(2500); box.click(); await sleep(2500);
    ok(box.checked === was, 'users: Active switch saved twice (back as it was)');
    await page('#admin/content', () => /basic/.test(document.body.textContent));
    ok(/10 basic/.test(document.body.textContent) && /Recorded voices/.test(document.body.textContent), 'phrases: library by access level, units and voices');
    log.push('PASSED');
    return { ok: true, log };
  } catch (e) {
    log.push(String(e && e.message || e));
    return { ok: false, log };
  }
})();
