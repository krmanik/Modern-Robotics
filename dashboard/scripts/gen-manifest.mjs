// Scan slides/ + coursera/ and emit src/lib/data/manifest.json.
import { readdir, writeFile, mkdir } from 'node:fs/promises';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..', '..');
const OUT = join(__dirname, '..', 'src', 'lib', 'data', 'manifest.json');

const CH = [
  { id: 'ch01', n: 1,  title: 'Preview',                       start: 21,  end: 30,  ex: null },
  { id: 'ch02', n: 2,  title: 'Configuration Space',           start: 31,  end: 76,  ex: 58 },
  { id: 'ch03', n: 3,  title: 'Rigid-Body Motions',            start: 77,  end: 154, ex: 134 },
  { id: 'ch04', n: 4,  title: 'Forward Kinematics',            start: 155, end: 188, ex: 178 },
  { id: 'ch05', n: 5,  title: 'Velocity Kinematics & Statics', start: 189, end: 236, ex: 220 },
  { id: 'ch06', n: 6,  title: 'Inverse Kinematics',            start: 237, end: 262, ex: 254 },
  { id: 'ch07', n: 7,  title: 'Kinematics of Closed Chains',   start: 263, end: 288, ex: 281 },
  { id: 'ch08', n: 8,  title: 'Dynamics of Open Chains',       start: 289, end: 346, ex: 343 },
  { id: 'ch09', n: 9,  title: 'Trajectory Generation',         start: 347, end: 374, ex: 370 },
  { id: 'ch10', n: 10, title: 'Motion Planning',               start: 375, end: 424, ex: 420 },
  { id: 'ch11', n: 11, title: 'Robot Control',                 start: 425, end: 482, ex: 475 },
  { id: 'ch12', n: 12, title: 'Grasping and Manipulation',     start: 483, end: 534, ex: 526 },
  { id: 'ch13', n: 13, title: 'Wheeled Mobile Robots',         start: 535, end: 586, ex: 577 },
];

const sortNat = (a, b) => a.localeCompare(b, undefined, { numeric: true });

// --- YouTube playlist matching ----------------------------------------------
// youtube-playlist.json is [{id,title}] scraped from the official MR playlist:
// https://www.youtube.com/playlist?list=PLggLP4f-rq02vX0OQQ5vrCxbJrzamYDfx
let PLAYLIST = [];
try { PLAYLIST = JSON.parse(readFileSync(join(__dirname, 'youtube-playlist.json'), 'utf8')); }
catch {}
const STOP = new Set('modern robotics chapter part of the a to through and for with in on intro introduction optional review'.split(' '));
const ytNorm = (s) => s.toLowerCase().replace(/modern robotics,?/g, ' ').replace(/\(.*?\)/g, ' ')
  .replace(/chapter[\s0-9.\-–]*/g, ' ').replace(/part \d+ of \d+/g, ' ').replace(/[^a-z0-9]+/g, ' ').trim();
const ytToks = (s) => new Set(ytNorm(s).split(' ').filter(w => w && !STOP.has(w)));
const ytSecs = (s) => (s.match(/\d+\.\d+(?:\.\d+)?/g) || []);
function ytScore(a, b) {
  const ta = ytToks(a), tb = ytToks(b);
  let inter = 0; for (const t of ta) if (tb.has(t)) inter++;
  const jac = inter / (ta.size + tb.size - inter || 1);
  const sa = ytSecs(a), sb = ytSecs(b);
  const secMatch = sa.length && sb.length && sa.some(x => sb.includes(x)) ? 0.4 : 0;
  return jac + secMatch;
}
function matchYouTube(label) {
  let best = null, bs = 0;
  for (const p of PLAYLIST) { const s = ytScore(label, p.title); if (s > bs) { bs = s; best = p; } }
  return bs >= 0.3 ? best.id : null;
}

async function ls(dir) {
  try { return await readdir(dir, { withFileTypes: true }); }
  catch { return []; }
}

// --- slides: slides/ChNN/pdf/*.pdf -------------------------------------------
async function slidesFor(n) {
  const folder = `Ch${String(n).padStart(2, '0')}`;
  const dir = join(ROOT, 'slides', folder, 'pdf');
  const files = (await ls(dir)).filter(f => f.isFile() && f.name.endsWith('.pdf')).map(f => f.name).sort(sortNat);
  return files.map(name => ({
    label: name.replace(/\.pdf$/, '').replace(/-edited$/, ' (annotated)'),
    url: `/slides/${folder}/pdf/${name}`,
  }));
}

// --- videos: coursera/courseX/Week.../NN - Title.mp4 -------------------------
// Map each week to a chapter by the "Chapter N" token in the folder name.
function chapterOfWeek(weekName) {
  const m = weekName.match(/Chapter\s+(\d+)/i);
  return m ? Number(m[1]) : null;
}

async function allVideos() {
  const byChapter = {};       // n -> [{label,url,vtt,week}]
  const capstone = [];
  const courses = (await ls(join(ROOT, 'coursera'))).filter(d => d.isDirectory()).map(d => d.name).sort(sortNat);
  for (const course of courses) {
    const weeks = (await ls(join(ROOT, 'coursera', course))).filter(d => d.isDirectory()).map(d => d.name).sort(sortNat);
    for (const week of weeks) {
      const wd = join(ROOT, 'coursera', course, week);
      const mp4s = (await ls(wd)).filter(f => f.isFile() && f.name.endsWith('.mp4')).map(f => f.name).sort(sortNat);
      const vtts = new Set((await ls(wd)).filter(f => f.name.endsWith('.vtt')).map(f => f.name));
      const items = mp4s.map(name => {
        const base = name.replace(/\.mp4$/, '');
        const vtt = vtts.has(base + '.vtt') ? `/coursera/${course}/${week}/${base}.vtt` : null;
        const label = base.replace(/^\d+\s*-\s*/, '');
        return {
          label,
          url: `/coursera/${course}/${week}/${name}`,
          vtt,
          yt: matchYouTube(label),
          week: week.replace(/^Week\s+\d+\s*-\s*/, ''),
        };
      });
      const n = chapterOfWeek(week);
      const isCapstone = /capstone/i.test(course) || /capstone|milestone/i.test(week);
      if (isCapstone) { for (const it of items) capstone.push(it); }
      else if (n) { (byChapter[n] ||= []).push(...items); }
      else { (byChapter[1] ||= []).push(...items); } // intro week -> chapter 1
    }
  }
  return { byChapter, capstone };
}

const main = async () => {
  const { byChapter, capstone } = await allVideos();
  const chapters = [];
  for (const c of CH) {
    chapters.push({
      ...c,
      pdf: `/book/${c.id}.pdf`,
      exPdf: c.ex ? `/book/${c.id}-ex.pdf` : null,
      pages: c.end - c.start + 1,
      slides: await slidesFor(c.n),
      videos: byChapter[c.n] || [],
    });
  }
  // Capstone pseudo-chapter
  chapters.push({
    id: 'capstone', n: 14, title: 'Capstone Project', start: null, end: null, ex: null,
    pdf: null, exPdf: null, pages: 0, slides: [], videos: capstone,
  });

  await mkdir(dirname(OUT), { recursive: true });
  await writeFile(OUT, JSON.stringify({ generated: new Date().toISOString(), chapters }, null, 2));
  const vids = chapters.reduce((a, c) => a + c.videos.length, 0);
  const sld = chapters.reduce((a, c) => a + c.slides.length, 0);
  console.log(`manifest: ${chapters.length} chapters, ${sld} slide decks, ${vids} videos`);
};
main();
