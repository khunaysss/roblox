# Aufgaben für ChatGPT 6.1 (Stand 2026-10-20)

Alle Blender-Modelle und Animationen sind fertig (siehe unten). Was fehlt, ist Roblox-Einbau, Logik und Texte.
Jeder Block unten ist ein fertiger Auftrag: kompletten Block kopieren, an ChatGPT schicken, Antwort-Block zurück an Claude.

## Was schon da ist (nicht neu bauen)

| Teil | Wo |
|---|---|
| Animationen Walkout, Sieg, Niederlage, Ringarzt | `export/anim_rbxmx/Fighter_Walkout.rbxmx`, `Fighter_Celebrate`, `Fighter_Dejected`, `Doc_Check` (in Studio: `ServerStorage.CC_Animations`, noch nicht hochgeladen) |
| Gürtel-Modelle | `export/Fighter_Belts_v01.fbx` (Titelgürtel 4 Teile, Stoffgürtel 2 Teile), Setup `roblox/setup_belts_v01.luau` |
| Ringrichter | `ServerScriptService.CC_Referee` (fertig, getestet) |
| Ecken-Pause | `CC_Corner.server`, `CC_CornerView.client` (fertig, getestet) |
| Kampf-Ablauf | `ServerScriptService.CC_Match` (States: walkout, intro, fight, break, finisher, over; Attribute Winner, Stoppage, Corner) |

---

## Auftrag 1 – Upload der 4 neuen Animationen (du selbst, 1 Minute)

Doppelklick auf `mma_arena_design/upload_starten.bat`, Schlüssel einfügen, `j`. Danach an Claude oder ChatGPT: „hochgeladen“.

---

## Auftrag 2 – Walkout, Siegerjubel, Verlierer (Roblox-Einbau)

```
Du arbeitest im Roblox-Studio-MCP am Spiel "Cage Champions" (Place CageChampions). Antworte am Ende NUR mit einem Code-Block im Format unten.

REGELN
- Vor jedem Test: workspace-Attribut CC_TestProfileKey = "chatgpt_test1", CC_TestNewPlayer = nil. Danach: CC_TestProfileKey = nil, CC_TestNewPlayer = true. Echtes Profil nie verändern.
- Vor jeder Skriptänderung: Kopie des alten Skripts nach ServerStorage.CC_Backup_<Datum> legen.
- Animationen: ServerStorage.CC_Animations.<Name> (KeyframeSequence) oder ID aus ServerStorage.CC_Animations.CC_AnimIds. Laden wie in ServerScriptService.CC_Referee (Funktion animFor).

AUFGABE
1. Walkout: In ServerScriptService.CC_Match gibt es State "walkout" (nur Fight Night). Während die Kämpfer zum Käfig laufen, auf beiden Charakteren die Animation "Fighter_Walkout" (Schleife, Priorität Action) abspielen, beim State "intro" stoppen.
2. Sieg: Bei State "over" spielt der Sieger nach der Arm-Hochhalten-Pose (CC_Referee, Animation Fighter_WinRaise) die Animation "Fighter_Celebrate" einmal ab (Priorität Action4).
3. Niederlage: Der Verlierer spielt bei State "over" "Fighter_Dejected" (Schleife, Action4), Stopp sobald CC_MatchId am Charakter leer ist.
4. Alle Tracks müssen stoppen, wenn der Spieler den Kampf verlässt (Attribut CC_MatchId wird leer). Sonst bleibt die Pose im Gym hängen.
5. Test mit einem Trainingskampf: Server: game.ServerStorage.CC_MenuServer:Fire(player, "training"); K.o. erzwingen: workspace.CC_TrainingDummy:SetAttribute("CC_KO", true). Prüfen: Sieger jubelt, Gegner (Dummy) hängt die Schultern, nach Rückkehr ins Gym keine Pose mehr aktiv.

ANTWORT-FORMAT (genau so, ein Code-Block):
AUFTRAG: 2
GEAENDERT: <Skriptnamen>
BACKUP: <Pfad>
TEST: <OK | FEHLER | NICHT GETESTET> je Punkt 1-5, eine Zeile pro Punkt
FEHLER: <Konsole oder "keine">
NEUER_CODE: <vollständiger Code jedes geänderten oder neuen Skripts>
```

---

## Auftrag 3 – Ringarzt (Logik + Einbau)

