#!/usr/bin/env bash
#
# Сборка сайта в отдельный каталог _site/ — для хостингов, которые
# раздают указанную папку (Cloudflare Pages, Netlify, Vercel).
#
# build.py пишет HTML рядом с исходниками, в корень репозитория. Отдавать
# корень наружу нельзя: туда попадут legacy/ (1.8 МБ архива Craftum),
# tools/, .env и заметки. Поэтому после сборки раскладываем только нужное.
#
# Локально:        bash tools/build_site.sh
# Cloudflare Pages: эта же строка в поле «Build command»,
#                   «Build output directory» — _site
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "→ сборка"
python3 tools/build.py

echo "→ проверка"
python3 tools/check.py

echo "→ раскладка в _site/"
rm -rf _site
mkdir -p _site

# rsync есть в образах Cloudflare Pages и GitHub Actions; на голой системе
# без него используем tar как запасной вариант
EXCLUDES=(
  '.git' '.github' '.claude' '.env*' '.gitignore'
  '_site' 'legacy' 'tools' '*.md'
)

if command -v rsync >/dev/null 2>&1; then
  args=()
  for e in "${EXCLUDES[@]}"; do args+=(--exclude="$e"); done
  rsync -a "${args[@]}" ./ _site/
else
  args=()
  for e in "${EXCLUDES[@]}"; do args+=(--exclude="$e"); done
  tar -cf - "${args[@]}" . | (cd _site && tar -xf -)
fi

touch _site/.nojekyll

echo "→ готово: $(find _site -type f | wc -l | tr -d ' ') файлов, $(du -sh _site | cut -f1)"
