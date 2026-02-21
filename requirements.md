# Req-1: Project Structure
1. The package should be installable with pip
2. It should support local installs, editable installs (pip install -e), as well as later i want to publish it on pypi
3. I want a pytoml style project

# Req-2: Publicly API Frontend
1. I want one central class, which gets constructed with a path to an linkinfo.xml file.
2. All different analysis should be accessible via methods on this class

# Req-3: Software Architecture Guidelines
1. Do not create one big class, split the logic into internal classes, functions etc. where reasonable
2. At the base i want some kind of parser class, which only parses the linkinfo files into python objects, which then can be used by all further analysis
3. Create a reasonanable project folder structure

# Req-4: Unit-tests
1. I want pytest-based tests for the package, using the example linkinfo.xml files in the "example_files/" folder
2. Keep the tests up-to-date
3. I want a code coverage report

# Req-5: Analysis with markdown output
Hint: This feature is already partly implemented in the "linkinfo_parser.py"
1. This set of analysis outputs the linker data in a structured, hierarchical markdown file
2. On each hierachical level, i generally want to sort the items in descending byte size
3. Each item should show its accumulated byte size
4. This analysis should be one analysis function, which can be configured with arguments, which hierarchical levels should be added:
   1. One style is already implemented by "LinkInfoParser.export_sorted_input_files_markdown()": The top-level are the input files, the next level are the object components belonging to this file
   2. Another style i want is already implemented by "LinkInfoParser.export_memory_areas_hierarchy_markdown()": Above the Input-files there are the logical groups and the memory areas

# Req-6: Folder Grouping of input files
1. Using the "path" from the input-files, we can hierachically group the input files along the original source-files folder structure
2. This Information will be used by different analysis

# Req-7: Icicle Plot Analysis
1. I want an icicle plot using the plotly package
2. The Graph should group after the input files folder structure, then the input files, and then the object-components as the leaf
3. If a folder has only one subfolder, it can be grouped together to form one icicle section
4. The size of each section is based on the byte size of the respective folder (accumulated subfolders/inputfiles), input-file, object-component
5. I want the plot to be vertically: The highest level should be at the bottom.

# Req-8: Graph-based Analysis
1. Using networkx and pyvis.network packages we can do graph visualisations
2. The nodes may be some sort of the hierarchical groups: object-components, input-files, input-file folders, logical groups, memory areas
3. The edges between the nodes originate from the "refd_ro_sections" and "refd_rw_sections" of the object components. 
4. The edges between higher hierachical levels are deducted by all links between the underlying object components
5. For example, "linkinfo_graph" already makes a graph visualisation on the input-file level
6. Similar to the markdown analysis, i want one api-function which can be customized using arguments
7. The base graph is drawn on the input-file level
8. The size of the nodes is based on the byte size of the respective group
9. I want to optionally supply a list of folders, which are additionally added as nodes.
   1. All input-files which belong to one of these folders, are removed as nodes and added to these folder nodes
   2. The folder nodes size are equal to the sum of the input files belonging to
   3. The edges between the folder nodes and other folder/inputfile-nodes should also be found by analysing all links of the underlying input files