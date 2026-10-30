# The Alchemist – a LODLAM project

Linked Open Data project on *The Alchemist* by Paulo Coelho, built from its English Wikipedia
article. The article is encoded in XML/TEI, its entities are reconciled with external
authorities (Wikidata, VIAF, WorldCat, NDL), and the encoding is transformed into an
annotated HTML page and an RDF dataset described by a reuse-only ontology.

**Website:** https://faultylogic23.github.io/The_Alchemist/

Project for the course *Information Science and Cultural Heritage*, Prof. Francesca Tomasi
and Prof. Marilena Daquino, DHDK, University of Bologna, a.y. 2025/2026.

## Contents

| File | Description |
|---|---|
| `Alchemist.xml` | TEI encoding of the Wikipedia article |
| `tei_to_html.py` | XML/TEI → HTML transformation |
| `tei_to_rdf.py` | XML/TEI → RDF transformation, produces `alchemist-data.ttl` |
| `alchemist-ontology.ttl` | Ontology (application profile built by using Protégé) |
| `items_triples.csv`, `triples_to_rdf.py` | Extra dataset of the works, produces `items.ttl` |
| `visualize_rdf.py` | Draws the RDF datasets as SVG graphs |
| `Theoretical Model/`, `Conceptual Model/` | Models drawn in yEd with the Graffoo palette |

## How to run

Requirements: Python 3, `lxml`, `rdflib`, and Graphviz for the visualisation.

    pip install lxml rdflib
    python3 tei_to_html.py
    python3 tei_to_rdf.py
    python3 triples_to_rdf.py
    python3 visualize_rdf.py

## License

The source text is the Wikipedia article *The Alchemist (novel)*, released under
CC BY-SA 4.0; the data and the encoding are released under the same license.

## Author

Samuele Bertelli
