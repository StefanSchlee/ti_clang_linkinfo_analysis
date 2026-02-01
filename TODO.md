- Graph View of inputfiles
  - use NetworkX package 
  - Nodesize should represent size
  - Node should have labels: Name+Size
  - directed edges between inputfiles(nodes) should be added, if any component from one inputfile references (by refd_ro_sections or refd_rw_sections) any component from another input file
  - it should be possible by clicking/hovering an edge to check from which subcomponents the edges are originated

- Table view with Regions + Sections
  - Top Level: Memory Regions
  - Next Level: Memory Sections
  - Next Level: Input Files
  - Next Level: Components

- Semantic subGroups
  - with manually filters?

- Präsentation
  - Bisherige Analysen
    - Incrementelle Analyse per Pull-Request und Total size plot
    - Sections Pie Chart
    - Manuelle Analyse der größten Brocken im CCS Memory Plot
  - Welche zusätzlichen Informationen in der Linkinfo
    - Inputfile (object file)
    - referenced symbols
  - Neue Analysen
    - Tables
    - Graph