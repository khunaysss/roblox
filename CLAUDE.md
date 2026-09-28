# Regeln für Claude in diesem Projekt

- Der Nutzer kann nicht programmieren. Antworte auf **Deutsch** und erkläre einfach.
- Das Spiel ist in **PLAN.md** beschrieben. Halte dich genau daran.
- **Baue nichts, was nicht im Plan steht.** Wenn etwas unklar ist, frag zuerst nach.
- Arbeite **Phase für Phase** (siehe PLAN.md, Abschnitt 10). Nach jeder Phase kurz zeigen, was gebaut wurde,
  und auf das OK warten, bevor die nächste Phase anfängt.
- Alles selbst aus Parts bauen, **keine Toolbox-Modelle**.
- Wird im Plan etwas geändert, PLAN.md aktualisieren.

## Fertige Bau-Skripte
- `src/build/Phase1_Map.lua`: baut Phase 1 (Map-Grundgerüst). Den Inhalt mit `run_code` in Studio ausführen,
  danach prüfen und Fehler beheben. Das Skript löscht vorher `workspace.StealACar_Map` und baut sie neu.
