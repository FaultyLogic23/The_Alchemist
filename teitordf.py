from lxml import etree
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, SKOS

Input_file = "Alchemist.xml"
Output_file = "alchemist-data.ttl"

TEI_ns = {"tei": "http://www.tei-c.org/ns/1.0"}
Wikidata_base = "http://www.wikidata.org/entity"

alch = Namespace("https://w3id.org/alchemist/ontology#")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
schema = Namespace("https://schema.org/")
dcterms = Namespace("http://purl.org/dc/terms/")
rel = Namespace("http://purl.org/vocab/relationship/")

# Helper function

def choose_typedate(value):

    if not value:
        return None
    v = value.strip()
    if len(v) == 4:
        return XSD.gYear
    if len(v) == 7:
        return XSD.gYearMonth
    if len(v) == 10:
        return XSD.date
    return None

def add_wikidata_link(entity_uri, element):
    for idno in element.findall("tei:idno", namespaces=TEI_ns):
        idno_type = (idno.get("type") or "").lower()
        if idno_type == "wikidata" and idno.text:
            value = idno.text.strip()
            wd_uri = URIRef(value if value.startswith("http") else Wikidata_base+value)
            g.add((entity_uri, RDFS.seeAlso, wd_uri))

def resolve_entity(ref):
    ref = ref.strip()
    if ref.startswith("http"):
        return URIRef(ref)
    return alch[ref.lstrip("#")]

def process_entity(list_xpath, item_tag, rdf_class, label_tag, label_prop=RDFS.label, extra=None):
    items = root.findall(f"{list_xpath}/tei:{item_tag}", namespaces=TEI_ns)
    print(f"Found {len(items)} {item_tag}.")
    for item in items:
        xml_id = item.get("{http://www.w3.org/XML/1998/namespace}id")
        if not xml_id:
            continue
        uri = alch[xml_id]
        g.add((uri, RDF.type, rdf_class))
        label_el = item.find(f"tei:{label_tag}", namespaces=TEI_ns)
        if label_el is not None and label_el.text:
            g.add((uri, label_prop, Literal(label_el.text.strip(), lang="eng")))
        add_wikidata_link(uri, item)
        if extra:
            extra(uri, item)

def extraperson(uri, element):

    for tag, prop in [("birth", schema.birthDate), ("death", schema.deathDate)]:
        el = element.find(f"tei:{tag}", namespaces=TEI_ns)
        if el is not None:
            when = el.get("when")
            dtype = choose_typedate(when)
            if dtype:
                g.add((uri, prop, Literal(when.strip(), datatype=dtype)))

def extraevent(uri, element):
    for attr, prop in [("when", schema.startDate), ("from", schema.startDate), ("to", schema.endDate)]:
        val = element.get(attr)
        dtype = choose_typedate(val)
        if dtype:
            g.add((uri, prop, Literal(val.strip(), datatype=dtype)))


tree = etree.parse(Input_file)
root = tree.getroot()

g= Graph()
g.bind("alch", alch)
g.bind("foaf", foaf)
g.bind("schema", schema)
g.bind("dcterms", dcterms)
g.bind("rel", rel)
g.bind("skos", SKOS)

process_entity(".//tei:listPerson", "person", foaf.Person, "persName", foaf.name, extraperson)
process_entity(".//tei:listOrg",    "org",    schema.Organization, "orgName")
process_entity(".//tei:listPlace",  "place",  schema.Place, "placeName")
process_entity(".//tei:listBibl",   "bibl",   schema.CreativeWork, "title")
process_entity(".//tei:list[@type='concept']", "item", SKOS.Concept, "term", SKOS.prefLabel)
process_entity(".//tei:listEvent",  "event",  schema.Event, "label", extra=extraevent)

relation_map = {
    "author": dcterms.creator,
    "characterIn": schema.character,
    "loves": rel["hasRomanticRelationshipWith"],
    "mentor": rel.mentorOf,
    "imprintOf": schema.parentOrganization,
    "adaptationOf": schema.isBasedOn,
    "adapter": schema.contributor,
    "illustrator": schema.illustrator,
    "inspiredBy": schema.isBasedOn,
    "filmRightsHolder": dcterms.rightsHolder,
    "basedOn": schema.isBasedOn,
}

inverted = {"characterIn", "imprintOf"}

symmetricrel = {"loves"}

relations = root.findall(".//tei:listRelation/tei:relation", namespaces=TEI_ns)
print(f"Found {len(relations)} relations.")

for relation in relations:
    name = relation.get("name")
    if name not in relation_map:
        print(f"Relation '{name}' not mapped")
        continue
    predicate = relation_map[name]

    mutual = relation.get("mutual")
    if mutual:
        refs = mutual.split()
        for i, a in enumerate(refs):
            for b in refs[i+1:]:
                a_uri, b_uri = resolve_entity(a), resolve_entity(b)
                g.add((a_uri, predicate, b_uri))
                g.add((b_uri, predicate, a_uri))
        continue

    active = relation.get("active")
    passive = relation.get("passive")
    if not active or not passive:
        continue

    for a in active.split():
        for p in passive.split():
            a_uri, p_uri = resolve_entity(a), resolve_entity(p)
            if name in inverted:
                g.add((p_uri, predicate, a_uri))
            else:
                g.add((a_uri, predicate, p_uri))

g.serialize(destination=Output_file, format="turtle")
print(f"Graph saved in {Output_file}. Total triples: {len(g)}")