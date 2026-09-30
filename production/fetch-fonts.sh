#!/usr/bin/env bash
# Downloads the three typefaces the book is set in into fonts/lib/.
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p fonts/lib tmpf; cd tmpf
curl -sSL -o ss4.zip https://github.com/adobe-fonts/source-serif/releases/download/4.005R/source-serif-4.005_Desktop.zip
curl -sSL -o ss3.zip https://github.com/adobe-fonts/source-sans/releases/download/3.052R/OTF-source-sans-3.052R.zip
curl -sSL -o jbm.zip https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip
for z in *.zip; do unzip -q -o "$z" -d "${z%.zip}"; done
cp ss4/source-serif-4.005_Desktop/OTF/SourceSerif4-{Regular,It,Bold,BoldIt,Semibold}.otf ../fonts/lib/
cp ss3/OTF/SourceSans3-{Regular,It,Bold,Semibold}.otf ../fonts/lib/
cp jbm/fonts/ttf/JetBrainsMono-{Regular,Bold,Italic}.ttf ../fonts/lib/
cd .. && rm -rf tmpf && ls fonts/lib
