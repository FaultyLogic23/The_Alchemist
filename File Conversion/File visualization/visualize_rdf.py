'''
Visualize_pdf.py draws the RDF datasets as graphs (SVG Images).
'''

import subprocess
from rdflib import Graph
from rdflib.tools.rdf2dot import rdf2dot


def draw(graph, name):

    
    # Writes name.dot from the graph, then draws name.svg with
    # Graphviz.

    # First part is -> RDF to .dot
    

    with open(f"{name}.dot", "w", encoding="utf-8") as f:
        rdf2dot(graph, f)

    
    # Second part is -> .dot to .svg
    

    subprocess.run(["dot", "-Tsvg", f"{name}.dot", "-o", f"{name}.svg"], check=True)

    print(f"{name}.svg: {len(graph)} triples")

'''
Then we define the two datasets, each in its own graph.
'''

tei_graph = Graph().parse("alchemist-data.ttl")
items_graph = Graph().parse("items.ttl")

draw(tei_graph, "alchemist-data")
draw(items_graph, "items")

'''
At the end we merge them for completeness. Parse() can be called
more than once on the same Graph.

Triples present in both files are kept only once, because the URIs 
are the same.
'''

all_graph = Graph()
all_graph.parse("alchemist-data.ttl")
all_graph.parse("items.ttl")

draw(all_graph, "alchemist-all")