<script module>
  let probedLocal = false; // session-wide: only probe local availability once
</script>

<script>
  import { store, persist } from '../stores/store.svelte.js';

  let { chapter } = $props();
  const vids = chapter.videos;
  let idx = $state(Math.min((store.ui.video || 0), Math.max(0, vids.length - 1)));
  let videoEl = $state(null);
  let lastSave = 0;

  const current = $derived(vids[idx]);
  const anyYt = vids.some(v => v.yt);
  const ytMode = $derived(store.ui.videoSource === 'youtube');
  function setSource(s) { store.ui.videoSource = s; persist(); }

  // If local video files aren't present (e.g. fresh clone with no coursera/),
  // fall back to YouTube automatically — probed once per session.
  $effect(() => {
    if (probedLocal || ytMode || !current?.url || !anyYt) return;
    probedLocal = true;
    fetch(encodeURI(current.url), { method: 'HEAD' })
      .then(r => { if (!r.ok) setSource('youtube'); })
      .catch(() => setSource('youtube'));
  });
  const vstate = (url) => {
    if (!store.videos[url]) store.videos[url] = { time: 0, done: false };
    return store.videos[url];
  };

  // group by week for the list
  const groups = $derived.by(() => {
    const g = [];
    vids.forEach((v, i) => {
      const last = g[g.length - 1];
      if (last && last.week === v.week) last.items.push({ v, i });
      else g.push({ week: v.week, items: [{ v, i }] });
    });
    return g;
  });

  function pick(i) {
    idx = i; store.ui.video = i; persist();
  }
  function onLoaded() {
    const s = store.videos[current.url];
    if (s && s.time > 0 && s.time < (videoEl.duration - 5)) videoEl.currentTime = s.time;
  }
  function onTime() {
    const now = Date.now();
    if (now - lastSave < 4000) return;
    lastSave = now;
    vstate(current.url).time = videoEl.currentTime;
    persist();
  }
  function onEnded() {
    vstate(current.url).done = true;
    persist();
    if (idx < vids.length - 1) pick(idx + 1);
  }
  function toggleDone(url, e) {
    e.stopPropagation();
    const s = vstate(url); s.done = !s.done; persist();
  }
  const fmt = (t) => isNaN(t) ? '' : `${Math.floor(t/60)}:${String(Math.floor(t%60)).padStart(2,'0')}`;
  const doneCount = $derived(vids.filter(v => store.videos[v.url]?.done).length);
</script>

<div class="videos">
  <div class="list">
    <div class="list-head">
      <span>{vids.length} lectures</span>
      <span class="muted">{doneCount} done</span>
    </div>
    {#each groups as grp}
      <div class="week">{grp.week}</div>
      {#each grp.items as { v, i }}
        {@const s = store.videos[v.url]}
        <button class="row" class:active={i === idx} onclick={() => pick(i)}>
          <span class="check" class:on={s?.done} role="button" tabindex="-1" onclick={(e) => toggleDone(v.url, e)} title="Mark watched"></span>
          <span class="rtitle">{v.label}</span>
          {#if s && !s.done && s.time > 5}<span class="resume muted">{fmt(s.time)}</span>{/if}
        </button>
      {/each}
    {/each}
  </div>

  <div class="player">
    <div class="src-bar">
      <div class="seg">
        <button class:active={!ytMode} onclick={() => setSource('local')}>Local file</button>
        <button class:active={ytMode} onclick={() => setSource('youtube')} disabled={!current.yt && !anyYt}>YouTube</button>
      </div>
      {#if ytMode && !current.yt}<span class="srcnote muted">Not on the YouTube playlist — playing local file.</span>{/if}
    </div>

    <div class="stage">
      {#if ytMode && current.yt}
        {#key current.yt}
          <iframe
            class="ytframe"
            src={`https://www.youtube.com/embed/${current.yt}?rel=0&modestbranding=1`}
            title={current.label}
            frameborder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowfullscreen
          ></iframe>
        {/key}
      {:else}
        {#key current.url}
          <video
            bind:this={videoEl}
            src={encodeURI(current.url)}
            controls
            onloadedmetadata={onLoaded}
            ontimeupdate={onTime}
            onended={onEnded}
          >
            {#if current.vtt}
              <track kind="subtitles" src={encodeURI(current.vtt)} srclang="en" label="English" default />
            {/if}
          </video>
        {/key}
      {/if}
    </div>

    <div class="meta">
      <div class="vt">{current.label}</div>
      <div class="muted">{current.week}</div>
    </div>
  </div>
</div>

<style>
  .videos { display: grid; grid-template-columns: 320px 1fr; height: 100%; min-height: 0; }
  @media (max-width: 860px) {
    .videos { grid-template-columns: 1fr; grid-template-rows: 1fr 1fr; }
    .list { border-right: none; border-bottom: 1px solid var(--border); }
  }
  .list { border-right: 1px solid var(--border); overflow-y: auto; background: var(--surface); padding-bottom: 16px; }
  .list-head { display: flex; justify-content: space-between; padding: 12px 16px 6px; font-weight: 600; font-size: 13px; position: sticky; top: 0; background: var(--surface); }
  .week { font-size: 11px; text-transform: uppercase; letter-spacing: .05em; color: var(--text-3); padding: 12px 16px 4px; font-weight: 600; }
  .row { width: 100%; display: flex; align-items: center; gap: 9px; text-align: left; border: none; background: transparent; padding: 7px 14px; color: var(--text); }
  .row:hover { background: var(--surface-2); }
  .row.active { background: var(--accent-soft); color: var(--accent-text); }
  .check { flex: none; width: 18px; height: 18px; border-radius: 50%; border: 1.5px solid var(--border-strong); display: grid; place-items: center; font-size: 11px; color: var(--accent); }
  .check.on { background: var(--accent); border-color: var(--accent); color: #fff; }
  .rtitle { flex: 1; font-size: 13px; line-height: 1.3; }
  .resume { font-size: 11px; }

  .player { display: flex; flex-direction: column; min-width: 0; background: var(--bg); padding-right: 16px; }
  .src-bar { display: flex; align-items: center; gap: 12px; padding: 8px 14px; border-bottom: 1px solid var(--border); background: var(--surface); }
  .seg { display: flex; gap: 2px; background: var(--surface-2); padding: 3px; border-radius: 8px; }
  .seg button { border: none; background: transparent; padding: 5px 12px; border-radius: 6px; font-weight: 550; font-size: 12.5px; color: var(--text-2); }
  .seg button.active { background: var(--surface); color: var(--text); box-shadow: var(--shadow); }
  .seg button:disabled { opacity: .4; cursor: not-allowed; }
  .srcnote { font-size: 12px; }
  .stage { flex: 1; min-height: 0; display: flex; background: #000; }
  .stage video, .stage .ytframe { flex: 1; min-height: 0; width: 100%; height: 100%; background: #000; object-fit: contain; border: 0; }
  .meta { padding: 12px 18px; border-top: 1px solid var(--border); background: var(--surface); }
  .vt { font-weight: 600; }
</style>
