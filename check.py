import xml.etree.ElementTree as ET
from path8 import build_path8
from prop1 import build_prop1
from prop2 import build_prop2
from product import build_product

XML_FILE = "fichier_f_ref.xml"


def clean(text):
	return "".join((text or "").split())


def edges_from_xml(template):
	edges = set()
	for t in template.findall("transition"):
		labels = {label.get("kind"): label.text for label in t.findall("label")}
		edges.add((
			t.find("source").get("ref"),
			t.find("target").get("ref"),
			clean(labels.get("guard")),
			clean(labels.get("synchronisation")),
			clean(labels.get("assignment")),
		))
	return edges


def locations_from_xml(template):
	locations = {}
	for loc in template.findall("location"):
		name = loc.find("name")
		locations[loc.get("id")] = name.text if name is not None else ""
	return locations


def all_nodes(initial):
	seen = {}
	to_visit = [initial]
	while to_visit:
		node = to_visit.pop()
		if node.id in seen:
			continue
		seen[node.id] = node
		to_visit.extend(t.target for t in node.transitions)
	return seen


def edges_from_python(nodes):
	edges = set()
	for node in nodes.values():
		for t in node.transitions:
			edges.add((node.id, t.target.id, clean(t.guard), clean(t.sync), clean(t.update)))
	return edges


def compare(name, template, initial):
	nodes = all_nodes(initial)
	xml_locations = locations_from_xml(template)
	python_locations = {id: node.name for id, node in nodes.items()}
	xml_edges = edges_from_xml(template)
	python_edges = edges_from_python(nodes)
	xml_init = template.find("init").get("ref")

	ok = True
	if xml_locations != python_locations:
		ok = False
		print(f"  locations differ: xml={xml_locations} python={python_locations}")
	if xml_init != initial.id:
		ok = False
		print(f"  initial location differs: xml={xml_init} python={initial.id}")
	for edge in xml_edges - python_edges:
		ok = False
		print(f"  missing in python: {edge}")
	for edge in python_edges - xml_edges:
		ok = False
		print(f"  extra in python:   {edge}")

	status = "MATCH" if ok else "DIFFERENT"
	print(f"{name}: {len(python_locations)} locations, {len(python_edges)} edges -> {status}")
	return ok


def main():
	root = ET.parse(XML_FILE).getroot()
	templates = {t.find("name").text: t for t in root.findall("template")}

	path8_start, _ = build_path8()
	prop1_start = build_prop1()
	prop2_start = build_prop2()

	print("=== 1. Python models vs XML templates ===")
	all_match = all([
		compare("path8", templates["path8"], path8_start),
		compare("prop1", templates["prop1"], prop1_start),
		compare("prop2", templates["prop2"], prop2_start),
	])
	print("All templates match the XML." if all_match else "Some templates differ from the XML.")

	print()
	print("=== 2. Queries from the XML, checked on the product automaton ===")
	initial, states = build_product(path8_start, [prop1_start, prop2_start])
	print(f"product: {len(states)} states, initial state {initial.name}")
	queries = [
		("E<>( prop1.ok && prop2.f)", "ok", "f"),
		("E<>( prop1.ok && prop2.g)", "ok", "g"),
	]
	for formula, prop1_name, prop2_name in queries:
		satisfied = any(r[0].name == prop1_name and r[1].name == prop2_name for _, *r in (s.locations for s in states))
		print(f"{formula}: {'satisfied' if satisfied else 'NOT satisfied'}")


if __name__ == "__main__":
	main()
