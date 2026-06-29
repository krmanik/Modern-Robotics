<script>
  import PdfViewer from './PdfViewer.svelte';
  import { store, persist } from '../stores/store.svelte.js';

  let { chapter } = $props();
  let deck = $state((store.slides[chapter.id]?.deck) || 0);
  let page = $state((store.slides[chapter.id]?.page) || 1);

  if (deck >= chapter.slides.length) deck = 0;
  const current = $derived(chapter.slides[deck]);

  function pickDeck(i) {
    if (i === deck) return;
    deck = i; page = 1;
    store.slides[chapter.id] = { deck, page };
    persist();
  }
  function onpagechange(p) { store.slides[chapter.id] = { deck, page: p }; persist(); }
</script>

<div class="slides">
  {#if chapter.slides.length === 0}
    <div class="empty">No slides for this chapter.</div>
  {:else}
  {#if chapter.slides.length > 1}
    <div class="decks">
      {#each chapter.slides as s, i}
        <button class="deck" class:active={i === deck} onclick={() => pickDeck(i)}>{s.label}</button>
      {/each}
    </div>
  {/if}
  <div class="vwrap">
    {#key current.url}
      <PdfViewer url={current.url} bind:page {onpagechange} />
    {/key}
  </div>
  {/if}
</div>

<style>
  .slides { display: flex; flex-direction: column; height: 100%; min-height: 0; }
  .decks { display: flex; gap: 6px; padding: 10px 14px; border-bottom: 1px solid var(--border); background: var(--surface); overflow-x: auto; }
  .deck {
    flex: none; border: 1px solid var(--border-strong); background: var(--surface);
    padding: 5px 11px; border-radius: 20px; font-size: 12.5px; font-weight: 500; color: var(--text-2);
    white-space: nowrap;
  }
  .deck:hover { background: var(--surface-2); color: var(--text); }
  .deck.active { background: var(--accent); border-color: var(--accent); color: #fff; }
  .vwrap { flex: 1; min-height: 0; }
  .empty { flex: 1; display: grid; place-items: center; color: var(--text-3); }
</style>
