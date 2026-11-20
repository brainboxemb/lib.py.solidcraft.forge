# Central CI chat handoff

Copy the text block below into a new chat when continuing the Forge/CAD-CI work.

This is a bootstrap message only. The live GitHub state and each repository's
`docs/plan.md` are authoritative.

~~~text
Je werkt verder aan de centrale CI-structuur rond Forge.

Belangrijk: gebruik dit bericht alleen als bootstrap. Inspecteer vóór iedere
wijziging eerst de actuele GitHub-toestand. Issues, PR's, branches en plannen
kunnen sinds dit bericht veranderd zijn.

Belangrijkste repositories:

- `lib.py.solidcraft.forge` — Forge consumer en modeldefinities
- `lib.py.cad.ci` — generieke CAD-CI-logica
- `tool.cad.ci` — dunne CLI en reusable GitHub Actions workflows
- `tool.cad.ci.test` — externe black-box test van released CAD-CI
- `lib.py.cad.verification` — generieke CAD/model-verificatie
- `tool.py.lib.ci` — generieke CI voor gewone Python-libraries
- `tool.py.lib.ci.test` — externe test daarvan

Repositorygrenzen:

- Generieke CAD-CI-selectie, SCons-uitvoering, dependency-output, evidence,
  durable build output en Pages/publication horen in `lib.py.cad.ci`.
- `tool.cad.ci` blijft dun en exposeert alleen de released library via CLI en
  reusable workflows.
- `tool.cad.ci.test` test alleen de exact released tool/library-stack van
  buitenaf.
- Generieke CAD-verificatiemechanics en SolidCraft-verificatie-adapters horen in
  `lib.py.cad.verification`.
- Forge bezit Forge-compilatie, modellen en model-specifieke expectation data,
  maar geen generieke CAD-CI- of verificatielogica.
- `tool.py.lib.ci` en `tool.py.lib.ci.test` blijven volledig CAD-neutraal.

Voor iedere actieve repository moeten minimaal actueel zijn:

- `AGENTS.md` — werkafspraken en repositorygrenzen
- `docs/plan.md` — huidige source of truth voor onafgemaakt werk
- `docs/requirements.md` — stabiele eisen
- `docs/design.md` — ontwerp/verantwoordelijkheden waar relevant

Werkproces bij iedere wijziging:

1. Lees eerst actuele issues, PR's, branches, `AGENTS.md` en `docs/plan.md`.
2. Gebruik deze handoff nooit als vervanging van die live inspectie.
3. Maak een issue als de wijziging nog geen issue heeft.
4. Update `docs/plan.md` vóór implementatie.
5. Beoordeel daarin alle open issues opnieuw als `now`, `next`, `later`,
   `blocked`, `probably obsolete` of
   `effectively complete but still open`.
6. Update requirements/design als gedrag of architectuur verandert.
7. Daarna pas code.
8. Eén logische wijziging = één issue, branch en PR.
9. Na merge/release het plan opnieuw actualiseren.
10. Ontstaat tijdens Forge-werk een generiek CAD-CI- of verificatieprobleem,
    stop dan en los/test/release dat eerst op in de eigenaar-repository. Maak
    geen Forge-lokale workaround.

Actuele Forge-snapshot bij het schrijven van deze handoff
(20 november 2026):

- Forge issue #472 ("Make model verification depend only on the Forge package
  build") is geïmplementeerd in PR #475.
- PR #475 was op deze snapshot open, mergeable en de Forge-workflow was groen.
  Controleer dit opnieuw voordat je merge of vervolgwerk doet.
- #475 splitst de package-flow in:
  `forge-package` -> onafhankelijk `forge-tests`, `forge-release` en
  modelverificatie.
- De Forge-wheel wordt eenmaal gebouwd; consumers gebruiken de exacte
  dependency-output. Er is hiervoor geen nieuwe generieke CAD-CI-feature nodig.
- De staged modelproof gebruikt precies vijf actieve modelverificaties:
  `simple-box`, `anchor-topology-mutation`, `attach-angle`,
  `four-corner-l` en `xz-anchor`.
- Na #472 is de hoofdrichting:
  #432 declaratieve verification verder afmaken ->
  #430/#378 simple-box visual/verification-stage proof ->
  #366 durable build/Pages publication.
- Meet na #472 eerst de vijf-model runtime voordat je een nieuw
  performance-ontwerp maakt. Herhaalde Docker/SolidCraft-startup kan een
  aparte issue worden, maar alleen op basis van gemeten timing.
- In `lib.py.cad.verification` bestaan #44 en #45 voor partial parameter- en
  sketch-expectations. Voeg geen Forge workaround toe als een volgend model
  die semantics nodig heeft.
- De repository is hernoemd naar de correcte naam
  `lib.py.cad.verification`. Issue #48 in die repository ruimt resterende
  oude `lib.py.cad.verfication`-verwijzingen op. De Python import blijft
  `cad_verification` en de distributienaam blijft
  `brainboxemb-cad-verification-lib`.

Oude handover-volgordes zoals
`lib.py.cad.ci #35 -> tool.cad.ci #47 -> ... -> Forge #424`
zijn inmiddels uitgevoerd/gesloten en mogen niet blind als actuele werkvolgorde
worden hervat.

Start een nieuwe werksessie daarom zo:

1. Inspecteer live alle zeven repositories.
2. Lees per actieve repo `AGENTS.md` en `docs/plan.md`.
3. Controleer open issues, open PR's en branches.
4. Controleer eerst de actuele status van Forge PR #475/#472.
5. Bepaal daarna vanuit de actuele plannen de eerstvolgende wijziging.
6. Werk zelfstandig verder volgens issue -> plan -> requirements/design indien
   nodig -> code -> tests -> PR -> merge/release -> plan-update.
~~~
