// Teilt eine aus Studio gespeicherte Sammeldatei (Ordner mit KeyframeSequences, "Save to File" als .rbxmx) in einzelne Dateien
// export/anim_rbxmx/<Name>.rbxmx auf (eine KeyframeSequence pro Datei, wie upload_animations_v01.js sie erwartet).
// Quelle: export/CC_AnimUpload_*.rbxmx (alle passenden Dateien). Einzeldateien bereits hochgeladener Animationen (ID in
// roblox/CC_AnimIds.luau) bleiben unberuehrt; noch nicht hochgeladene werden mit dem aktuellen Studio-Stand geschrieben.
// Aufruf: node split_anim_bundle_v01.js
const fs = require('fs'), path = require('path');
const EXP = path.join(__dirname, 'export'), OUT = path.join(EXP, 'anim_rbxmx');
const HEAD = '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">';
const bundles = fs.readdirSync(EXP).filter(f => /^CC_AnimUpload_.*\.rbxmx$/i.test(f));
if (!bundles.length) { console.log('Keine Datei export/CC_AnimUpload_*.rbxmx gefunden. Bitte zuerst in Studio speichern (siehe Anleitung).'); process.exit(1); }
const idsFile = path.join(__dirname, 'roblox', 'CC_AnimIds.luau');
const uploaded = new Set(fs.existsSync(idsFile) ? [...fs.readFileSync(idsFile, 'utf8').matchAll(/\["([^"]+)"\]\s*=\s*\d+/g)].map(m => m[1]) : []);
let made = 0, kept = 0;
for (const b of bundles) {
  const xml = fs.readFileSync(path.join(EXP, b), 'utf8');
  const re = /<Item class="([^"]+)"[^>]*>|<\/Item>/g;
  let depth = 0, start = -1, m;
  while ((m = re.exec(xml))) {
    if (m[1]) {
      depth++;
      if (m[1] === 'KeyframeSequence' && start < 0) start = m.index;
    } else {
      depth--;
      if (start >= 0) {
        const chunk = xml.slice(start, re.lastIndex);
        const opens = (chunk.match(/<Item /g) || []).length, closes = (chunk.match(/<\/Item>/g) || []).length;
        if (opens === closes) {
          const name = (chunk.match(/<string name="Name">([^<]+)<\/string>/) || [])[1];
          if (name) {
            const file = path.join(OUT, name + '.rbxmx');
            // Schon hochgeladene (ID vorhanden) nie anfassen; noch nicht hochgeladene durch den aktuellen Studio-Stand ersetzen
            if (uploaded.has(name)) kept++;
            else { fs.writeFileSync(file, HEAD + chunk + '</roblox>'); made++; }
          }
          start = -1;
        }
      }
    }
  }
}
console.log(`Aufgeteilt: ${made} neue Animationsdateien, ${kept} schon hochgeladen (unveraendert).`);
