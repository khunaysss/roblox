// Erzeugt export/anim_rbxmx/<Name>.rbxmx (KeyframeSequence) direkt aus export/<Name>_vNN_keyframes.luau.
// Gleiche Umrechnung wie CC_Loader in Studio: Blender -> Roblox  CFrame.new(-x, y, -z, -qx, qy, -qz, qw), lineare Easing, Poses nach Bone-Hierarchie.
// Hierarchie und Format stammen aus einer vorhandenen Datei (export/anim_rbxmx/Trainer_Tyson_Idle.rbxmx).
// Aufruf: node make_rbxmx_from_keyframes.js Name=Datei.luau:Loop:Prioritaet ...   (Prioritaet: Idle=0 Movement=1 Action=2 Action4=5)
// Beispiel: node make_rbxmx_from_keyframes.js Ref_Idle=Ref_Idle_v28_keyframes.luau:1:0
// Bestehende Dateien werden nicht ueberschrieben.
const fs = require('fs'), path = require('path');
const ROOT = __dirname, SRC = path.join(ROOT, 'export', 'anim_rbxmx');
const OUT = process.env.RBXMX_OUT || SRC;          // nur fuer Tests: anderer Ausgabeordner
const tpl = fs.readFileSync(path.join(SRC, 'Trainer_Tyson_Idle.rbxmx'), 'utf8');

// Bone-Hierarchie aus der Vorlage (Verschachtelung der Pose-Elemente)
const tree = {}; const stack = [];
for (const m of tpl.matchAll(/<Item class="Pose"[^>]*><Properties><string name="Name">(\w+)<\/string>|<\/Item>/g)) {
  if (m[1]) { const parent = stack.length ? stack[stack.length - 1] : null; tree[m[1]] = parent; stack.push(m[1]); } else stack.pop();
}
const order = Object.keys(tree);                       // Eltern vor Kindern
const children = n => order.filter(k => tree[k] === n);

function parseFrames(file) {
  const src = fs.readFileSync(file, 'utf8');
  const frames = [];
  for (const line of src.split('\n')) {
    const t = line.match(/\{t=([\d.eE+-]+),/); if (!t) continue;
    const poses = {};
    for (const b of line.matchAll(/(\w+)=\{([^}]*)\}/g)) poses[b[1]] = b[2].split(',').map(Number);
    frames.push({ t: Number(t[1]), poses });
  }
  return frames;
}
function cf(v) {                                       // v = {x,y,z,qw,qx,qy,qz} (Blender) -> Roblox-CFrame (Matrix)
  const [x, y, z, qw, qx0, qy0, qz0] = v;
  const X = -x, Y = y, Z = -z, qx = -qx0, qy = qy0, qz = -qz0, qW = qw;
  const r = [
    1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qW), 2 * (qx * qz + qy * qW),
    2 * (qx * qy + qz * qW), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qW),
    2 * (qx * qz - qy * qW), 2 * (qy * qz + qx * qW), 1 - 2 * (qx * qx + qy * qy)];
  return { X, Y, Z, r };
}
const num = n => (Math.abs(n) < 1e-9 ? 0 : Number(n.toFixed(7)));
let ref = 0; const rid = () => 'RBX' + (++ref);
function poseXml(name, fr, w) {
  const v = fr.poses[name];
  const c = v ? cf(v) : { X: 0, Y: 0, Z: 0, r: [1, 0, 0, 0, 1, 0, 0, 0, 1] };
  const kids = children(name).map(k => poseXml(k, fr, 1)).join('');
  return `<Item class="Pose" referent="${rid()}"><Properties><string name="Name">${name}</string><CoordinateFrame name="CFrame"><X>${num(c.X)}</X><Y>${num(c.Y)}</Y><Z>${num(c.Z)}</Z>` +
    ['R00', 'R01', 'R02', 'R10', 'R11', 'R12', 'R20', 'R21', 'R22'].map((k, i) => `<${k}>${num(c.r[i])}</${k}>`).join('') +
    `</CoordinateFrame><token name="EasingDirection">0</token><token name="EasingStyle">0</token><float name="Weight">${w}</float></Properties>${kids}</Item>`;
}
for (const arg of process.argv.slice(2)) {
  const [name, rest] = arg.split('='); const [file, loop, prio] = rest.split(':');
  const out = path.join(OUT, name + '.rbxmx');
  if (fs.existsSync(out)) { console.log('existiert, uebersprungen:', name); continue; }
  const frames = parseFrames(path.join(ROOT, 'export', file));
  if (!frames.length) { console.log('keine Frames:', file); continue; }
  ref = 0;
  let xml = tpl.slice(0, tpl.indexOf('<Item class="KeyframeSequence"'));
  xml += `<Item class="KeyframeSequence" referent="${rid()}"><Properties><string name="Name">${name}</string><bool name="Loop">${loop === '1'}</bool><token name="Priority">${prio}</token><float name="AuthoredHipHeight">2</float></Properties>`;
  for (const fr of frames) xml += `<Item class="Keyframe" referent="${rid()}"><Properties><string name="Name">Keyframe</string><float name="Time">${fr.t}</float></Properties>${poseXml(order[0], fr, 0)}</Item>`;
  xml += '</Item></roblox>\n';
  fs.writeFileSync(out, xml);
  console.log('OK', name, frames.length, 'Frames,', (xml.length / 1024).toFixed(0), 'KB');
}
