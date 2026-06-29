# Modern Robotics — Study Workspace

An offline-first study dashboard for **_Modern Robotics: Mechanics, Planning, and
Control_** (Kevin M. Lynch & Frank C. Park, Cambridge University Press, 2017).
It brings the textbook, lecture slides, video lectures, end-of-chapter exercises,
your notes & highlights, and in-browser Python coding challenges together — one
clean, chapter-by-chapter interface.

The web app (in [`dashboard/`](dashboard/)) is built with **Svelte 5 + Vite** and
runs entirely in the browser. All progress is stored locally and can be exported.

The textbook, the per-chapter/exercise PDFs, and the compressed lecture slides are
committed to this repo, so the app works as soon as you clone it. The video library
is not bundled — lectures stream from YouTube by default, and you can optionally
download them for fully local playback.

---

## Quick start

**Live demo:** https://krmanik.github.io/Modern-Robotics/ — runs in the browser, videos stream from YouTube. Nothing to install.

Run it locally:

```bash
git clone https://github.com/krmanik/Modern-Robotics
cd Modern-Robotics/dashboard
npm install
npm run dev        # open the printed http://localhost:5173
```

That's it. The book, exercises and slides are already in place, and videos stream
from YouTube. No accounts, downloads, or API keys required.

---

## Features

| Tab | What it does |
|-----|--------------|
| **Reader** | The book split per chapter — continuous scroll, zoom, page jump, reading-progress tracking. Select text to **highlight** or **save as a note**. |
| **Videos** | The lectures for each chapter, with a **YouTube / Local file** source switch, subtitles, resume position, and per-lecture watched tracking. |
| **Slides** | The official lecture slide decks (annotated variants included). |
| **Exercises** | Just the exercises pages of each chapter, as a focused PDF. |
| **Challenges** | LeetCode-style Python problems set in each chapter's context (48 in total). Real Python runs in-browser via **Pyodide** against hidden tests, with a syntax-highlighted editor. |
| **Notes** | All highlights & notes for a chapter — edit, delete, jump back to the page. |

Per-chapter **progress** combines reading, exercises, videos watched, and
challenges solved. Each chapter can be **marked complete** or **reset** from the
`⋯` menu. Everything persists in `localStorage`; use **Export / Import** in the
sidebar to back it up or move it between machines.

---

## Optional: download videos for fully local playback

If you want offline video (e.g. on a plane), download the Coursera lectures with
the included helper. You must have access to the free *Modern Robotics*
specialization on Coursera.

The specialization is six courses:

| Folder    | Course URL |
|-----------|------------|
| `course1` | https://www.coursera.org/learn/modernrobotics-course1 |
| `course2` | https://www.coursera.org/learn/modernrobotics-course2 |
| `course3` | https://www.coursera.org/learn/modernrobotics-course3 |
| `course4` | https://www.coursera.org/learn/modernrobotics-course4 |
| `course5` | https://www.coursera.org/learn/modernrobotics-course5 |
| `course6` | https://www.coursera.org/learn/modernrobotics-course6 |

**1. Provide your login cookie.** Coursera needs a logged-in `CAUTH` cookie:

- *Cookie file (recommended):* with a "cookies.txt" / "Cookie-Editor" browser
  extension, log into coursera.org and export cookies to a file in the repo root
  (Netscape `cookies.txt` or JSON — both work). It's auto-detected. Example:
  ```
  # Netscape HTTP Cookie File
  .coursera.org   TRUE   /   TRUE   0   CAUTH   <your-cauth-token>
  ```
- *From the browser:* choose `b` at the prompt to read cookies straight from
  Chrome/Brave/Edge/Firefox/Safari (installs `browser_cookie3` for you).

Cookie files are credentials — they're git-ignored. Keep them private.

**2. Run the downloader once per course:**

```bash
pip install requests
python3 coursera_downloader.py        # interactive; --demo shows the flow offline
```

Paste each course URL, pick your cookies, and **name the output folder `course1` …
`course6`** (matching the table). It writes
`coursera/courseN/Week X – …/NN – Title.mp4` plus `.vtt` subtitles and resumes
interrupted downloads. Then flip the Videos tab to **Local file**.

---

## Regenerating bundled data

Only needed if you change the source PDFs/slides or the challenge set:

```bash
cd dashboard
npm run split             # MR-v2.pdf -> public/book/chNN.pdf + chNN-ex.pdf
npm run compress-slides   # ../slides/**/*.pdf -> public/slides/ (Ghostscript /ebook)
npm run manifest          # scan slides + coursera, map YouTube ids -> manifest.json
npm run challenges        # author challenges -> challenges.json (needs python3)
npm run data              # all of the above in order
```

The YouTube mapping uses `dashboard/scripts/youtube-playlist.json` (scraped from the
official playlist); `npm run manifest` fuzzy-matches each lecture to its video id.

---

## Project structure

```
modern-robotics/
├─ MR-v2.pdf                       # textbook (committed)
├─ coursera_downloader.py          # optional video downloader
├─ slides/                         # raw slide sources incl. .pptx (git-ignored)
├─ coursera/                       # downloaded videos (git-ignored, optional)
└─ dashboard/
   ├─ public/book/                 # per-chapter + per-exercise PDFs (committed)
   ├─ public/slides/               # compressed slide PDFs (committed)
   ├─ scripts/                     # data-generation scripts
   └─ src/                         # the Svelte app
```

The large `slides/` (with `.pptx`) and `coursera/` folders are git-ignored; the
app uses the committed, compressed copies in `dashboard/public/`. In dev, Vite also
serves `coursera/` directly (with range requests) if you've downloaded it.

---

## Hosting (GitHub Pages, etc.)

`npm run build` produces a static bundle in `dashboard/dist/` (app + book + slides;
videos excluded). With the Videos tab on YouTube it's a complete, hostable site. To
trim further, you can drop `public/slides` from the deploy if you only need the
reader.

---

## Acknowledgments & sources

This repository contains original code (the dashboard, scripts, and challenges)
plus copies of freely distributed course materials, included for convenience. All
rights to the course materials remain with their authors and publisher.

- **Textbook — _Modern Robotics_** (`MR-v2.pdf`) © Kevin M. Lynch & Frank C. Park.
  The authors provide the PDF free of charge. Source / latest version:
  **http://modernrobotics.org** and
  **https://hades.mech.northwestern.edu/index.php/Modern_Robotics**
- **Lecture slides** (`dashboard/public/slides/`, compressed) — © the authors,
  from the same Northwestern course page above (download the per-section slide PDFs
  there).
- **Video lectures** — © the authors / Northwestern University. Streamed from the
  official YouTube playlist
  **https://www.youtube.com/playlist?list=PLggLP4f-rq02vX0OQQ5vrCxbJrzamYDfx**,
  or downloadable from the Coursera specialization (links above).
- **Coursera downloader** adapted from
  https://github.com/Sinmane/coursera_downloader.
- **Pyodide** (Python in the browser), **CodeMirror**, **PDF.js**, and **Svelte**
  are used under their respective open-source licenses.

If you are an author/rights-holder and would like material removed, please open an
issue. Use these materials for personal study; respect the original licenses.
