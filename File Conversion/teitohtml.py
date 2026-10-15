'''
Some documentation about what this file do. It converts the TEI file "Alchemist.xml" based on the Wikipedia Article
which can be found at https://en.wikipedia.org/wiki/The_Alchemist_(novel).
'''

# First Phase
'''
We define the input and output files, we declare the namespace
and declare the unique xml_id of the document (we need it to link the mentions
in the text with the forms of the entities).
'''

from lxml import etree

input_file = "Alchemist.xml"
output_file = "alchemist.html"
css_file = "stylemed.css"

# Namespaces

tei_ns = "http://www.tei-c.org/ns/1.0"
nsmap = {"tei": tei_ns}
xml_id = "{http://www.w3.org/XML/1998/namespace}id"

'''
Then we load the XML file and analyse by recognizing opening, closing tags
and attributen. After it we build the tree starting by the root, following
the body and so on, respecting the HTML hierarchy.

Then we create an empty dictionary which is going to be filled
with the entities' index.
'''

# Parsing

tree = etree.parse(input_file)
root = tree.getroot()

body = root.find(".//tei:body", namespaces=nsmap)

sections = body.findall("./tei:div", namespaces=nsmap)
print(f"Found {len(sections)} sections in the TEI body.") # Debug

entities = {}

# Second Phase, Entity building

for element in root.iter():
    xml_id = element.get(xml_id)
    if not xml_id:
        continue
    if etree.QName(element).localname not in ("person", "personGrp", "org", "place", "bibl", "item", "event"):
        continue

    label = ""
    for label_tag in ("persName", "orgName", "placeName", "title", "term", "label", "name"):
        found = element.find(f"tei:{label_tag}", namespaces=nsmap)
        if found is not None and found.text:
            label = found.text.strip()
            break

    uri = ""
    for idno in element.findall("tei:idno", namespaces=nsmap):
        if idno.text and idno.text.strip().startswith("http"):
            uri = idno.text.strip()
            break

    entities[xml_id] = {"label": label, "uri": uri}

print(f"Indexed {len(entities)} entities from the back matter.") # Debug

# Mapping TEI tags

entity_map = {
    "persName": "person",
    "orgName": "org",
    "placeName": "place",
    "term": "concept",
    "title": "work",
}

rs_typemap = {
    "person": "person",
    "work": "work",
    "software": "software",
    "award": "award",
}

def transform_entity(element):

    tag_local = etree.QName(element).localname # take the name of the tag without the namespace

    if tag_local == "rs":
        rs_type = element.get("type", "")
        css_class = rs_typemap.get(rs_type, "entity")
    else:
        css_class = entity_map.get(tag_local, "entity")

    ref = element.get("ref", "")
    key = ref.lstrip("#")
    info = entities.get(key)

    if ref.startswith("http"):
        span = etree.Element("a")
        span.set("href", ref)
        span.set("target", "_blank")
    elif info and info["uri"]:
        span = etree.Element("a")
        span.set("href", info["uri"])
        span.set("target", "_blank")
        span.set("title", info["label"])
    else:
        span = etree.Element("span")
        if info:
            span.set("title", info["label"])

    span.set("class", css_class)

    if ref:
        span.set("data-ref", key)

    span.text = element.text or ""

    for child in element:
        child_html = transform_element(child)
        if child_html is not None:
            span.append(child_html)
            if child.tail:
                child_html.tail = child.tail

    return span


# Structure tag

structure_map = {
    "p": "p",
    "quote": "q",
    "cit": "span",
    "bibl": "span",
    "list": "ul",
    "item": "li",
    "head": "h3"
}

def transform_element(element, div_level=0):
    
    tag_local = etree.QName(element).localname

    if tag_local in entity_map or tag_local == "rs":
        return transform_entity(element)

    if tag_local == "div":
        section = etree.Element("section")
        xml_id = element.get(xml_id)
        if xml_id:
            section.set("id", xml_id)
            heading = etree.SubElement(section, "h2" if div_level <= 1 else "h3")
            heading.text = xml_id.replace("-", " ").capitalize()

        for child in element:
            child_html = transform_element(child, div_level + 1)
            if child_html is not None:
                section.append(child_html)
        return section

    if tag_local == "head":
        heading = etree.Element("h2" if div_level <= 1 else "h3")
        heading.text = element.text or ""
        return heading

    if tag_local == "date":
        time_el = etree.Element("time")
        when = element.get("when") or element.get("from")
        if when:
            time_el.set("datetime", when)
        time_el.text = element.text or ""
        return time_el

    if tag_local == "ptr":
        target = element.get("target", "")
        link = etree.Element("a")
        link.set("class", "ptr")
        if target.startswith("http"):
            link.set("href", target)
            link.set("target", "_blank")
            link.text = target
        else:
            key = target.lstrip("#")
            info = entities.get(key)
            link.set("href", "#" + key)
            link.text = "[" + (info["label"] if info else key) + "]"
        return link

    if tag_local in structure_map:
        new_tag = etree.Element(structure_map[tag_local])
        if tag_local in ("cit", "bibl", "quote"):
            new_tag.set("class", tag_local)
        new_tag.text = element.text or ""
        for child in element:
            child_html = transform_element(child, div_level)
            if child_html is not None:
                new_tag.append(child_html)

                if child.tail:
                    child_html.tail = child.tail
        return new_tag

    return None

# HTML creation

html = etree.Element("html", lang="en")

head = etree.SubElement(html, "head")

meta = etree.SubElement(head, "meta")
meta.set("charset", "UTF-8")

viewport = etree.SubElement(head, "meta")
viewport.set("name", "viewport")
viewport.set("content", "width=device-width, initial-scale=1")

title = etree.SubElement(head, "title")
title.text = "The Alchemist, Annotated Wikipedia Article"

link = etree.SubElement(head, "link")
link.set("rel", "stylesheet")
link.set("href", css_file)

body_html = etree.SubElement(html, "body")
main = etree.SubElement(body_html, "main")

h1 = etree.SubElement(main, "h1")
h1.text = "The Alchemist"

for section in body.findall("./tei:div", namespaces=nsmap):
    section_html = transform_element(section, div_level=1)
    if section_html is not None:
        main.append(section_html)


# Serialization

html_string = "<!DOCTYPE html>\n" + etree.tostring(
    html,
    pretty_print=True,
    method="html",
    encoding="unicode"
)

with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_string)

print(f"\nHTML saved in {output_file}.")

# Debug
'''
This last section is used to report the refs
which do not correspond with any entity.
'''

orph = set()
for element in body.iter():
    ref = element.get("ref") or element.get("target")
    if ref and not ref.startswith("http"):
        if ref.lstrip("#") not in entities:
            orph.add(ref)

if orph:
    print("Attention, @ref without correspondence in the back:")
    for r in sorted(orph):
        print("  " + r)
else:
    print("Every @ref of the body resolve on the back.")