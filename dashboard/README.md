# Modern Robotics — Study Dashboard

A clean, client-side study dashboard for *Modern Robotics* (Lynch & Park, 2nd ed.),
built with Svelte 5 + Vite. Everything runs in the browser; progress, notes,
highlights and solved challenges are saved in `localStorage`.

## Layout
- **Left sidebar** — 13 chapters + Capstone. Shows per-chapter read progress and a
  ✓ when marked complete. Collapsible (on mobile it becomes a slide-in drawer).
- **Top bar** — six tabs: Reader · Slides · Exercises · Challenges · Videos · Notes.
  The `⋯` menu marks a chapter complete or resets its progress.

## Tabs
- **Reader** — the book PDF split per chapter, continuous scroll, zoom, page jump.
  Tracks current/furthest page (read %). Select text to **highlight** (5 colors) or
  **save as a note**.
- **Slides** — the lecture slide decks for the chapter (annotated versions included).
- **Exercises** — just the exercises pages of the chapter as a focused PDF.
- **Challenges** — LeetCode-style Python problems set in the chapter's context
  (48 total). Real Python runs in-browser via **Pyodide** against hidden test cases;
  syntax-highlighted editor (CodeMirror), examples, and a Solution tab.
- **Videos** — the lectures for the chapter, with a **Local file / YouTube** source
  toggle. Local plays the downloaded `.mp4` (subtitles, resume position); YouTube
  embeds the official playlist video (mapped automatically in the manifest). Per-
  lecture "watched" tracking either way.
- **Notes** — all highlights/notes for the chapter; edit, delete, jump back to the page.

## Run it
```bash
cd dashboard
npm install
npm run dev      # open the printed http://localhost:5173
```
The book PDFs (`public/book/`) and compressed slides (`public/slides/`) are committed,
so it works immediately; videos stream from YouTube by default. If you've downloaded
the Coursera videos to `../coursera/`, the dev server serves them too (range-enabled)
and you can switch the Videos tab to **Local file**. See the repo root README for the
full setup and the optional video download.

## Regenerating data (only if source files change)
```bash
npm run split             # MR-v2.pdf -> public/book/chNN.pdf + chNN-ex.pdf
npm run compress-slides   # ../slides/**/*.pdf -> public/slides/ (Ghostscript)
npm run manifest          # scan slides + coursera, map YouTube ids -> manifest.json
npm run challenges        # author challenges -> challenges.json (needs python3)
npm run data              # all of the above
```

## Notes
- Chapter PDF page ranges and exercise pages come from the book's outline.
- Challenge expected outputs are computed from reference solutions at authoring time,
  so they are guaranteed correct.
