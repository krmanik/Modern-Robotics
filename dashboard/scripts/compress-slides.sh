#!/usr/bin/env bash
# Copy + compress the lecture slide PDFs from ../slides into the committed
# public/slides/ folder (Ghostscript /ebook). Skips files already up to date.
# Requires: ghostscript (`brew install ghostscript` / `apt install ghostscript`).
set -euo pipefail

cd "$(dirname "$0")/.."          # dashboard/
SRC="../slides"
DST="public/slides"

command -v gs >/dev/null || { echo "Ghostscript (gs) not found. Install it first."; exit 1; }
[ -d "$SRC" ] || { echo "No $SRC directory — nothing to compress."; exit 0; }

mkdir -p "$DST"
n=0
while IFS= read -r f; do
  rel="${f#"$SRC"/}"                       # ChNN/pdf/Name.pdf
  out="$DST/$rel"
  mkdir -p "$(dirname "$out")"
  if [ -s "$out" ] && [ "$(wc -c < "$out")" -le "$(wc -c < "$f")" ]; then continue; fi
  gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
     -dNOPAUSE -dQUIET -dBATCH -sOutputFile="$out" "$f" 2>/dev/null || cp "$f" "$out"
  # if compression grew the file, keep the original instead
  if [ ! -s "$out" ] || [ "$(wc -c < "$out")" -gt "$(wc -c < "$f")" ]; then cp "$f" "$out"; fi
  n=$((n + 1))
done < <(find "$SRC" -name '*.pdf')

echo "compressed/updated $n slide PDF(s) -> $DST ($(du -sh "$DST" | cut -f1))"
