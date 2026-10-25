"""HTML for the vehicle lookup page (served at /)."""

INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="theme-color" content="#e9e3d7">
<meta name="api-key" content="__API_KEY__">
<title>VTU Sync · Vehicle RC Lookup</title>
<meta name="description" content="Look up Indian vehicle RC details — owner, insurance, fitness and RTO information, live from VahanX.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%23f1ebe0'/%3E%3Crect x='9' y='20' width='46' height='24' rx='4' fill='%23fdfcf8' stroke='%23bf4a2a' stroke-width='2'/%3E%3Crect x='9' y='20' width='7' height='24' rx='2' fill='%232f5fa8'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --paper: #e9e3d7;
    --paper-deep: #ddd4c4;
    --surface: #f1ebe0;
    --surface-hi: #f8f4ec;
    --ink: #20242b;
    --ink-2: #565a61;
    --ink-3: #625f57;
    --seal: #bf4a2a;
    --seal-deep: #9c3a1f;
    --sage: #3d6f5d;
    --sage-deep: #2f5749;
    --line: rgba(32, 36, 43, .1);
    --line-strong: rgba(32, 36, 43, .17);
    --clay: 18px 18px 40px rgba(150, 135, 112, .27), -13px -13px 32px rgba(255, 255, 255, .72);
    --clay-sm: 9px 9px 20px rgba(150, 135, 112, .22), -7px -7px 17px rgba(255, 255, 255, .7);
    --clay-inset: inset 4px 4px 10px rgba(150, 135, 112, .24), inset -4px -4px 10px rgba(255, 255, 255, .78);
    --clay-inset-sm: inset 2px 2px 6px rgba(150, 135, 112, .22), inset -2px -2px 6px rgba(255, 255, 255, .72);
    --radius: 26px;
    --radius-sm: 16px;
    --font-sans: "Plus Jakarta Sans", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
    --font-display: "Instrument Serif", "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
    --font-mono: "JetBrains Mono", ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
  }

  * { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; }
  body {
    margin: 0;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    color: var(--ink);
    font-family: var(--font-sans);
    background:
      radial-gradient(900px 620px at 82% -12%, rgba(191, 74, 42, .13), transparent 62%),
      radial-gradient(820px 560px at 4% 8%, rgba(61, 111, 93, .12), transparent 58%),
      radial-gradient(700px 500px at 50% 118%, rgba(191, 74, 42, .07), transparent 62%),
      linear-gradient(158deg, #f1ece2 0%, #e8e1d3 52%, #ebe4d6 100%);
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
  }
  body::before {
    content: "";
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    opacity: .42;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)' opacity='.22'/%3E%3C/svg%3E");
  }
  a { color: inherit; }
  button, input { font: inherit; }
  button { -webkit-tap-highlight-color: transparent; }
  ::selection { background: rgba(191, 74, 42, .2); }
  :focus-visible { outline: 3px solid rgba(191, 74, 42, .38); outline-offset: 3px; border-radius: 6px; }

  .topbar {
    position: relative;
    z-index: 2;
    width: min(1100px, calc(100% - 40px));
    margin: 0 auto;
    padding: 24px 0 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
  }
  .brand { display: flex; align-items: center; gap: 13px; text-decoration: none; }
  .brand-mark {
    width: 46px;
    height: 46px;
    display: grid;
    place-items: center;
    flex: none;
    border-radius: 15px;
    background: linear-gradient(145deg, var(--surface-hi), var(--paper-deep));
    box-shadow: var(--clay-inset-sm), 0 1px 0 rgba(255, 255, 255, .7);
    color: var(--seal);
    font-family: var(--font-display);
    font-size: 23px;
    line-height: 1;
    text-shadow: 0 1px 0 #fff, 0 -1px 0 rgba(120, 100, 80, .18);
  }
  .brand-copy { display: grid; gap: 3px; line-height: 1; }
  .brand-copy strong { font-size: 15px; font-weight: 700; letter-spacing: -.02em; }
  .brand-copy small {
    font-size: 9.5px;
    font-weight: 600;
    letter-spacing: .17em;
    text-transform: uppercase;
    color: var(--ink-3);
  }
  .source-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 9px 14px;
    border-radius: 999px;
    background: rgba(248, 244, 236, .66);
    box-shadow: var(--clay-sm);
    color: var(--ink-2);
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: .13em;
    text-transform: uppercase;
    text-decoration: none;
    transition: transform .2s ease, box-shadow .2s ease;
  }
  .source-badge:hover { transform: translateY(-1px); box-shadow: 12px 12px 26px rgba(150, 135, 112, .26), -8px -8px 20px rgba(255, 255, 255, .75); }
  .source-badge .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--sage);
    box-shadow: 0 0 0 4px rgba(61, 111, 93, .13);
    animation: breathe 3.2s ease-in-out infinite;
  }

  main {
    position: relative;
    z-index: 1;
    flex: 1;
    width: min(1100px, calc(100% - 40px));
    margin: 0 auto;
    padding: 48px 0 76px;
  }

  .hero { max-width: 840px; margin: 0 auto; text-align: center; }
  .eyebrow {
    margin: 0 0 22px;
    display: inline-flex;
    align-items: center;
    gap: 9px;
    padding: 8px 15px;
    border-radius: 999px;
    background: rgba(255, 255, 255, .3);
    box-shadow: var(--clay-inset-sm);
    color: var(--ink-2);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: .18em;
    text-transform: uppercase;
  }
  .eyebrow::before {
    content: "";
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: var(--seal);
    box-shadow: 0 0 0 3px rgba(191, 74, 42, .12);
  }
  h1 {
    margin: 0 0 18px;
    font-family: var(--font-display);
    font-size: clamp(2.9rem, 7.2vw, 5rem);
    font-weight: 400;
    line-height: .96;
    letter-spacing: -.022em;
  }
  h1 em {
    font-style: italic;
    color: var(--seal);
    white-space: nowrap;
  }
  .lede {
    max-width: 540px;
    margin: 0 auto;
    color: var(--ink-2);
    font-size: 15px;
    line-height: 1.72;
  }

  .search-card {
    position: relative;
    max-width: 780px;
    margin: 36px auto 0;
    padding: 20px;
    border-radius: var(--radius);
    background: linear-gradient(155deg, #f5f0e7 0%, #ede6d9 60%, #e8e0d2 100%);
    box-shadow: var(--clay);
    text-align: left;
  }
  .search-card::before {
    content: "";
    position: absolute;
    inset: 1px;
    border-radius: calc(var(--radius) - 1px);
    border: 1px solid rgba(255, 255, 255, .55);
    pointer-events: none;
  }
  .search-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 14px;
    padding: 0 3px 10px;
  }
  .search-head label {
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: .17em;
    text-transform: uppercase;
    color: var(--ink-2);
  }
  .format-hint {
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 500;
    letter-spacing: .04em;
    color: var(--ink-3);
    white-space: nowrap;
  }
  .search-row { display: flex; gap: 12px; }

  .plate-field {
    position: relative;
    flex: 1 1 auto;
    min-width: 0;
    display: flex;
    align-items: stretch;
    height: 60px;
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(118, 103, 84, .24);
    background:
      linear-gradient(180deg, #fdfcf8 0%, #f4f0e7 54%, #e8e2d4 100%);
    box-shadow:
      inset 0 1px 0 #fff,
      inset 0 -3px 5px rgba(118, 103, 84, .16),
      0 10px 22px -14px rgba(70, 60, 45, .9);
    transition: box-shadow .22s ease, transform .22s ease;
  }
  .plate-field::before,
  .plate-field::after {
    content: "";
    position: absolute;
    right: 11px;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 30%, #fff, #d3cbbc 56%, #a89d8c);
    box-shadow: inset 0 0 2px rgba(0, 0, 0, .4), 0 1px 1px rgba(255, 255, 255, .85);
    pointer-events: none;
  }
  .plate-field::before { top: 9px; }
  .plate-field::after { bottom: 9px; }
  .plate-field:focus-within {
    transform: translateY(-1px);
    box-shadow:
      inset 0 1px 0 #fff,
      inset 0 -3px 5px rgba(118, 103, 84, .16),
      0 0 0 4px rgba(191, 74, 42, .14),
      0 14px 26px -16px rgba(70, 60, 45, .95);
  }
  .plate-strip {
    flex: none;
    width: 28px;
    display: grid;
    place-items: center;
    background: linear-gradient(180deg, #3566ad, #204a86);
    color: #f4f8ff;
    font-family: var(--font-sans);
    font-size: 7px;
    font-weight: 700;
    letter-spacing: .18em;
    writing-mode: vertical-rl;
    transform: rotate(180deg);
    box-shadow: inset -1px 0 0 rgba(0, 0, 0, .28), inset 1px 0 0 rgba(255, 255, 255, .22);
  }
  .plate-field input {
    flex: 1;
    min-width: 0;
    height: 100%;
    padding: 0 32px 0 20px;
    border: 0;
    outline: 0;
    background: transparent;
    color: #232830;
    font-family: var(--font-mono);
    font-size: clamp(1.05rem, 3vw, 1.3rem);
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
  }
  .plate-field input::placeholder {
    font-family: var(--font-sans);
    font-size: 13.5px;
    font-weight: 500;
    letter-spacing: .01em;
    text-transform: none;
    color: #6f6a5f;
  }

  .search-btn {
    flex: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    height: 60px;
    padding: 0 25px;
    border: 0;
    border-radius: 14px;
    cursor: pointer;
    color: #fff8f3;
    background: linear-gradient(160deg, #c04d2d, #9c3a1f);
    font-size: 13.5px;
    font-weight: 700;
    letter-spacing: .01em;
    white-space: nowrap;
    box-shadow:
      0 16px 26px -14px rgba(160, 60, 32, .95),
      inset 0 1px 0 rgba(255, 255, 255, .34),
      inset 0 -3px 0 rgba(86, 28, 12, .3);
    transition: transform .18s ease, box-shadow .18s ease, filter .18s ease;
  }
  .search-btn:hover:not(:disabled) { transform: translateY(-1px); filter: saturate(1.06) brightness(1.02); }
  .search-btn:active:not(:disabled) {
    transform: translateY(1px);
    box-shadow: inset 0 3px 10px rgba(86, 28, 12, .45), 0 7px 16px -12px rgba(160, 60, 32, .9);
  }
  .search-btn:disabled { cursor: progress; opacity: .92; filter: saturate(.85); }
  .search-btn svg { flex: none; }
  .spinner {
    width: 15px;
    height: 15px;
    border: 2px solid rgba(255, 248, 243, .38);
    border-top-color: #fff8f3;
    border-radius: 50%;
    animation: spin .7s linear infinite;
  }

  .form-note {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 13px;
    padding: 0 3px;
    color: var(--ink-3);
    font-size: 10.5px;
    letter-spacing: .02em;
  }
  .form-note .left { display: inline-flex; align-items: center; gap: 6px; }
  .form-note svg { color: var(--sage); }
  .form-note .mono { font-family: var(--font-mono); letter-spacing: .06em; }

  .state { max-width: 1000px; margin: 32px auto 0; }
  .state[aria-busy="true"] { min-height: 220px; }

  .empty {
    padding: 26px;
    border-radius: var(--radius);
    background: linear-gradient(158deg, rgba(247, 243, 235, .9), rgba(234, 227, 216, .82));
    box-shadow: var(--clay);
  }
  .empty-top {
    display: flex;
    align-items: center;
    gap: 16px;
    padding-bottom: 20px;
    border-bottom: 1px dashed var(--line-strong);
  }
  .empty-badge {
    flex: none;
    width: 48px;
    height: 48px;
    display: grid;
    place-items: center;
    border-radius: 15px;
    background: var(--surface);
    box-shadow: var(--clay-inset-sm), 0 1px 0 rgba(255, 255, 255, .7);
    color: var(--seal);
  }
  .empty-top h2 {
    margin: 0 0 5px;
    font-family: var(--font-display);
    font-size: 27px;
    font-weight: 400;
    line-height: 1.05;
    letter-spacing: -.01em;
  }
  .empty-top p { margin: 0; color: var(--ink-2); font-size: 12.5px; line-height: 1.62; }
  .empty-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-top: 20px; }
  .peek {
    padding: 16px;
    border-radius: 15px;
    background: rgba(255, 255, 255, .3);
    box-shadow: var(--clay-inset-sm);
  }
  .peek-icon {
    width: 30px;
    height: 30px;
    display: grid;
    place-items: center;
    margin-bottom: 11px;
    border-radius: 9px;
    background: var(--surface-hi);
    box-shadow: var(--clay-sm);
    color: var(--sage);
  }
  .peek h3 {
    margin: 0 0 5px;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
  }
  .peek p { margin: 0; color: var(--ink-2); font-size: 11.5px; line-height: 1.58; }

  .loading-card {
    padding: 25px;
    border-radius: var(--radius);
    background: linear-gradient(158deg, #f4efe5, #eae3d5);
    box-shadow: var(--clay);
  }
  .loading-head { display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-bottom: 24px; }
  .skeleton {
    border-radius: 8px;
    background: linear-gradient(100deg, rgba(32, 36, 43, .055) 20%, rgba(255, 255, 255, .65) 42%, rgba(32, 36, 43, .055) 64%);
    background-size: 220% 100%;
    animation: shimmer 1.4s linear infinite;
  }
  .sk-title { width: min(300px, 58%); height: 24px; margin-bottom: 10px; }
  .sk-sub { width: min(190px, 38%); height: 12px; }
  .sk-plate { width: 138px; height: 44px; border-radius: 9px; flex: none; }
  .sk-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 11px; }
  .sk-box { height: 74px; border-radius: 13px; }
  .sk-lines { display: grid; gap: 12px; margin-top: 22px; }
  .sk-line { height: 12px; }
  .sk-line:nth-child(2) { width: 88%; }
  .sk-line:nth-child(3) { width: 71%; }

  .error-card {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 22px;
    border-radius: var(--radius);
    background: linear-gradient(158deg, #f4e8e1, #ecded4);
    box-shadow: var(--clay);
    animation: rise .35s ease both;
  }
  .error-icon {
    flex: none;
    width: 44px;
    height: 44px;
    display: grid;
    place-items: center;
    border-radius: 13px;
    background: linear-gradient(150deg, #c95535, #a63c20);
    color: #fff8f3;
    box-shadow: 0 12px 22px -13px rgba(160, 60, 32, .95), inset 0 1px 0 rgba(255, 255, 255, .32);
  }
  .error-card h2 { margin: 2px 0 6px; font-size: 16px; font-weight: 700; letter-spacing: -.01em; }
  .error-card p { margin: 0; color: var(--ink-2); font-size: 13px; line-height: 1.62; }
  .retry-btn {
    margin-top: 14px;
    padding: 9px 15px;
    border: 0;
    border-radius: 10px;
    cursor: pointer;
    background: var(--surface-hi);
    box-shadow: var(--clay-sm);
    color: var(--ink);
    font-size: 12px;
    font-weight: 600;
    transition: transform .18s ease, box-shadow .18s ease;
  }
  .retry-btn:hover { transform: translateY(-1px); }
  .retry-btn:active { transform: translateY(1px); box-shadow: var(--clay-inset-sm); }

  .record {
    overflow: hidden;
    border-radius: var(--radius);
    background: linear-gradient(165deg, #f7f3ea 0%, #efe8dc 56%, #eae2d4 100%);
    box-shadow: var(--clay);
    animation: rise .45s cubic-bezier(.2, .7, .2, 1) both;
  }
  .record-head {
    position: relative;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 22px;
    padding: 26px 28px 23px;
    border-bottom: 1px solid var(--line);
    background:
      radial-gradient(520px 190px at 8% -30%, rgba(255, 255, 255, .72), transparent 72%),
      linear-gradient(180deg, rgba(255, 255, 255, .18), transparent);
  }
  .record-id { display: flex; align-items: center; gap: 17px; min-width: 0; }

  .plate {
    position: relative;
    flex: none;
    display: inline-flex;
    align-items: stretch;
    height: 50px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid rgba(118, 103, 84, .26);
    background: linear-gradient(180deg, #fdfcf8, #eee9dd);
    box-shadow:
      inset 0 1px 0 #fff,
      inset 0 -2px 4px rgba(118, 103, 84, .16),
      0 11px 20px -14px rgba(70, 60, 45, .95);
  }
  .plate::before,
  .plate::after {
    content: "";
    position: absolute;
    right: 6px;
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 30%, #fff, #d3cbbc 56%, #a89d8c);
    box-shadow: inset 0 0 2px rgba(0, 0, 0, .4);
  }
  .plate::before { top: 7px; }
  .plate::after { bottom: 7px; }
  .plate .strip { width: 10px; background: linear-gradient(180deg, #3566ad, #204a86); }
  .plate .num {
    display: grid;
    place-items: center;
    padding: 0 22px 0 14px;
    color: #232830;
    font-family: var(--font-mono);
    font-size: 17px;
    font-weight: 700;
    letter-spacing: .09em;
    text-shadow: 0 1px 0 #fff, 0 -1px 0 rgba(80, 68, 50, .2);
  }

  .record-title { min-width: 0; }
  .record-kicker {
    display: flex;
    align-items: center;
    gap: 9px;
    flex-wrap: wrap;
    margin: 0 0 6px;
    color: var(--ink-3);
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: .16em;
    text-transform: uppercase;
  }
  .source-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 8px;
    border-radius: 999px;
    background: rgba(61, 111, 93, .1);
    color: var(--sage-deep);
    font-size: 8.5px;
    letter-spacing: .1em;
  }
  .source-pill .dot { width: 5px; height: 5px; border-radius: 50%; background: var(--sage); }
  .record-title h2 {
    margin: 0 0 5px;
    font-family: var(--font-display);
    font-size: clamp(1.5rem, 3.2vw, 2.05rem);
    font-weight: 400;
    line-height: 1.03;
    letter-spacing: -.005em;
    overflow-wrap: anywhere;
  }
  .record-sub { margin: 0; color: var(--ink-2); font-size: 12px; line-height: 1.5; overflow-wrap: anywhere; }

  .record-stamp {
    flex: none;
    width: 92px;
    height: 92px;
    display: grid;
    place-items: center;
    align-content: center;
    gap: 3px;
    border-radius: 50%;
    border: 2px solid rgba(191, 74, 42, .6);
    color: rgba(191, 74, 42, .86);
    font-family: var(--font-mono);
    line-height: 1.05;
    text-align: center;
    text-transform: uppercase;
    transform: rotate(-9deg);
    box-shadow:
      inset 0 0 0 3px rgba(255, 255, 255, .42),
      inset 0 0 0 4px rgba(191, 74, 42, .35);
    animation: stampIn .5s cubic-bezier(.2, 1.35, .4, 1) .1s both;
  }
  .record-stamp span { font-size: 12px; font-weight: 700; letter-spacing: .14em; }
  .record-stamp small { font-size: 6.5px; font-weight: 500; letter-spacing: .18em; }
  .record-stamp b { font-size: 7.5px; font-weight: 700; letter-spacing: .16em; }

  .stat-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1px;
    background: var(--line);
    border-bottom: 1px solid var(--line);
  }
  .stat { min-width: 0; padding: 17px 25px; background: rgba(245, 240, 231, .72); }
  .stat span.label {
    display: block;
    margin-bottom: 6px;
    color: var(--ink-3);
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: .14em;
    text-transform: uppercase;
  }
  .stat strong {
    display: block;
    font-size: 14.5px;
    font-weight: 600;
    letter-spacing: -.01em;
    line-height: 1.4;
    overflow-wrap: anywhere;
  }
  .stat strong.lapsed { color: var(--seal-deep); }
  .stat strong.soon { color: #94621c; }

  .tag {
    display: inline-block;
    margin-left: 7px;
    padding: 2px 6px;
    border-radius: 5px;
    font-size: 8px;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    vertical-align: 2px;
  }
  .tag.lapsed { background: rgba(191, 74, 42, .13); color: var(--seal-deep); }
  .tag.soon { background: rgba(148, 98, 28, .14); color: #845514; }

  .groups { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .group { min-width: 0; padding: 22px 26px 25px; border-right: 1px solid var(--line); }
  .group:last-child { border-right: 0; }
  .group h3 {
    display: flex;
    align-items: center;
    gap: 9px;
    margin: 0 0 11px;
    color: var(--ink-2);
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: .15em;
    text-transform: uppercase;
  }
  .group h3 .ico {
    width: 25px;
    height: 25px;
    flex: none;
    display: grid;
    place-items: center;
    border-radius: 8px;
    background: var(--surface-hi);
    box-shadow: var(--clay-inset-sm);
    color: var(--seal);
  }
  .row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 14px;
    padding: 8px 0;
    border-bottom: 1px dashed rgba(32, 36, 43, .11);
  }
  .row:last-child { padding-bottom: 0; border-bottom: 0; }
  .row dt { flex: none; color: var(--ink-3); font-size: 11px; }
  .row dd {
    margin: 0;
    min-width: 0;
    text-align: right;
    font-size: 12px;
    font-weight: 600;
    line-height: 1.48;
    overflow-wrap: anywhere;
  }
  .row dd.lapsed { color: var(--seal-deep); }
  .row dd.soon { color: #845514; }

  .record-foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    padding: 13px 28px;
    border-top: 1px solid var(--line);
    background: rgba(255, 255, 255, .2);
    color: var(--ink-3);
    font-size: 10.5px;
  }
  .record-foot .mono { font-family: var(--font-mono); letter-spacing: .08em; }

  footer {
    position: relative;
    z-index: 1;
    width: min(1100px, calc(100% - 40px));
    margin: 0 auto;
    padding: 0 0 34px;
    color: var(--ink-3);
    font-size: 10.5px;
    letter-spacing: .02em;
    text-align: center;
  }
  footer strong { color: var(--ink-2); font-weight: 600; }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  @keyframes shimmer { to { background-position: -220% 0; } }
  @keyframes rise { from { opacity: 0; transform: translateY(13px); } to { opacity: 1; transform: none; } }
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes breathe { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }
  @keyframes stampIn {
    from { opacity: 0; transform: rotate(-9deg) scale(1.35); }
    to { opacity: 1; transform: rotate(-9deg) scale(1); }
  }

  @media (max-width: 880px) {
    .groups { grid-template-columns: 1fr; }
    .group { border-right: 0; border-bottom: 1px solid var(--line); }
    .group:last-child { border-bottom: 0; }
    .empty-grid { grid-template-columns: 1fr; }
  }
  @media (max-width: 640px) {
    .topbar { width: calc(100% - 32px); padding-top: 18px; }
    main { width: calc(100% - 32px); padding-top: 34px; padding-bottom: 56px; }
    .source-badge .label { display: none; }
    .search-card { padding: 16px; border-radius: 22px; }
    .search-row { flex-direction: column; }
    .search-btn { width: 100%; height: 56px; }
    .plate-field { height: 56px; }
    .format-hint { display: none; }
    .empty { padding: 20px; }
    .empty-top { align-items: flex-start; }
    .empty-top h2 { font-size: 23px; }
    .sk-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .record-head { padding: 20px 20px 18px; padding-right: 92px; }
    .record-id { flex-direction: column; align-items: flex-start; gap: 12px; }
    .record-stamp { position: absolute; top: 18px; right: 12px; width: 66px; height: 66px; gap: 1px; }
    .record-stamp span { font-size: 9px; }
    .record-stamp b { font-size: 6px; }
    .record-stamp small { font-size: 5.5px; }
    .stat { padding: 15px 18px; }
    .group { padding: 19px 20px 21px; }
    .record-foot { padding: 12px 20px; }
    footer { width: calc(100% - 32px); }
  }
  @media (max-width: 400px) {
    h1 { font-size: 2.7rem; }
    h1 em { white-space: normal; }
    .plate .num { font-size: 15px; padding: 0 18px 0 12px; }
  }
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: .001ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: .001ms !important;
    }
  }
</style>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="/">
      <span class="brand-mark">VS</span>
      <span class="brand-copy">
        <strong>VTU Sync</strong>
        <small>Vehicle registry</small>
      </span>
    </a>
    <a class="source-badge" href="https://vahanx.in" target="_blank" rel="noopener noreferrer">
      <span class="dot" aria-hidden="true"></span>
      <span class="label">Live source</span>
      <span>VahanX</span>
    </a>
  </header>

  <main>
    <section class="hero">
      <p class="eyebrow">Registration certificate intelligence</p>
      <h1>One plate.<br><em>The whole record.</em></h1>
      <p class="lede">Owner, insurance, fitness and RTO details for any Indian vehicle — pulled live from VahanX and laid out like the document it is.</p>

      <form class="search-card" id="search-form" novalidate>
        <div class="search-head">
          <label for="vehicle-input">Registration number</label>
          <span class="format-hint" id="format-hint">Format · XX00XX0000</span>
        </div>
        <div class="search-row">
          <div class="plate-field">
            <span class="plate-strip" aria-hidden="true">IND</span>
            <input id="vehicle-input" name="vehicle" type="text" inputmode="text"
                   autocomplete="off" autocapitalize="characters" spellcheck="false"
                   maxlength="16" enterkeyhint="search"
                   placeholder="Enter registration number"
                   aria-describedby="format-hint form-note">
          </div>
          <button class="search-btn" id="search-btn" type="submit">
            <span id="btn-icon" aria-hidden="true">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.2-3.2"/></svg>
            </span>
            <span id="btn-label">Look up vehicle</span>
          </button>
        </div>
        <div class="form-note" id="form-note">
          <span class="left">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>
            Key-protected API
          </span>
          <span class="mono">No sign-in · no stored searches</span>
        </div>
      </form>
    </section>

    <section class="state" id="state" aria-busy="false">
      <div class="empty" id="empty-state">
        <div class="empty-top">
          <span class="empty-badge" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3h7l4 4v14H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/><path d="M14 3v4h4"/><path d="M9 12h6"/><path d="M9 16h4"/></svg>
          </span>
          <div>
            <h2>Your first lookup starts here</h2>
            <p>Type a registration number above. The full RC record — owner, vehicle, insurance and RTO — appears here after your search.</p>
          </div>
        </div>
        <div class="empty-grid">
          <div class="peek">
            <span class="peek-icon" aria-hidden="true">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>
            </span>
            <h3>Owner &amp; vehicle</h3>
            <p>Owner, maker, model, class, fuel, chassis and engine.</p>
          </div>
          <div class="peek">
            <span class="peek-icon" aria-hidden="true">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 20 7v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7l8-4Z"/><path d="m9 12 2 2 4-4"/></svg>
            </span>
            <h3>Insurance &amp; validity</h3>
            <p>Insurer, policy, insurance, fitness and tax dates.</p>
          </div>
          <div class="peek">
            <span class="peek-icon" aria-hidden="true">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></svg>
            </span>
            <h3>Registration &amp; RTO</h3>
            <p>Registration date, RTO office, city and address.</p>
          </div>
        </div>
      </div>
    </section>
    <p class="sr-only" id="live" role="status" aria-live="polite"></p>
  </main>

  <footer>
    Built for <strong>VTU Sync</strong> · Live data from <strong>VahanX</strong> · Unofficial, for reference only
  </footer>

<script>
(() => {
  "use strict";

  const API_KEY = document.querySelector('meta[name="api-key"]').getAttribute("content") || "";
  const form = document.getElementById("search-form");
  const input = document.getElementById("vehicle-input");
  const button = document.getElementById("search-btn");
  const buttonLabel = document.getElementById("btn-label");
  const buttonIcon = document.getElementById("btn-icon");
  const state = document.getElementById("state");
  const live = document.getElementById("live");

  let activeController = null;
  let requestSeq = 0;
  let lastPlate = "";

  const ICONS = {
    user: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
    car: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 17h14l1-6-3-5H7L4 11l1 6Z"/><circle cx="7.5" cy="17.5" r="1.5"/><circle cx="16.5" cy="17.5" r="1.5"/></svg>',
    shield: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3 20 7v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7l8-4Z"/><path d="m9 12 2 2 4-4"/></svg>'
  };

  const GROUPS = [
    {
      title: "Owner & registration",
      icon: ICONS.user,
      fields: [
        ["Owner", "Owner_Name"],
        ["Ownership", "Owner_Serial_No"],
        ["Registration no.", "Registration_Number"],
        ["Registered on", "Registration_Date"],
        ["RTO", "Registered_RTO"],
        ["City", "City_Name"],
        ["Phone", "Phone"],
        ["Address", "Address"]
      ]
    },
    {
      title: "Vehicle",
      icon: ICONS.car,
      fields: [
        ["Manufacturer", "Make_Name"],
        ["Model", "Model_Name"],
        ["Class", "Vehicle_Class"],
        ["Fuel", "Fuel_Type"],
        ["Fuel norms", "Fuel_Norms"],
        ["Chassis", "Chassis_Number"],
        ["Engine", "Engine_Number"],
        ["Cubic capacity", "Cubic_Capacity"],
        ["Seating", "Seating_Capacity"]
      ]
    },
    {
      title: "Insurance & validity",
      icon: ICONS.shield,
      fields: [
        ["Insurer", "Insurance_Company"],
        ["Policy no.", "Insurance_No"],
        ["Insurance upto", "Insurance_Upto"],
        ["Fitness upto", "Fitness_Upto"],
        ["Tax upto", "Tax_Upto"]
      ]
    }
  ];

  const DATE_FIELDS = new Set(["Insurance_Upto", "Fitness_Upto", "Tax_Upto"]);
  const MONTHS = { jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5, jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11 };

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[ch]));
  }

  function normalizePlate(value) {
    return String(value || "").replace(/[\s-]+/g, "").toUpperCase();
  }

  function parseDate(value) {
    const match = /^(\d{1,2})-([A-Za-z]{3})-(\d{4})$/.exec(String(value || "").trim());
    if (!match) return null;
    const month = MONTHS[match[2].toLowerCase()];
    if (month === undefined) return null;
    return new Date(Number(match[3]), month, Number(match[1]));
  }

  function dateInfo(value, includeFuture = false) {
    const date = parseDate(value);
    if (!date) return null;
    const diff = date.getTime() - Date.now();
    if (diff < 0) return { cls: "lapsed", tag: "lapsed" };
    if (!includeFuture) return null;
    if (diff < 30 * 864e5) return { cls: "soon", tag: "due soon" };
    return null;
  }

  function announce(message) {
    live.textContent = "";
    live.textContent = message;
  }

  function revealResults() {
    if (window.innerWidth > 720) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (state.getBoundingClientRect().top > window.innerHeight - 140) {
      state.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function setLoading(loading) {
    button.disabled = loading;
    state.setAttribute("aria-busy", loading ? "true" : "false");
    buttonIcon.innerHTML = loading
      ? '<span class="spinner"></span>'
      : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.2-3.2"/></svg>';
    buttonLabel.textContent = loading ? "Reading record…" : "Look up vehicle";
  }

  function loadingMarkup(plate) {
    return `
      <div class="loading-card">
        <div class="loading-head">
          <div>
            <div class="skeleton sk-title"></div>
            <div class="skeleton sk-sub"></div>
          </div>
          <div class="skeleton sk-plate"></div>
        </div>
        <div class="sk-grid">
          <div class="skeleton sk-box"></div>
          <div class="skeleton sk-box"></div>
          <div class="skeleton sk-box"></div>
          <div class="skeleton sk-box"></div>
        </div>
        <div class="sk-lines">
          <div class="skeleton sk-line"></div>
          <div class="skeleton sk-line"></div>
          <div class="skeleton sk-line"></div>
        </div>
      </div>`;
  }

  function errorMarkup(title, message, plate) {
    return `
      <div class="error-card" role="alert">
        <div class="error-icon">
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6"/><path d="M12 17h.01"/></svg>
        </div>
        <div>
          <h2>${escapeHtml(title)}</h2>
          <p>${escapeHtml(message)}</p>
          ${plate ? '<button type="button" class="retry-btn" id="retry-btn">Try again</button>' : ""}
        </div>
      </div>`;
  }

  function row(label, key, data) {
    const value = data[key];
    if (value === undefined || value === null || value === "" || value === "NA") return "";
    const info = DATE_FIELDS.has(key) ? dateInfo(value, true) : null;
    const cls = info ? info.cls : "";
    const tag = info ? `<span class="tag ${info.cls}">${info.tag}</span>` : "";
    return `<div class="row"><dt>${escapeHtml(label)}</dt><dd class="${cls}">${escapeHtml(value)}${tag}</dd></div>`;
  }

  function showError(title, message, plate) {
    state.innerHTML = errorMarkup(title, message, plate);
    announce(title + ". " + message);
    const retry = document.getElementById("retry-btn");
    if (retry) retry.addEventListener("click", () => search(plate));
    if (plate) revealResults();
  }

  function showResult(data) {
    const stats = [
      ["Owner", data.Owner_Name, null],
      ["Registered", data.Registration_Date, null],
      ["Insurance", data.Insurance_Upto, dateInfo(data.Insurance_Upto, true)],
      ["Fitness", data.Fitness_Upto, dateInfo(data.Fitness_Upto, true)]
    ].filter(([, value]) => value);

    const statMarkup = stats.map(([label, value, info]) => {
      const cls = info ? info.cls : "";
      const tag = info ? `<span class="tag ${info.cls}">${info.tag}</span>` : "";
      return `<div class="stat"><span class="label">${escapeHtml(label)}</span><strong class="${cls}">${escapeHtml(value)}${tag}</strong></div>`;
    }).join("");

    const groupsMarkup = GROUPS.map((group) => {
      const rows = group.fields.map(([label, key]) => row(label, key, data)).join("");
      if (!rows) return "";
      return `
        <section class="group">
          <h3><span class="ico">${group.icon}</span>${escapeHtml(group.title)}</h3>
          <dl>${rows}</dl>
        </section>`;
    }).join("");

    const model = data.Model_Name || data.Make_Name || "Vehicle record";
    const subtitleParts = [data.Make_Name, data.Vehicle_Class, data.Fuel_Type].filter(Boolean);
    const fetchedAt = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const source = data.source === "vahanx" ? "Live · VahanX" : (data.source || "VahanX");
    const plate = data.Registration_Number || lastPlate || "—";

    state.innerHTML = `
      <article class="record">
        <div class="record-head">
          <div class="record-id">
            <div class="plate" aria-label="Registration number ${escapeHtml(plate)}">
              <span class="strip" aria-hidden="true"></span>
              <span class="num">${escapeHtml(plate)}</span>
            </div>
            <div class="record-title">
              <p class="record-kicker">
                Registration certificate
                <span class="source-pill"><span class="dot" aria-hidden="true"></span>${escapeHtml(source)}</span>
              </p>
              <h2>${escapeHtml(model)}</h2>
              <p class="record-sub">${escapeHtml(subtitleParts.join(" · ") || "Record retrieved from VahanX")}</p>
            </div>
          </div>
          <div class="record-stamp" aria-hidden="true">
            <span>Verified</span>
            <b>Live record</b>
            <small>VahanX</small>
          </div>
        </div>
        <div class="stat-row">${statMarkup}</div>
        <div class="groups">${groupsMarkup}</div>
        <div class="record-foot">
          <span>Fetched ${escapeHtml(fetchedAt)} · Data provided by VahanX</span>
          <span class="mono">${escapeHtml(plate)}</span>
        </div>
      </article>`;

    announce(`Record found for ${plate}. ${model}.`);
    revealResults();
  }

  function friendlyError(data, statusCode, plate) {
    if (statusCode === 404) {
      return {
        title: "Vehicle not found",
        message: `No RC record was found for ${plate}. Check the registration number and try again.`
      };
    }
    if (statusCode === 401) {
      return {
        title: "API key rejected",
        message: "This page could not authenticate with the lookup API. Check the API_KEY configuration."
      };
    }
    if (statusCode === 400) {
      return {
        title: "Invalid registration number",
        message: data.message || "Use a valid Indian registration number, for example MH12AB1234."
      };
    }
    if (statusCode === 429) {
      const code = data.error?.code;
      return {
        title: "Too many lookups",
        message: code === "RATE_LIMITED"
          ? "You are searching too fast. Wait a few seconds and try again."
          : "VahanX is limiting lookups from this server. Wait a minute or two and try again."
      };
    }
    if (statusCode === 502) {
      return {
        title: "VahanX is unavailable",
        message: "The live service did not respond. Please wait a moment and try again."
      };
    }
    return {
      title: "Lookup failed",
      message: data.message || data.error || "Something went wrong while fetching this vehicle."
    };
  }

  async function search(plate) {
    const number = normalizePlate(plate || input.value);
    if (!number) {
      showError("Enter a registration number", "Type a plate such as MH12AB1234 to search.", "");
      input.focus();
      return;
    }

    const seq = ++requestSeq;
    lastPlate = number;
    input.value = number;
    history.replaceState(null, "", `?plate=${encodeURIComponent(number)}`);

    if (activeController) activeController.abort();
    activeController = new AbortController();

    setLoading(true);
    state.innerHTML = loadingMarkup(number);
    announce(`Reading RC record for ${number}.`);

    try {
      const keyParam = API_KEY ? `&key=${encodeURIComponent(API_KEY)}` : "";
      const url = `/vehicle?query=${encodeURIComponent(number)}${keyParam}`;
      const response = await fetch(url, {
        headers: { Accept: "application/json" },
        signal: activeController.signal
      });
      const data = await response.json().catch(() => ({}));
      if (seq !== requestSeq) return;

      if (!response.ok || data.status === "error" || !data.found) {
        const copy = friendlyError(data, response.status, number);
        showError(copy.title, copy.message, number);
        return;
      }
      showResult(data);
    } catch (error) {
      if (error.name === "AbortError" || seq !== requestSeq) return;
      showError(
        "Could not reach the API",
        "Check that the lookup service is running, then try again.",
        number
      );
    } finally {
      if (seq === requestSeq) setLoading(false);
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    search(input.value);
  });

  input.addEventListener("input", () => {
    const start = input.selectionStart;
    input.value = input.value.toUpperCase();
    if (start !== null) input.setSelectionRange(start, start);
  });

  // Only search automatically when a plate is explicitly present in the URL.
  // The bare page stays empty — no defaults, no hidden lookup on load.
  const initial = normalizePlate(new URLSearchParams(window.location.search).get("plate") || "");
  if (initial) {
    input.value = initial;
    search(initial);
  }
})();
</script>
</body>
</html>
"""
