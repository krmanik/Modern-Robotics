#!/usr/bin/env python3
# https://github.com/Sinmane/coursera_downloader
"""
Coursera Bulk Video Downloader — Interactive Mode

Uses Coursera's internal API directly (yt-dlp does NOT support Coursera).
Requires a valid CAUTH session cookie exported from your logged-in browser.

Requires: pip install requests
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

API = "https://www.coursera.org/api"

# How many times to retry a single video on transient network errors.
MAX_TRIES = 4
# How many videos to download at once (parallelism = speed). Tune to taste.
DEFAULT_WORKERS = 5

# Demo data so the interactive flow can be shown without an account.
DEMO_ITEMS = [
    {"index": 1,  "title": "Welcome to the Course",        "module": "Week 1 - Introduction",      "item_id": "d1", "type": "lecture"},
    {"index": 2,  "title": "What is Machine Learning?",     "module": "Week 1 - Introduction",      "item_id": "d2", "type": "lecture"},
    {"index": 3,  "title": "Supervised vs Unsupervised",    "module": "Week 1 - Introduction",      "item_id": "d3", "type": "lecture"},
    {"index": 4,  "title": "Linear Regression Overview",    "module": "Week 2 - Linear Regression", "item_id": "d4", "type": "lecture"},
    {"index": 5,  "title": "Cost Function Explained",       "module": "Week 2 - Linear Regression", "item_id": "d5", "type": "lecture"},
    {"index": 6,  "title": "Gradient Descent",              "module": "Week 2 - Linear Regression", "item_id": "d6", "type": "lecture"},
    {"index": 7,  "title": "Logistic Regression",           "module": "Week 3 - Classification",    "item_id": "d7", "type": "lecture"},
    {"index": 8,  "title": "Decision Boundary",             "module": "Week 3 - Classification",    "item_id": "d8", "type": "lecture"},
    {"index": 9,  "title": "Neural Networks Introduction",  "module": "Week 4 - Neural Networks",   "item_id": "d9", "type": "lecture"},
    {"index": 10, "title": "Backpropagation",               "module": "Week 4 - Neural Networks",   "item_id": "d10","type": "lecture"},
]


# ── dependencies ──────────────────────────────────────────────────────────────

def check_requests():
    try:
        import requests  # noqa: F401
    except ImportError:
        print("requests not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
        print("requests installed.\n")


# ── cookies ───────────────────────────────────────────────────────────────────

def load_cookies(path: str) -> dict:
    """Load cookies from a JSON export or a Netscape cookies.txt file.
    Returns a dict of {name: value} for coursera.org cookies."""
    text = Path(path).read_text(encoding="utf-8-sig").strip()
    cookies = {}

    # Try JSON first (handles [] and {"cookies": [...]} shapes)
    try:
        data = json.loads(text)
        entries = data if isinstance(data, list) else (data.get("cookies") or [])
        for c in entries:
            if "coursera.org" in c.get("domain", ""):
                cookies[c["name"]] = c["value"]
        return cookies
    except json.JSONDecodeError:
        pass

    # Otherwise parse Netscape format
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 7 and "coursera.org" in parts[0]:
            cookies[parts[5]] = parts[6]
    return cookies


def load_browser_cookies(browser: str) -> dict:
    """Read coursera.org cookies directly from the browser via browser_cookie3."""
    try:
        import browser_cookie3
    except ImportError:
        print("Installing browser_cookie3 (needed to read browser cookies)...")
        subprocess.run([sys.executable, "-m", "pip", "install", "browser-cookie3"], check=True)
        import browser_cookie3

    loaders = {
        "chrome":   browser_cookie3.chrome,
        "chromium": browser_cookie3.chromium,
        "brave":    browser_cookie3.brave,
        "opera":    browser_cookie3.opera,
        "edge":     browser_cookie3.edge,
        "vivaldi":  browser_cookie3.vivaldi,
        "firefox":  browser_cookie3.firefox,
        "safari":   browser_cookie3.safari,
    }
    cj = loaders[browser](domain_name="coursera.org")
    return {c.name: c.value for c in cj}


# ── Coursera API client ───────────────────────────────────────────────────────

class Coursera:
    def __init__(self, cookies: dict):
        import requests
        from requests.adapters import HTTPAdapter
        try:
            from urllib3.util.retry import Retry
        except ImportError:  # very old urllib3
            from requests.packages.urllib3.util.retry import Retry

        self.s = requests.Session()
        self.s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Referer": "https://www.coursera.org/",
        })

        # Transport-level retries handle brief DNS/connection blips automatically,
        # with exponential backoff between attempts.
        retry = Retry(
            total=5, connect=5, read=5,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET"]),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.s.mount("https://", adapter)
        self.s.mount("http://", adapter)

        for name, value in cookies.items():
            self.s.cookies.set(name, value, domain=".coursera.org")
        # Coursera GET API calls require the CSRF3 token echoed as a header.
        csrf = cookies.get("CSRF3-Token")
        if csrf:
            self.s.headers["X-CSRF3-Token"] = csrf

    def _get(self, url: str) -> dict:
        r = self.s.get(url, timeout=30)
        if r.status_code in (401, 403):
            raise PermissionError(
                f"Authentication failed (HTTP {r.status_code}). "
                "Your CAUTH cookie is missing or expired — re-export a fresh cookies file."
            )
        r.raise_for_status()
        return r.json()

    def course_id(self, slug: str) -> str:
        data = self._get(f"{API}/onDemandCourses.v1?q=slug&slug={slug}")
        elements = data.get("elements") or []
        if not elements:
            raise ValueError(f"Course '{slug}' not found (are you enrolled?).")
        return elements[0]["id"]

    def materials(self, slug: str) -> list[dict]:
        """Return ordered list of lecture items: {title, module, item_id, type}."""
        fields = (
            "onDemandCourseMaterialModules.v1(name,lessonIds),"
            "onDemandCourseMaterialLessons.v1(name,itemIds),"
            "onDemandCourseMaterialItems.v2(name,contentSummary)"
        )
        url = (
            f"{API}/onDemandCourseMaterials.v2/?q=slug&slug={slug}"
            f"&includes=modules,lessons,items&fields={fields}&showLockedItems=true"
        )
        data = self._get(url)
        linked = data.get("linked", {})

        # The course element doesn't carry moduleIds — the modules array itself
        # is already in course order, so iterate it directly.
        module_list = linked.get("onDemandCourseMaterialModules.v1", [])
        lessons = {l["id"]: l for l in linked.get("onDemandCourseMaterialLessons.v1", [])}
        items   = {i["id"]: i for i in linked.get("onDemandCourseMaterialItems.v2", [])}

        ordered = []
        idx = 0
        for week_num, mod in enumerate(module_list, 1):
            mod_name = f"Week {week_num} - {mod.get('name', 'Module')}"
            for les_id in mod.get("lessonIds", []):
                les = lessons.get(les_id, {})
                for it_id in les.get("itemIds", []):
                    it = items.get(it_id, {})
                    summary = it.get("contentSummary", {}) or {}
                    type_name = summary.get("typeName", "")
                    if type_name != "lecture":
                        continue  # skip quizzes, readings, etc.
                    idx += 1
                    ordered.append({
                        "index":   idx,
                        "title":   it.get("name", f"Video {idx}"),
                        "module":  mod_name,
                        "item_id": it_id,
                        "type":    type_name,
                    })
        return ordered

    def video_sources(self, course_id: str, item_id: str) -> dict:
        """Return {'mp4': {res: url}, 'subtitles': {lang: url}} for a lecture item."""
        fields = "onDemandVideos.v1(sources,subtitles,subtitlesVtt)"
        url = f"{API}/onDemandLectureVideos.v1/{course_id}~{item_id}?includes=video&fields={fields}"
        data = self._get(url)
        videos = data.get("linked", {}).get("onDemandVideos.v1", [])
        if not videos:
            return {"mp4": {}, "subtitles": {}}
        v = videos[0]

        mp4 = {}
        sources = v.get("sources", {})
        by_res = sources.get("byResolution", {}) if isinstance(sources, dict) else {}
        for res, info in by_res.items():
            if isinstance(info, dict) and info.get("mp4VideoUrl"):
                mp4[res] = info["mp4VideoUrl"]

        subs = v.get("subtitlesVtt") or v.get("subtitles") or {}
        subtitles = {}
        for lang, rel in subs.items():
            subtitles[lang] = rel if rel.startswith("http") else "https://www.coursera.org" + rel

        return {"mp4": mp4, "subtitles": subtitles}

    def remote_size(self, url: str) -> int:
        """Content-Length of the remote file (0 if the server won't say)."""
        try:
            r = self.s.head(url, timeout=20, allow_redirects=True)
            if r.ok:
                return int(r.headers.get("content-length", 0))
        except Exception:
            pass
        return 0

    def download_resumable(self, url: str, dest: Path, on_progress=None) -> str:
        """Download `url` to `dest`, resuming a partial `.part` file via HTTP Range.

        `on_progress(done_bytes, total_bytes)` is called as data arrives (total may
        be 0 if the server won't report a size).

        Returns:
          'skip'  — a complete file already exists (verified by size)
          'ok'    — downloaded (or resumed and finished) successfully
        Raises on network failure so the caller can retry.
        """
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_name(dest.name + ".part")
        remote = self.remote_size(url)

        # A finished file already present and the right size? Nothing to do.
        if dest.exists():
            if remote and dest.stat().st_size == remote:
                return "skip"
            if not remote and dest.stat().st_size > 0:
                return "skip"  # can't verify size, assume the existing file is good
            dest.unlink()  # 0-byte or wrong-size — re-download

        have = part.stat().st_size if part.exists() else 0
        headers = {}
        mode = "wb"
        if have and remote and have < remote:
            headers["Range"] = f"bytes={have}-"   # resume where we left off
            mode = "ab"
        elif have and remote and have >= remote:
            part.replace(dest)                    # .part already complete
            return "ok"
        else:
            have = 0  # start fresh

        try:
            with self.s.get(url, stream=True, timeout=(15, 300), headers=headers) as r:
                # If we asked to resume but the server ignored it, restart cleanly.
                if "Range" in headers and r.status_code == 200:
                    mode = "wb"
                    have = 0
                r.raise_for_status()
                done = have  # bytes already on disk count toward the total
                if on_progress:
                    on_progress(done, remote)
                with open(part, mode) as f:
                    for chunk in r.iter_content(chunk_size=1 << 18):  # 256 KB chunks
                        if chunk:
                            f.write(chunk)
                            done += len(chunk)
                            if on_progress:
                                on_progress(done, remote)
            # Verify the finished size when the server told us what to expect.
            if remote and part.stat().st_size != remote:
                raise IOError(
                    f"size mismatch (got {part.stat().st_size}, expected {remote})"
                )
            part.replace(dest)
            return "ok"
        except BaseException:
            # Keep the .part file on a transient failure so the next run resumes
            # from here; only the size-mismatch case above discards it.
            raise


# ── helpers ───────────────────────────────────────────────────────────────────

def extract_slug(url: str) -> str:
    """Pull the course slug out of any Coursera URL or accept a bare slug."""
    m = re.search(r"/learn/([^/?#]+)", url)
    if m:
        return m.group(1)
    return url.strip().strip("/")


def parse_range(text: str, maximum: int) -> list[int]:
    """Parse user input like '1,3,5-7' into a sorted list of ints."""
    result = set()
    for part in text.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            result.update(range(int(a), int(b) + 1))
        elif part:
            result.add(int(part))
    return sorted(i for i in result if 1 <= i <= maximum)


def sanitize(name: str) -> str:
    """Make a string safe for use as a Windows filename."""
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip().rstrip(".")


def group_by_module(items: list[dict]) -> dict[str, list[dict]]:
    groups = defaultdict(list)
    for it in items:
        groups[it["module"]].append(it)
    return dict(groups)


# ── display & selection ───────────────────────────────────────────────────────

def print_course(weeks: dict[str, list[dict]]):
    print()
    for week, vids in weeks.items():
        indices = f"{vids[0]['index']}-{vids[-1]['index']}"
        print(f"  [{indices:>7}]  {week}")
        for v in vids:
            print(f"             {v['index']:>3}. {v['title']}")
    print()


def select_videos(videos: list[dict], weeks: dict[str, list[dict]]) -> list[dict]:
    total = len(videos)
    week_names = list(weeks.keys())

    print("=" * 60)
    print("SELECTION OPTIONS")
    print("=" * 60)
    print("  a          Download ALL videos")
    print("  w          Select by WEEK")
    print("  v          Select specific VIDEOS by number")
    print("  wv         Select a week, then specific videos within it")
    print("=" * 60)
    choice = input("Your choice: ").strip().lower()

    if choice == "a":
        print(f"\nSelected: all {total} videos.")
        return videos

    if choice == "w":
        print("\nWeeks:")
        for i, name in enumerate(week_names, 1):
            print(f"  {i:>3}. {name}  ({len(weeks[name])} videos)")
        raw = input("\nEnter week numbers (e.g. 1,3,5-7): ").strip()
        selected_weeks = parse_range(raw, len(week_names))
        selected = []
        for wi in selected_weeks:
            selected.extend(weeks[week_names[wi - 1]])
        print(f"\nSelected: {len(selected)} videos from {len(selected_weeks)} week(s).")
        return selected

    if choice == "v":
        print_course(weeks)
        raw = input(f"Enter video numbers (e.g. 1,3,5-7, max {total}): ").strip()
        index_set = set(parse_range(raw, total))
        selected = [v for v in videos if v["index"] in index_set]
        print(f"\nSelected: {len(selected)} video(s).")
        return selected

    if choice == "wv":
        print("\nWeeks:")
        for i, name in enumerate(week_names, 1):
            print(f"  {i:>3}. {name}  ({len(weeks[name])} videos)")
        wi = int(input("\nEnter ONE week number: ").strip())
        week_name = week_names[wi - 1]
        week_vids = weeks[week_name]
        print(f"\nVideos in '{week_name}':")
        for local_i, v in enumerate(week_vids, 1):
            print(f"  {local_i:>3}. {v['title']}")
        raw = input("\nEnter video numbers to download (or 'a' for all in this week): ").strip()
        if raw.lower() == "a":
            selected = week_vids
        else:
            local_indices = set(parse_range(raw, len(week_vids)))
            selected = [v for li, v in enumerate(week_vids, 1) if li in local_indices]
        print(f"\nSelected: {len(selected)} video(s) from '{week_name}'.")
        return selected

    print("Unrecognised option. Exiting.")
    sys.exit(0)


# ── download orchestration ────────────────────────────────────────────────────

def pick_resolution(mp4: dict, quality: str) -> str | None:
    """Choose the best available mp4 URL for the requested quality."""
    order = ["720p", "540p", "360p"]
    if quality == "720p":
        prefs = ["720p", "540p", "360p"]
    elif quality == "480p":
        prefs = ["540p", "360p", "720p"]
    else:  # best
        prefs = ["720p", "540p", "360p"]
    for res in prefs:
        if res in mp4:
            return mp4[res]
    # fall back to anything present
    for res in order:
        if res in mp4:
            return mp4[res]
    return next(iter(mp4.values()), None)


def _human_size(n: int) -> str:
    return f"{n / (1 << 20):.1f} MB" if n < (1 << 30) else f"{n / (1 << 30):.2f} GB"


def _short(text: str, width: int) -> str:
    """Truncate/pad a title to a fixed width (ASCII-safe for Windows consoles)."""
    text = text.encode("ascii", "replace").decode("ascii")  # avoid console encode errors
    if len(text) > width:
        text = text[: width - 3] + "..."
    return text.ljust(width)


def _bar(done: int, total: int, width: int = 18) -> str:
    """A textual progress bar like '[####------]  42%   11.1/27.0 MB'."""
    if total > 0:
        frac = min(1.0, done / total)
        filled = int(frac * width)
        return (f"[{'#' * filled}{'-' * (width - filled)}] {frac * 100:3.0f}%  "
                f"{done / (1 << 20):5.1f}/{total / (1 << 20):5.1f} MB")
    # Unknown size — just show how much has arrived.
    return f"[{'-' * width}]  ..   {done / (1 << 20):5.1f} MB"


class LiveDisplay:
    """A multi-line, in-place progress dashboard for parallel downloads.

    Reserves `slots` lines at the bottom of the terminal — one per concurrent
    download, each showing the video name and a live progress bar. Completed
    videos are printed as permanent lines that scroll above the dashboard.

    Falls back to plain one-line-per-finish output when stdout isn't a TTY
    (e.g. piped to a file or run in the background), so logs stay clean.
    """

    def __init__(self, slots: int, total: int):
        self.n = max(1, slots)
        self.total = total
        self.slots = [None] * self.n      # each: [title, done, total] or None
        self.lock = Lock()
        self.completed = 0
        self.tty = bool(getattr(sys.stdout, "isatty", lambda: False)())
        self.drawn = False
        self._last_paint = 0.0

    # ---- internal (assume lock held) ----
    def _paint_dashboard(self):
        for slot in self.slots:
            sys.stdout.write("\033[2K")  # clear the whole line
            if slot:
                title, done, total = slot
                sys.stdout.write(f"  > {_short(title, 30)}  {_bar(done, total)}\n")
            else:
                sys.stdout.write("  . (idle)\n")
        sys.stdout.flush()

    def _repaint(self):
        # Cursor sits just below the dashboard; move up and redraw in place.
        sys.stdout.write(f"\033[{self.n}A")
        self._paint_dashboard()

    # ---- public ----
    def start(self):
        if self.tty:
            with self.lock:
                self._paint_dashboard()  # draw initial idle dashboard
                self.drawn = True

    def acquire(self, title: str) -> int:
        with self.lock:
            i = self.slots.index(None) if None in self.slots else 0
            self.slots[i] = [title, 0, 0]
            if self.drawn:
                self._repaint()
            return i

    def update(self, i: int, done: int, total: int):
        now = time.time()
        with self.lock:
            if self.slots[i] is None:
                return
            self.slots[i][1] = done
            self.slots[i][2] = total
            # Throttle redraws to keep the terminal smooth (~12 fps).
            if self.drawn and (now - self._last_paint >= 0.08 or done >= total > 0):
                self._last_paint = now
                self._repaint()

    def release(self, i: int):
        """Free a slot (e.g. before a retry) and refresh the dashboard."""
        with self.lock:
            if 0 <= i < self.n:
                self.slots[i] = None
                if self.drawn:
                    self._repaint()

    def complete(self, i, message: str):
        """Free slot `i` (if any) and print a permanent completed line."""
        with self.lock:
            self.completed += 1
            line = f"[{self.completed}/{self.total}] {message}"
            if i is not None:
                self.slots[i] = None
            if self.tty and self.drawn:
                sys.stdout.write(f"\033[{self.n}A")  # up to dashboard top
                sys.stdout.write("\033[J")           # erase dashboard
                sys.stdout.write(line + "\n")        # permanent scrolled line
                self._paint_dashboard()              # redraw dashboard below
            else:
                print(line, flush=True)

    def stop(self):
        with self.lock:
            if self.tty and self.drawn:
                sys.stdout.write(f"\033[{self.n}A\033[J")  # erase dashboard
                sys.stdout.flush()
                self.drawn = False


def download_videos(client, course_id, selected, output_dir, quality, dry_run,
                    get_subs, demo=False, workers=DEFAULT_WORKERS):
    total = len(selected)

    if demo:
        for i, v in enumerate(selected, 1):
            print(f"[{i}/{total}] {v['title']} ... ", end="", flush=True)
            time.sleep(0.2)
            print("done")
        print(f"\n[DEMO] All {total} video(s) would be saved to: {output_dir.resolve()}")
        return

    if dry_run:
        print(f"\nDRY RUN — these {total} video(s) would be downloaded to {output_dir.resolve()}:\n")
        for v in selected:
            print(f"  [{v['index']:>3}] {v['module']} / {v['title']}")
        print("\nNo files were saved. Re-run with 'Dry run? n' to actually download.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    workers = max(1, min(workers, total))
    print(f"\nDownloading {total} video(s) with {workers} parallel connection(s)")
    print(f"into: {output_dir.resolve()}\n")

    state = {"ok": 0, "skipped": 0, "locked": 0, "bytes": 0}
    state_lock = Lock()
    failed = []
    display = LiveDisplay(workers, total)

    def attempt(v) -> tuple[str, int]:
        """Download one video (with retries). Returns (status, bytes_written)."""
        week_dir = output_dir / sanitize(v["module"])
        base = f"{v['index']:02d} - {sanitize(v['title'])}"
        video_path = week_dir / f"{base}.mp4"

        for tries in range(1, MAX_TRIES + 1):
            slot = None
            try:
                src = client.video_sources(course_id, v["item_id"])
                url = pick_resolution(src["mp4"], quality)
                if not url:
                    return ("locked", 0)

                slot = display.acquire(v["title"])
                status = client.download_resumable(
                    url, video_path,
                    on_progress=lambda d, t, s=slot: display.update(s, d, t),
                )
                size = video_path.stat().st_size if video_path.exists() else 0

                if get_subs and src["subtitles"]:
                    sub_url = src["subtitles"].get("en") or next(iter(src["subtitles"].values()))
                    sub_path = week_dir / f"{base}.vtt"
                    if not (sub_path.exists() and sub_path.stat().st_size > 0):
                        try:
                            client.download_resumable(sub_url, sub_path)
                        except Exception:
                            pass  # subtitles are best-effort

                return (status, size, slot)  # 'ok' or 'skip'

            except Exception as e:
                if slot is not None:
                    display.release(slot)
                if tries < MAX_TRIES:
                    time.sleep(3 * tries)
                else:
                    return (f"fail:{e}", 0, None)

    start = time.time()
    display.start()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(attempt, v): v for v in selected}
        for fut in as_completed(futures):
            v = futures[fut]
            status, size, slot = fut.result()
            with state_lock:
                if status == "ok":
                    state["ok"] += 1
                    state["bytes"] += size
                    display.complete(slot, f"OK    {v['title']}  ({_human_size(size)})")
                elif status == "skip":
                    state["skipped"] += 1
                    display.complete(slot, f"have  {v['title']}  (already complete)")
                elif status == "locked":
                    state["locked"] += 1
                    display.complete(slot, f"LOCK  {v['title']}  (no downloadable video)")
                else:
                    failed.append(v)
                    display.complete(slot, f"FAIL  {v['title']}  ({status[5:]})")
    display.stop()

    elapsed = time.time() - start
    bps = state["bytes"] / elapsed if elapsed > 0 else 0
    speed = f"{bps / (1 << 20):.1f} MB/s" if bps >= (1 << 20) else f"{bps / 1024:.0f} KB/s"

    print("\n" + "=" * 60)
    parts = [f"{state['ok']} downloaded", f"{state['skipped']} already had"]
    if state["locked"]:
        parts.append(f"{state['locked']} locked")
    if failed:
        parts.append(f"{len(failed)} failed")
    print("Done! " + ", ".join(parts) + ".")
    if state["bytes"]:
        print(f"Transferred {_human_size(state['bytes'])} in {elapsed:.0f}s "
              f"(~{speed}).")
    print(f"\nFiles saved to:\n  {output_dir.resolve()}")
    print("Tip: paste that path into File Explorer's address bar to open it.")
    if failed:
        print("\nThese videos still failed (network problems persisted):")
        for v in failed:
            print(f"  - [{v['index']}] {v['title']}")
        print("Just run the script again with the same output folder — it resumes")
        print("partial files and skips completed ones, retrying only these.")
    print("=" * 60)


# ── main ──────────────────────────────────────────────────────────────────────

def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{label}{suffix}: ").strip()
    return val or default


def find_cookie_files() -> list[str]:
    """Find files in the current folder that contain a valid Coursera CAUTH cookie."""
    found = []
    for p in sorted(Path(".").glob("*"), key=lambda x: -x.stat().st_mtime if x.is_file() else 0):
        if p.is_file() and p.suffix.lower() in (".txt", ".json"):
            try:
                if "CAUTH" in load_cookies(str(p)):
                    found.append(str(p))
            except Exception:
                pass
    return found


def choose_output_folder() -> Path:
    """Let the user reuse an existing download folder or create a new one."""
    # Detect folders that already contain videos, or whose subfolders look like
    # "Week N - ..." — these are previous download targets worth resuming.
    existing = []
    for d in sorted(p for p in Path(".").iterdir() if p.is_dir() and not p.name.startswith((".", "__"))):
        has_videos = any(d.rglob("*.mp4"))
        looks_like = any(sub.is_dir() and sub.name.lower().startswith("week") for sub in d.iterdir())
        if has_videos or looks_like:
            existing.append(d)

    if existing:
        print("\nExisting download folders found (pick one to resume/add to it):")
        for i, d in enumerate(existing, 1):
            count = sum(1 for _ in d.rglob("*.mp4"))
            print(f"  {i}. {d.name}/  ({count} videos so far)")
        print("  n. Create a NEW folder")
        choice = prompt("Choose a folder number or 'n'", "1" if existing else "n")
        if choice.lower() != "n" and choice.isdigit() and 1 <= int(choice) <= len(existing):
            return existing[int(choice) - 1]

    name = prompt("New output folder name", "coursera_downloads")
    return Path(name)


def main():
    demo = "--demo" in sys.argv

    print("=" * 60)
    print("  COURSERA BULK VIDEO DOWNLOADER" + ("  [DEMO MODE]" if demo else ""))
    print("=" * 60)

    if demo:
        items = DEMO_ITEMS
        weeks = group_by_module(items)
        print(f"\n[DEMO] Using mock course data — no network request made.")
        print(f"\nFound {len(items)} videos across {len(weeks)} week(s):\n")
        print_course(weeks)
        selected = select_videos(items, weeks)
        if not selected:
            print("Nothing selected. Exiting.")
            return
        confirm = prompt(f"\nProceed to download {len(selected)} video(s)? y/n", "y")
        if confirm.lower() != "y":
            print("Cancelled.")
            return
        download_videos(None, None, selected, Path("coursera_downloads_demo"),
                        "best", False, True, demo=True)
        return

    check_requests()

    url = prompt("Course URL (e.g. https://www.coursera.org/learn/machine-learning)")
    if not url:
        print("No URL provided. Exiting.")
        return
    slug = extract_slug(url)
    print(f"  Course slug: {slug}")

    SUPPORTED_BROWSERS = ["chrome", "chromium", "brave", "opera", "edge", "vivaldi", "firefox", "safari"]

    # ── Authentication — auto-detect cookie files for a smoother start ──
    cookies = None
    detected = find_cookie_files()
    if detected:
        print(f"\nFound cookie file(s) with a valid Coursera login:")
        for i, f in enumerate(detected, 1):
            print(f"  {i}. {f}")
        print("  b. Read from browser instead")
        choice = prompt("Use which cookies?", "1")
        if choice.isdigit() and 1 <= int(choice) <= len(detected):
            cookies = load_cookies(detected[int(choice) - 1])

    if cookies is None:
        print("\nAuthentication — Coursera requires your login session.")
        print("  1. Use a cookies file (JSON or cookies.txt)")
        print("  2. Read cookies from browser")
        auth_choice = prompt("Choice", "1")
        try:
            if auth_choice == "2":
                print(f"\nSupported browsers: {', '.join(SUPPORTED_BROWSERS)}")
                while True:
                    browser = prompt("Browser", "chrome").lower()
                    if browser in SUPPORTED_BROWSERS:
                        break
                    print(f"  Invalid browser. Choose from: {', '.join(SUPPORTED_BROWSERS)}")
                cookies = load_browser_cookies(browser)
            else:
                path = prompt("Path to cookies file")
                if not path or not Path(path).exists():
                    print("Cookies file not found. Exiting.")
                    return
                cookies = load_cookies(path)
        except Exception as e:
            print(f"\nERROR loading cookies: {e}")
            return

    if "CAUTH" not in cookies:
        print("\nERROR: No CAUTH cookie found — this is the Coursera login token.")
        print("  Make sure you exported cookies while logged in to coursera.org.")
        return
    print(f"  Loaded {len(cookies)} cookies (CAUTH present).")

    # ── Output, quality, speed ──
    output_dir = choose_output_folder()
    quality = prompt("Video quality (best/720p/480p)", "best")
    subs_in = prompt("Download English subtitles? y/n", "y")
    get_subs = subs_in.lower() == "y"
    workers_in = prompt("Parallel downloads (1-10, higher = faster)", str(DEFAULT_WORKERS))
    try:
        workers = max(1, min(10, int(workers_in)))
    except ValueError:
        workers = DEFAULT_WORKERS
    dry_in = prompt("Dry run? (just list, save nothing) y/n", "n")
    dry_run = dry_in.lower() == "y"

    client = Coursera(cookies)

    print("\nFetching course structure (this may take a moment)...")
    try:
        course_id = client.course_id(slug)
        items = client.materials(slug)
    except PermissionError as e:
        print(f"\nERROR: {e}")
        return
    except Exception as e:
        print(f"\nERROR: Could not fetch course structure.\n  {e}")
        return

    if not items:
        print("No video lectures found. The course may have no videos, or you may not be enrolled.")
        return

    weeks = group_by_module(items)
    print(f"\nFound {len(items)} videos across {len(weeks)} week(s):\n")
    print_course(weeks)

    selected = select_videos(items, weeks)
    if not selected:
        print("Nothing selected. Exiting.")
        return

    confirm = prompt(f"\nProceed to download {len(selected)} video(s)? y/n", "y")
    if confirm.lower() != "y":
        print("Cancelled.")
        return

    download_videos(client, course_id, selected, output_dir, quality, dry_run,
                    get_subs, workers=workers)


if __name__ == "__main__":
    main()
