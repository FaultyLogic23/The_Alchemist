"""
triples_to_rdf.py reads items_triples.csv,
where each row is already a triple (subject, predicate, object),
and turns it into RDF.
"""

import csv
import os
from rdflib import Graph, Namespace, URIRef, Literal

# Setting up namespaces

ALCH = Namespace("https://w3id.org/alchemist/ontology#")

PREFIXES = {
    "alch": "https://w3id.org/alchemist/ontology#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "schema": "https://schema.org/",
    "dcterms": "http://purl.org/dc/terms/",
    "marcrel": "http://id.loc.gov/vocabulary/relators/",
    "wd": "http://www.wikidata.org/entity/",
}


# Helper functions

def expand(term):
    ''''schema:name' -> URIRef('https://schema.org/name'); full URLs stay as they are.'''
    if term.startswith("http"):
        return URIRef(term)
    prefix, local = term.split(":", 1)
    return URIRef(PREFIXES[prefix] + local)

'''
This function builds the object of the triple according to the 
object_type column.
'''

def make_object(row):
    if row["object_type"] == "local":       # an entity of this project
        return ALCH[row["object"]]
    if row["object_type"] == "uri":         # a class or an external resource
        return expand(row["object"])
    # literal: with a datatype, with a language, or plain
    if row["datatype"]:
        return Literal(row["object"], datatype=expand(row["datatype"]))
    if row["language"]:
        return Literal(row["object"], lang=row["language"])
    return Literal(row["object"])


def new_graph():
    g = Graph()
    for prefix, ns in PREFIXES.items():
        g.bind(prefix, ns)
    return g


# Core of the script

with open("items_triples.csv", encoding="utf-8") as f:
    rows = [{k: v.strip() for k, v in r.items()} for r in csv.DictReader(f)]

# 1. The general dataset: every row becomes a triple

all_items = new_graph()
for row in rows:
    all_items.add((ALCH[row["subject"]], expand(row["predicate"]), make_object(row)))

all_items.serialize("items.ttl", format="turtle")
'''
2. One dataset for each item: the item's triples plus the triples 
of the agents it points to (so each file is self-contained).
'''
items = expand("schema:CreativeWork")
os.makedirs("items_rdf", exist_ok=True)

for item in all_items.subjects(expand("rdf:type"), items):
    single = new_graph()
    for p, o in all_items.predicate_objects(item):
        single.add((item, p, o))
        # if the object is a person/organisation, copy its description too
        if (o, expand("rdf:type"), items) not in all_items:
            for p2, o2 in all_items.predicate_objects(o):
                single.add((o, p2, o2))
    local_name = item.split("#")[-1]
    single.serialize(f"items_rdf/{local_name}.ttl", format="turtle")

print(f"Done: {len(rows)} rows, {len(all_items)} triples in items.ttl")
