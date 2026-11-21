# Central CI chat handoff

Copy the text block below into a new chat when continuing the Forge/CAD-CI work.

~~~text
Je werkt verder aan de centrale CI-structuur rond Forge.

Belangrijkste repositories:

- `lib.py.solidcraft.forge` — Forge consumer en modeldefinities
- `lib.py.cad.ci` — generieke CAD-CI-logica
- `tool.cad.ci` — dunne CLI/reusable workflows
- `tool.cad.ci.test` — externe test van released CAD-CI
- `lib.py.cad.verification` — generieke CAD-verificatie
- `docker.cad.solidcraft` — immutable SolidCraft runtime/container
- `tool.py.lib.ci` — generieke Python-library CI
- `tool.py.lib.ci.test` — externe test daarvan

Gebruik deze handoff alleen als ingang. Bepaal de actuele werkzaamheden altijd
uit GitHub en de repositoryplannen.

Voor iedere actieve repo:

1. Lees eerst actuele issues, PR's en branches.
2. Lees `AGENTS.md` en `docs/plan.md`.
3. Behandel `docs/plan.md` als source of truth voor onafgemaakt werk.
4. Maak een issue als de wijziging nog geen issue heeft.
5. Update `docs/plan.md` vóór implementatie en beoordeel alle open issues
   opnieuw als `now`, `next`, `later`, `blocked`,
   `probably obsolete` of `effectively complete but still open`.
6. Update `docs/requirements.md` en `docs/design.md` als gedrag of
   architectuur verandert.
7. Daarna pas code.
8. Eén logische wijziging = één issue, branch en PR.
9. Na merge/release het plan opnieuw actualiseren.

Werk niet onnodig serieel:

- `dev-cad` en `dev-ci` zijn onafhankelijke werkstromen en mogen parallel
  vooruitgaan;
- wacht alleen op een workflow als de volgende stap werkelijk van die uitslag
  afhangt;
- werk ondertussen door in de andere lane wanneer daar onafhankelijk werk ligt;
- gedeelde dependency-releases, eigenaar-repository handoffs en promoties naar
  `main` blijven echte synchronisatiepunten;
- repositorybrede governance die beide lanes gelijk raakt mag via een
  kortlevende branch rechtstreeks naar `main`;
- zulke direct-main governance PR's worden **squash-merged**;
- alleen `promote/dev-cad` / `promote/dev-ci` naar `main` gebruiken een
  normale merge commit.

Repositorygrenzen:

- Generieke CAD-CI-logica hoort in `lib.py.cad.ci`.
- `tool.cad.ci` blijft dun; externe acceptatie hoort in `tool.cad.ci.test`.
- Generieke CAD/model-verificatie hoort in `lib.py.cad.verification`.
- De SolidCraft runtime, dependency-pins en containerrelease horen in
  `docker.cad.solidcraft`; consumers gebruiken alleen een immutable image tag.
- Forge bezit Forge-compilatie, modellen en model-specifieke verwachtingen,
  maar geen generieke CI-, verificatie- of runtime-packaginglogica.
- Gewone Python-library CI hoort in `tool.py.lib.ci`; externe acceptatie
  daarvan in `tool.py.lib.ci.test`.

Als Forge een ontbrekende generieke CAD-CI-, verificatie- of runtimefunctie
blootlegt, los die dan eerst op in de eigenaar-repository, test en release die
daar, en pas daarna Forge aan. Maak geen Forge-lokale workaround.

Begin nu met `lib.py.solidcraft.forge`: inspecteer de actuele toestand en lees
`AGENTS.md` en `docs/plan.md`. Volg daarna de actuele werkvolgorde uit het
plan en de relevante plannen van de andere repositories.
~~~