```
Du arbeitest im Roblox-Studio-MCP am Spiel "Cage Champions". Antworte am Ende NUR mit einem Code-Block im Format unten.

REGELN: wie Auftrag 2 (Test-Profil, Backup vor Änderung, keine echten Daten).

AUFGABE
1. In ServerScriptService.CC_Match gibt es doctorWinner(m) und den Abbruch-Text "Doctor stoppage" (Attribut Stoppage). Erkläre zuerst in der Antwort, wann doctorWinner auslöst (Code lesen).
2. Ringarzt-Figur: Kopie von ServerStorage.CC_Referee, Name "Doctor", Hemd/Jacke weiß einfärben (MeshParts mit "Polo"/"Shirt" im Namen weiß, Rest unverändert).
3. Wenn Stoppage == "Doctor stoppage": Arzt erscheint am Käfigrand, geht zum verletzten Kämpfer (Verlierer), stellt sich 0,62 m vor ihn (Blick zu ihm), spielt "Doc_Check" (96 Frames, 4 s). Danach verschwindet er.
4. Test-Weg einbauen: Workspace-Attribut CC_TestDoctor = true → beim nächsten Kampf nach 5 s Arztabbruch auslösen (nur in Studio, RunService:IsStudio()).
5. Testen und Ergebnis melden.

ANTWORT-FORMAT: wie Auftrag 2, AUFTRAG: 3, zusätzlich Zeile AUSLOESER: <Erklärung aus Punkt 1>.
```

---

## Auftrag 4 – Gürtel ins Spiel

```
Du arbeitest im Roblox-Studio-MCP am Spiel "Cage Champions". Antworte am Ende NUR mit einem Code-Block im Format unten.

REGELN: wie Auftrag 2.

VORAUSSETZUNG: Der Nutzer hat export/Fighter_Belts_v01.fbx importiert (Import 3D, Rig Custom, Centimeter) und das Skript roblox/setup_belts_v01.luau im Edit-Modus ausgeführt → ServerStorage.CC_Belts mit Teilen Belt_Title_Band, Belt_Title_Plate, Belt_Title_Trim, Belt_Title_Gem, Belt_Cloth_Band, Belt_Cloth_Tip, je mit Attribut CC_C0. Wenn ServerStorage.CC_Belts fehlt: NUR das melden und aufhören.

AUFGABE
1. ModuleScript ReplicatedStorage.CC_BeltShared: Titelgürtel-Stufen an die Karriere-Siege (Attribut CC_CareerWins am Spieler): 2 = Amateur Champion (Platte Silber 170,174,182), 4 = Pro (Gold 212,168,56), 7 = Top Contender (Gold + Steine sichtbar), 10 = Lightweight Champion (Gold 232,190,70 + Steine). Unter 2 Siegen: kein Gürtel.
2. Gürtel am Kämpfer anbringen wie die Kleidung (siehe ReplicatedStorage.CC_LookShared, Funktion apply: Teil klonen, Motor6D Part0 = HumanoidRootPart, C0 = Attribut CC_C0). Stein-Teil (Belt_Title_Gem) nur ab Stufe 7.
3. Sichtbar: im Gym und beim Walkout. Im Kampf ab State "fight" ausblenden (Transparency 1), nach "over" wieder einblenden.
4. Auf der Mittelplatte (Belt_Title_Plate) eine SurfaceGui (Face Front) mit Text "CAGE CHAMPIONS" (Schrift GothamBlack, schwarz, klein).
5. Stoffgürtel (Belt_Cloth_*) noch NICHT verwenden (Freischaltung offen).
6. Test: Profil-Attribut CC_CareerWins im Test auf 0, 2, 7, 10 setzen und Screenshots machen.

ANTWORT-FORMAT: wie Auftrag 2, AUFTRAG: 4.
```

---

## Auftrag 5 – Texte (ohne Studio)

```
Antworte NUR mit einem Code-Block (Luau-Tabelle), nichts davor oder danach.

Schreibe für das Roblox-MMA-Spiel "Cage Champions" englische Ansagen, je Kategorie 6 Varianten, max. 8 Wörter, keine echten Personen oder Marken, keine Beleidigungen:
walkout, fightStart, knockdown, ko, submission, doctor, decision, winner, cornerAdvice.

Format:
return {
	walkout = { "…", … },
	...
}
```

---

## Was Claude später noch braucht (nicht ChatGPT)

- Prüfen der ChatGPT-Antworten (Code-Review), wenn Credits wieder da sind.
- Weitere Blender-Arbeit nur, wenn neue Modelle gewünscht sind.
