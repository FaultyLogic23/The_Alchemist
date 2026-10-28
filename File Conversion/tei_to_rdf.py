from lxml import etree
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, SKOS

Input_file = "TheAlchemist.xml"
Output_file = "alchemist-data.ttl"

TEI_ns = {"tei": "http://www.tei-c.org/ns/1.0"}
Wikidata_base = "http://www.wikidata.org/entity/"

alch = Namespace("https://w3id.org/alchemist/ontology#")
dbo = Namespace("http://dbpedia.org/ontology/")
marcrel = Namespace("http://id.loc.gov/vocabulary/relators/")
schema = Namespace("https://schema.org/")
dcterms = Namespace("http://purl.org/dc/terms/")
rel = Namespace("http://purl.org/vocab/relationship/")

# Helper function
'''
The first function choose the right XSD for a date based on its length, some examples:
1988 (4 characters) -> xsd:gYear
1988-04 (7 characters) -> xsd:gYearMonth
1988-04-12 (10 characters) -> xsd:date
'''
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

'''
The function "add_authority_links" read <idno> inside a TEI entity and add a rdfs:seeAlso which
points to the extral resource.
'''

def add_authority_links(entity_uri, element):
    for idno in element.findall("tei:idno", namespaces=TEI_ns):
        if not idno.text:
            continue
        value = idno.text.strip()
        idno_type = (idno.get("type") or "").lower()
        if value.startswith("http"):
            g.add((entity_uri, RDFS.seeAlso, URIRef(value)))
        elif idno_type == "wikidata":
            g.add((entity_uri, RDFS.seeAlso, URIRef(Wikidata_base + value)))

'''
resolve_entity transform a TEI reference to an URI.
'''

def resolve_entity(ref):
    ref = ref.strip()
    if ref.startswith("http"):
        return URIRef(ref)
    return alch[ref.lstrip("#")]

'''
The process_entity function takes the xml:id (if there is not then it is skipped),
creates the URI "alch:id" and assign a class to it with "rdf:type".
Then it search for an element which contains the name (persName, placeName, etc...)
and add it as a label with language tag, "en" in this case.
'''

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
            g.add((uri, label_prop, Literal(label_el.text.strip(), lang="en")))
        add_authority_links(uri, item) # With this one we add external links
        if extra:
            extra(uri, item)


'''
Every "extra" function adds entites dates.

extraperson -> It reads <birth when> and <death when>, it produces schema:birthDate and schema:deathDate
extrabibl -> It reads <date when> and produce schema:datePublished
extraevent -> It reads the attributes "when", "from" and "to", the first two becomes schema:startDate
and the other one schema:endDate. 
'''

def extraperson(uri, element):

    for tag, prop in [("birth", schema.birthDate), ("death", schema.deathDate)]:
        el = element.find(f"tei:{tag}", namespaces=TEI_ns)
        if el is not None:
            when = el.get("when")
            dtype = choose_typedate(when)
            if dtype:
                g.add((uri, prop, Literal(when.strip(), datatype=dtype)))

def extrabibl(uri, element):
    el = element.find("tei:date", namespaces=TEI_ns)
    if el is not None:
        when = el.get("when")
        dtype = choose_typedate(when)
        if dtype:
            g.add((uri, schema.datePublished, Literal(when.strip(), datatype=dtype)))

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
g.bind("dbo", dbo)
g.bind("marcrel", marcrel)
g.bind("schema", schema)
g.bind("dcterms", dcterms)
g.bind("rel", rel)
g.bind("skos", SKOS)

'''
Here we call process_entity one time for every entity.
'''

process_entity(".//tei:listPerson", "person", schema.Person, "persName", schema.name, extraperson)
process_entity(".//tei:listPerson", "personGrp", schema.Person, "name", schema.name)
process_entity(".//tei:listOrg",    "org",    schema.Organization, "orgName", schema.name)
process_entity(".//tei:listPlace",  "place",  schema.Place, "placeName", schema.name)
process_entity(".//tei:listBibl",   "bibl",   schema.CreativeWork, "title", schema.name, extrabibl)
process_entity(".//tei:list[@type='concept']", "item", SKOS.Concept, "term", SKOS.prefLabel)
process_entity(".//tei:listEvent",  "event",  schema.Event, "label", schema.name, extraevent)

relation_map = {
    "author":             dcterms.creator,
    "about":              schema.about,
    "characterIn":        schema.character,
    "founder":            schema.founder,
    "homeLocation":       schema.homeLocation,
    "loves":              rel.engagedTo,
    "mentor":             rel.mentorOf,
    "imprintOf":          schema.parentOrganization,
    "adaptationOf":       dcterms.isVersionOf,
    "adapter":            marcrel.adp,
    "illustrator":        schema.illustrator,
    "inspiredBy":         schema.isBasedOn,
    "illustratedVersionOf": dcterms.isVersionOf,
    "filmRightsHolder":   dcterms.rightsHolder,
    "basedOn":            schema.isBasedOn,
    "earliestVersionBy":  dcterms.relation,
    "containsVariantOf":  dcterms.isVersionOf,
    "setIn":              schema.contentLocation,
    "language":           dcterms.language,
    "location":           schema.location,
    "subject":            dcterms.subject,
    "performer":          schema.performer,
    "publisher":          dcterms.publisher,
    "producer":           schema.producer,
    "producerOrg":        schema.producer,
    
}

'''
We need to define the relations in which the relation must be inverted.
If we write active = "#coelho", passive="#alchemist" with "name=author" the triple
is correct if we look at the TEI standard but it is not correct in RDF.

The correct triple in RDF would be "works" -> "dcterms:creator" -> "author" and 
it is for this reason that the script invert subject and object.
'''

inverted = {"author", "characterIn", "adapter", "founder", "illustrator",
            "filmRightsHolder", "earliestVersionBy", "producer", "producerOrg", "performer", "publisher"}


'''
For every <relation> in the listRelation we do two things:
1. Mutual relations -> For every pairs of entities we add a triple in both directions
2. Active/Passive relations ->  For every active-passive combination we create a triple and reverse it 
if the name is in "inverted". We manage attributes with much more references.
'''

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

'''
Every entity which appears with "schema:character" is a character of the Novel
so in this part we want to eliminate "schema:Person" (which is needed for real persons)
and assign "dbo:FictionalCharacter" instead.
'''

for character in set(g.objects(None, schema.character)):
    g.remove((character, RDF.type, schema.Person))
    g.add((character, RDF.type, dbo.FictionalCharacter))

g.serialize(destination=Output_file, format="turtle")
print(f"Graph saved in {Output_file}. Total triples: {len(g)}")