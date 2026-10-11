// Cage Champions – Animationen in die Gruppe ANIMEXGANG hochladen (Roblox Open Cloud, Assets API).
// Quelle: export/anim_rbxmx/*.rbxmx (aus Studio geschrieben, eine KeyframeSequence pro Datei).
// Ergebnis: roblox/CC_AnimIds.luau  ({ [Name] = Asset-ID }), wird nach jedem Upload gespeichert -> erneuter Start macht weiter.
//
// Aufruf (PowerShell, im Ordner mma_arena_design):
//   $env:CC_ROBLOX_API_KEY = "<dein API-Schluessel>"; node upload_animations_v01.js
// Der Schluessel wird nur aus der Umgebungsvariable gelesen und nirgends gespeichert oder ausgegeben.
// Optional: node upload_animations_v01.js --test   (laedt nur eine Animation hoch)
const fs = require('fs'), path = require('path');
const GROUP_ID = '7160158';
const DIR = path.join(__dirname, 'export', 'anim_rbxmx');
const OUT = path.join(__dirname, 'roblox', 'CC_AnimIds.luau');
const KEY = process.env.CC_ROBLOX_API_KEY;
const TEST = process.argv.includes('--test');
if (!KEY) { console.error('Fehlt: Umgebungsvariable CC_ROBLOX_API_KEY (siehe Kopf der Datei).'); process.exit(1); }
const sleep = ms => new Promise(r => setTimeout(r, ms));

function loadIds() {
  if (!fs.existsSync(OUT)) return {};
  const ids = {};
  for (const m of fs.readFileSync(OUT, 'utf8').matchAll(/\["([\w]+)"\]\s*=\s*(\d+)/g)) ids[m[1]] = m[2];
  return ids;
}
function saveIds(ids) {
  const names = Object.keys(ids).sort();
  const lines = names.map(n => `\t["${n}"] = ${ids[n]},`);
  fs.writeFileSync(OUT, '-- Asset-IDs der hochgeladenen Animationen (Gruppe ANIMEXGANG 7160158), erzeugt von upload_animations_v01.js.\n'
    + '-- In Studio als ServerStorage.CC_Animations.CC_AnimIds (ModuleScript) einsetzen.\nreturn {\n' + lines.join('\n') + '\n}\n');
}
async function api(url, opts, tries = 6) {
  for (let i = 0; i < tries; i++) {
    const r = await fetch(url, { ...opts, headers: { ...(opts.headers || {}), 'x-api-key': KEY } });
    if (r.status === 429 || r.status >= 500) { const w = 15000 * (i + 1); console.log(`  Server ${r.status}, warte ${w / 1000}s`); await sleep(w); continue; }
    const text = await r.text();
    let body; try { body = JSON.parse(text); } catch { body = { raw: text }; }
    if (!r.ok) throw new Error(`${r.status} ${JSON.stringify(body).slice(0, 300)}`);
    return body;
  }
  throw new Error('zu viele Wiederholungen');
}
async function upload(name, file) {
  const form = new FormData();
  form.append('request', JSON.stringify({
    assetType: 'Animation', displayName: 'CC_' + name, description: 'Cage Champions Animation ' + name,
    creationContext: { creator: { groupId: GROUP_ID } },
  }));
  form.append('fileContent', new Blob([fs.readFileSync(file)], { type: 'model/x-rbxm' }), name + '.rbxmx');
  const op = await api('https://apis.roblox.com/assets/v1/assets', { method: 'POST', body: form });
  const opPath = op.path || ('operations/' + op.operationId);
  for (let i = 0; i < 60; i++) {
    const res = op.done ? op : await api('https://apis.roblox.com/assets/v1/' + opPath, { method: 'GET' });
    if (res.done) {
      if (res.response && res.response.assetId) return String(res.response.assetId);
      throw new Error('Upload abgelehnt: ' + JSON.stringify(res).slice(0, 300));
    }
    await sleep(2000);
  }
  throw new Error('keine Antwort nach 2 Minuten');
}
(async () => {
  const ids = loadIds();
  const files = fs.readdirSync(DIR).filter(f => f.endsWith('.rbxmx')).sort();
  const todo = files.filter(f => !ids[path.basename(f, '.rbxmx')]);
  console.log(`${files.length} Animationen, ${files.length - todo.length} schon hochgeladen, ${todo.length} offen.`);
  let ok = 0, fail = 0;
  for (const f of (TEST ? todo.slice(0, 1) : todo)) {
    const name = path.basename(f, '.rbxmx');
    try {
      const id = await upload(name, path.join(DIR, f));
      ids[name] = id; saveIds(ids); ok++;
      console.log(`OK   ${name} -> ${id}`);
    } catch (e) {
      fail++; console.log(`FEHLER ${name}: ${e.message}`);
      if (/401|403/.test(e.message)) { console.log('Schluessel ungueltig oder ohne Rechte – Abbruch.'); break; }
    }
    await sleep(1500);
  }
  console.log(`Fertig: ${ok} hochgeladen, ${fail} Fehler. IDs in roblox/CC_AnimIds.luau`);
})();
