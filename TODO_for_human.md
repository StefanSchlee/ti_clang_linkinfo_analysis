- license on pypi missing
- screenshots in readme
- in github-profile einfügen
- glob filter für path grouping?

  - Total size by-memory und by-inputfile passt nicht zusammen wegen sysmem -> make hint

  - Umrechung in KB in icicle unpraktikabel -> passt nicht mit anderen plots zusammen

  - Dokumentieren, welcher linkerflags nötig sind (tested for compiler V4)

    - --gen_xml_func_hash

    - –-xml_link_info

    Suche in dependency graph
    In dependency: use parent folder as default-option to group (show full path maybe)
    In dependency: maybe filters what to exclude from grouping

- Semantic FeatureGroups
  - linking between groups similar to input files: aggregate input file links
  - with path filters
  - with manually filters?
  - with AI-assisted filtering
    - muss größere Modelle Probieren

- Präsentation
  - Teil 1: Tool
    - Motivation: Speicher wird knapp
    - Bisherige Analysen
      - Incrementelle Analyse per Pull-Request und Total size plot
      - Sections Pie Chart
      - Manuelle Analyse der größten Brocken im CCS Memory Plot
    - Welche zusätzlichen Informationen in der Linkinfo
      - Inputfile (object file)
      - referenced symbols
    - Neue Analysen
      - Tables
      - Icicle
      - Graph
  - Teil 2: Agentenbasierte programmierung
    - Was sind Coding Agenten (Building blocks ums LLM)
    - Chat-Frontend: Chatting mit Context
    - advanced developement flow
      - requirements
      - agents.md
      - agents tasklist
      - video of developement: 10 min
        - extended graph view with folder grouping
        - cost: 1% of 10€ -> 10 cent
        - mit recherche und unit tests hätte ich locker 2-3 Tage gebraucht
    - There is more
      - background agents
      - cloud agents
      - subagents
    - Anbieter & costs
    - Dica+Kilo mit Copilot vergleichen
      - Intelligence scores (wie bei Anfangszeiten smartphone, diese Unterschiede entscheiden stark was geht)
      - Beispiel?
    - summary:
      - tool in einem Tag statt 2 Wochen
      - minimal costs in € ~1€ (+1 Tag mich)
      - better test coverage & documentation