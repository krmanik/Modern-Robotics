// Split MR-v2.pdf into per-chapter PDFs + per-chapter exercise PDFs.
// Page numbers are 1-indexed *physical* PDF pages (from the book outline).
import { PDFDocument } from 'pdf-lib';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SRC = join(__dirname, '..', '..', 'MR-v2.pdf');
const OUT = join(__dirname, '..', 'public', 'book');

// id, title, chapter start page, chapter end page, exercises start page (null = none)
const CH = [
  ['ch01', 'Preview',                      21,  30,  null],
  ['ch02', 'Configuration Space',          31,  76,  58],
  ['ch03', 'Rigid-Body Motions',           77,  154, 134],
  ['ch04', 'Forward Kinematics',           155, 188, 178],
  ['ch05', 'Velocity Kinematics & Statics',189, 236, 220],
  ['ch06', 'Inverse Kinematics',           237, 262, 254],
  ['ch07', 'Kinematics of Closed Chains',  263, 288, 281],
  ['ch08', 'Dynamics of Open Chains',      289, 346, 343],
  ['ch09', 'Trajectory Generation',        347, 374, 370],
  ['ch10', 'Motion Planning',              375, 424, 420],
  ['ch11', 'Robot Control',                425, 482, 475],
  ['ch12', 'Grasping and Manipulation',    483, 534, 526],
  ['ch13', 'Wheeled Mobile Robots',        535, 586, 577],
];

async function extract(src, from, to) {
  const out = await PDFDocument.create();
  const idx = [];
  for (let p = from; p <= to; p++) idx.push(p - 1); // 0-indexed
  const pages = await out.copyPages(src, idx);
  pages.forEach((pg) => out.addPage(pg));
  return out.save();
}

const main = async () => {
  await mkdir(OUT, { recursive: true });
  const bytes = await readFile(SRC);
  const src = await PDFDocument.load(bytes, { ignoreEncryption: true });
  for (const [id, title, start, end, ex] of CH) {
    const chBytes = await extract(src, start, end);
    await writeFile(join(OUT, `${id}.pdf`), chBytes);
    let exInfo = '';
    if (ex) {
      const exBytes = await extract(src, ex, end);
      await writeFile(join(OUT, `${id}-ex.pdf`), exBytes);
      exInfo = ` + ex ${ex}-${end}`;
    }
    console.log(`${id} ${title}: pages ${start}-${end}${exInfo}  (${(chBytes.length / 1024 | 0)}KB)`);
  }
  console.log('done');
};
main();
