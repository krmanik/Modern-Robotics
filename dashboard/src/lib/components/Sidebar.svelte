<script>
  import { store, chapterProgress, isChapterComplete, persist, exportData, importData } from '../stores/store.svelte.js';
  let { chapters } = $props();

  let fileInput = $state(null);
  function doExport() {
    const blob = new Blob([exportData()], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `mr-dashboard-progress-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }
  function doImport(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () => {
      try { importData(String(r.result)); location.reload(); }
      catch { alert('Invalid backup file.'); }
    };
    r.readAsText(f);
  }

  let isMobile = $state(typeof matchMedia !== 'undefined' && matchMedia('(max-width: 860px)').matches);
  $effect(() => {
    if (typeof matchMedia === 'undefined') return;
    const mq = matchMedia('(max-width: 860px)');
    const h = (e) => isMobile = e.matches;
    mq.addEventListener('change', h);
    return () => mq.removeEventListener('change', h);
  });
  const collapsed = $derived(store.ui.collapsed && !isMobile);
  function select(id) { store.ui.chapter = id; store.ui.mobileNav = false; persist(); }
  function toggle() { store.ui.collapsed = !store.ui.collapsed; persist(); }
  function closeMobile() { store.ui.mobileNav = false; persist(); }
</script>

{#if store.ui.mobileNav}
  <div class="m-backdrop" onclick={closeMobile}></div>
{/if}

<aside class="sidebar" class:collapsed class:mobile-open={store.ui.mobileNav}>
  <div class="brand">
    <div class="logo">MR</div>
    {#if !collapsed}
      <div class="titles">
        <div class="t1">Modern Robotics</div>
        <div class="t2">Study Dashboard</div>
      </div>
    {/if}
    <button class="toggle" onclick={toggle} title={collapsed ? 'Expand' : 'Collapse'}>{collapsed ? '»' : '«'}</button>
  </div>

  <nav class="nav">
    {#if !collapsed}<div class="nav-label">Chapters</div>{/if}
    {#each chapters as ch}
      {@const active = store.ui.chapter === ch.id}
      {@const prog = chapterProgress(ch)}
      {@const done = isChapterComplete(ch.id)}
      <button class="chap" class:active onclick={() => select(ch.id)} title={ch.title}>
        <span class="num" class:done>{ch.id === 'capstone' ? 'C' : ch.n}</span>
        {#if !collapsed}
          <span class="name">{ch.title}</span>
          {#if done}<span class="badge done">Done</span>{:else if prog > 0}<span class="badge">{Math.round(prog * 100)}%</span>{/if}
        {/if}
        {#if prog > 0}<span class="prog" style="width:{prog * 100}%"></span>{/if}
      </button>
    {/each}
  </nav>

  {#if !collapsed}
    <div class="foot">
      <div class="backup">
        <button class="bk" onclick={doExport}>Export progress</button>
        <button class="bk" onclick={() => fileInput.click()}>Import</button>
        <input type="file" accept="application/json" bind:this={fileInput} onchange={doImport} hidden />
      </div>
      <div class="cite">Lynch &amp; Park · 2nd ed.</div>
    </div>
  {/if}
</aside>

<style>
  .sidebar { background: var(--surface); border-right: 1px solid var(--border); display: flex; flex-direction: column; height: 100%; overflow: hidden; }
  .brand { display: flex; align-items: center; gap: 11px; padding: 16px 14px; border-bottom: 1px solid var(--border); }
  .logo { width: 36px; height: 36px; flex: none; border-radius: 9px; background: var(--accent); color: #fff; display: grid; place-items: center; font-weight: 700; letter-spacing: .5px; }
  .titles { min-width: 0; }
  .titles .t1 { font-weight: 650; line-height: 1.2; white-space: nowrap; }
  .titles .t2 { font-size: 12px; color: var(--text-2); white-space: nowrap; }
  .toggle { margin-left: auto; border: 1px solid var(--border); background: var(--surface); border-radius: 7px; width: 26px; height: 26px; color: var(--text-2); flex: none; }
  .toggle:hover { background: var(--surface-2); color: var(--text); }
  .collapsed .brand { flex-direction: column; gap: 8px; padding: 14px 8px; }
  .collapsed .toggle { margin-left: 0; }

  .nav { flex: 1; overflow-y: auto; padding: 12px 10px; }
  .collapsed .nav { padding: 12px 8px; }
  .nav-label { font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: var(--text-3); padding: 4px 8px 8px; font-weight: 600; }
  .chap { position: relative; width: 100%; display: flex; align-items: center; gap: 10px; text-align: left; border: none; background: transparent; border-radius: var(--radius-sm); padding: 8px 10px; color: var(--text); overflow: hidden; margin-bottom: 1px; }
  .collapsed .chap { justify-content: center; padding: 7px 0; }
  .chap:hover { background: var(--surface-2); }
  .chap.active { background: var(--accent-soft); color: var(--accent-text); }
  .num { flex: none; width: 22px; height: 22px; display: grid; place-items: center; border-radius: 6px; background: var(--surface-2); font-size: 12px; font-weight: 600; color: var(--text-2); }
  .chap.active .num { background: var(--accent); color: #fff; }
  .num.done { background: var(--accent); color: #fff; }
  .name { flex: 1; font-size: 13.5px; line-height: 1.25; }
  .badge { font-size: 10.5px; font-weight: 600; color: var(--accent-text); background: color-mix(in srgb, var(--accent) 14%, transparent); padding: 1px 6px; border-radius: 20px; }
  .badge.done { background: var(--accent); color: #fff; }
  .prog { position: absolute; left: 0; bottom: 0; height: 2px; background: var(--accent); opacity: .55; }
  .foot { padding: 10px 12px; border-top: 1px solid var(--border); }
  .backup { display: flex; gap: 6px; margin-bottom: 8px; }
  .bk { flex: 1; border: 1px solid var(--border-strong); background: var(--surface); border-radius: 7px; padding: 6px 8px; font-size: 12px; color: var(--text-2); }
  .bk:hover { background: var(--surface-2); color: var(--text); }
  .cite { font-size: 11.5px; color: var(--text-3); padding: 0 6px; }

  .m-backdrop { display: none; }
  @media (max-width: 860px) {
    .sidebar { position: fixed; z-index: 60; width: 270px; height: 100%; transform: translateX(-100%); transition: transform .2s ease; box-shadow: none; }
    .sidebar.collapsed { width: 270px; }
    .sidebar.mobile-open { transform: none; box-shadow: 0 0 40px rgba(0,0,0,.3); }
    .sidebar .toggle { display: none; }
    .m-backdrop { display: block; position: fixed; inset: 0; background: rgba(0,0,0,.35); z-index: 55; }
  }
</style>
