"""
Export prop1, the extended prop2 and a path to a UPPAAL XML file in the exports folder.

Usage:
    python3 export_uppaal.py f1 inv_f1 g2    (writes exports/export_f1_inv_f1_g2.xml)
    python3 export_uppaal.py                 (writes one file per path in PATHS)
"""
import os
import sys
import xml.etree.ElementTree as ET
from collections import deque
from itertools import count
from math import hypot

from check import XML_FILE, locations_from_xml
from functions import F_FUNCTIONS, G_FUNCTIONS, action_codes
from paths_fg import PATHS, build_path
from prop1 import build_prop1
from prop2_fg import build_prop2_fg
from run_path import final_prop2_state

EXPORT_FOLDER = "exports"
DOCTYPE = "<!DOCTYPE nta PUBLIC '-//Uppaal Team//DTD Flat System 1.6//EN' 'http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd'>"

DECLARATION = """
/* broadcast channel between automata */
broadcast chan next_state;
 /* global variables */
//action type
//0: undefined, 1: creation, 2: transition
//3: read, 4:undeterministic write, 5: store,
//6 to 6+(2n-1): f and f^{{-1}} inversibles functions
//6+2n to 6+2n+m-1 : g deterministic write functions
const int n = {n};
const int m = {m};
int[0,{action_max}] action = 0;

//integrity request requirement
bool integ_r = false;
 //integrity control request requirement
 bool integ_cr = false;
//enclave protected
bool p = false;
//enclave with signature service offered
bool s = false;

"""

LAYER_GAP = 300
ROW_GAP = 80
STEP_GAP = 300
LABEL_KINDS = [("guard", "guard"), ("synchronisation", "sync"), ("assignment", "update")]


def action_max(f_functions, g_functions):
	"""Upper bound of the action range: the original expression if it covers every code, else the largest code."""
	largest = max(5, *action_codes(f_functions, g_functions).values())
	if largest <= 6 + 2 * len(f_functions) + len(g_functions):
		return "6+2*n+m"
	return str(largest)


def declaration(f_functions, g_functions):
	return DECLARATION.format(n=len(f_functions), m=len(g_functions), action_max=action_max(f_functions, g_functions))


def bfs_order(initial):
	depths = {initial.id: 0}
	order = [initial]
	queue = deque([initial])
	while queue:
		node = queue.popleft()
		for transition in node.transitions:
			if transition.target.id not in depths:
				depths[transition.target.id] = depths[node.id] + 1
				order.append(transition.target)
				queue.append(transition.target)
	return order, depths


def layered_layout(initial):
	order, depths = bfs_order(initial)
	layers = {}
	for node in order:
		layers.setdefault(depths[node.id], []).append(node)
	positions = {}
	for depth, nodes in layers.items():
		for index, node in enumerate(nodes):
			positions[node.id] = (depth * LAYER_GAP, round((index - (len(nodes) - 1) / 2) * ROW_GAP))
	return positions


def line_layout(initial):
	order, _ = bfs_order(initial)
	return {node.id: (index * STEP_GAP, 0) for index, node in enumerate(order)}


def reference_template(name, nodes):
	"""The template with this name in the original XML, if its locations are exactly these nodes."""
	try:
		root = ET.parse(XML_FILE).getroot()
	except (OSError, ET.ParseError):
		return None
	for template in root.findall("template"):
		if template.findtext("name") == name:
			if locations_from_xml(template) == {node.id: node.name for node in nodes}:
				return template
	return None


def edge_geometry(source, target, positions, has_reverse):
	(x1, y1), (x2, y2) = positions[source.id], positions[target.id]
	if source is target:
		nails = [(x1 + 60, y1 - 30), (x1 + 60, y1 + 30)]
	elif x1 == x2:
		# same column: bend sideways so the edge doesn't run through the locations in between
		side = -1 if has_reverse and y2 < y1 else 1
		nails = [(x1 + side * (60 + abs(y2 - y1) // 4), (y1 + y2) // 2)]
	elif has_reverse:
		# two edges between the same locations: bend each one to its own side
		length = hypot(x2 - x1, y2 - y1)
		nails = [(round((x1 + x2) / 2 - 25 * (y2 - y1) / length), round((y1 + y2) / 2 + 25 * (x2 - x1) / length))]
	else:
		nails = []
	anchor = nails[0] if nails else ((x1 + x2) // 2, (y1 + y2) // 2)
	return nails, anchor


def add_location(parent, xml_id, node, x, y, name_xy):
	location = ET.SubElement(parent, "location", id=xml_id, x=str(x), y=str(y))
	if node.name:
		name = ET.SubElement(location, "name", x=str(name_xy[0]), y=str(name_xy[1]))
		name.text = node.name


def add_transition(parent, xml_id, source_id, target_id, labels, nails):
	transition = ET.SubElement(parent, "transition", id=xml_id)
	ET.SubElement(transition, "source", ref=source_id)
	ET.SubElement(transition, "target", ref=target_id)
	for kind, text, (x, y) in labels:
		label = ET.SubElement(transition, "label", kind=kind, x=str(x), y=str(y))
		label.text = text
	for x, y in nails:
		ET.SubElement(transition, "nail", x=str(x), y=str(y))


def reference_locations(reference):
	result = {}
	for location in reference.findall("location"):
		name = location.find("name")
		name_xy = (int(name.get("x")), int(name.get("y"))) if name is not None else None
		result[location.get("id")] = (int(location.get("x")), int(location.get("y")), name_xy)
	return result


def reference_edges(reference):
	result = {}
	for transition in reference.findall("transition"):
		key = (transition.find("source").get("ref"), transition.find("target").get("ref"))
		labels = {label.get("kind"): (int(label.get("x")), int(label.get("y"))) for label in transition.findall("label")}
		nails = [(int(nail.get("x")), int(nail.get("y"))) for nail in transition.findall("nail")]
		result[key] = (labels, nails)
	return result


def computed_labels(transition, anchor, above):
	texts = [(kind, getattr(transition, attribute)) for kind, attribute in LABEL_KINDS if getattr(transition, attribute)]
	top = anchor[1] - 5 - 17 * len(texts) if above else anchor[1] + 5
	return [(kind, text, (anchor[0] - 40, top + 17 * index)) for index, (kind, text) in enumerate(texts)]


def template_element(parent, name, initial, layout, new_id):
	"""Add one <template> and return the map from Python ids to XML ids."""
	nodes, _ = bfs_order(initial)
	ids = {node.id: new_id() for node in nodes}
	reference = reference_template(name, nodes)
	ref_locations = reference_locations(reference) if reference is not None else {}
	ref_edges = reference_edges(reference) if reference is not None else {}
	positions = layout(initial) if reference is None else {id: xy[:2] for id, xy in ref_locations.items()}

	template = ET.SubElement(parent, "template")
	ET.SubElement(template, "name").text = name
	for node in nodes:
		x, y = positions[node.id]
		name_xy = ref_locations[node.id][2] if node.id in ref_locations else (x - 10, y - 30)
		add_location(template, ids[node.id], node, x, y, name_xy)
	ET.SubElement(template, "init", ref=ids[initial.id])

	pairs = {(node.id, t.target.id) for node in nodes for t in node.transitions}
	edges = [(node, t) for node in nodes for t in node.transitions]
	for index, (node, transition) in enumerate(edges):
		target = transition.target
		nails, anchor = edge_geometry(node, target, positions, (target.id, node.id) in pairs)
		labels = computed_labels(transition, anchor, above=index % 2 == 1)
		if (node.id, target.id) in ref_edges:
			ref_labels, nails = ref_edges[(node.id, target.id)]
			labels = [(kind, text, ref_labels.get(kind, xy)) for kind, text, xy in labels]
		add_transition(template, new_id(), ids[node.id], ids[target.id], labels, nails)
	return ids


def build_document(templates, f_functions, g_functions, queries):
	"""templates: [(name, initial node, layout)], queries: [(formula, comment)]. Returns the root and the id maps."""
	root = ET.Element("nta")
	ET.SubElement(root, "declaration").text = declaration(f_functions, g_functions)
	counter = count()
	new_id = lambda: f"id{next(counter)}"
	id_maps = {name: template_element(root, name, initial, layout, new_id) for name, initial, layout in templates}
	ET.SubElement(root, "system").text = f"\nsystem {', '.join(name for name, _, _ in templates)};\n"
	queries_element = ET.SubElement(root, "queries")
	for formula, comment in queries:
		query = ET.SubElement(queries_element, "query")
		ET.SubElement(query, "formula").text = formula
		ET.SubElement(query, "comment").text = comment
	return root, id_maps


def write_xml(root, filename):
	ET.indent(root, space="\t")
	with open(filename, "w", encoding="utf-8") as file:
		file.write('<?xml version="1.0" encoding="utf-8"?>\n')
		file.write(DOCTYPE + "\n")
		file.write(ET.tostring(root, encoding="unicode") + "\n")


def expected_state(function_names):
	"""The prop2 state from PATHS, or computed the same way run_path.py does it."""
	for _, names, target in PATHS:
		if names == list(function_names):
			return target
	codes = action_codes(F_FUNCTIONS, G_FUNCTIONS)
	prop2 = build_prop2_fg(F_FUNCTIONS, G_FUNCTIONS)
	return final_prop2_state(prop2, [0, 1, *(codes[name] for name in function_names), 3])


def queries(prop2_state):
	return [
		(f"E<>( prop1.ok && prop2.{prop2_state})", f"prop1 reaches ok while prop2 is in {prop2_state} (expected: satisfied)"),
		("A[] not deadlock", "the path loops forever in end, so the system never deadlocks (expected: satisfied)"),
		("E<> prop1.Error", "the path always starts on a protected enclave, so prop1 never reaches Error (expected: not satisfied)"),
	]


def export_xml(function_names, filename):
	templates = [
		("prop1", build_prop1(), layered_layout),
		("prop2", build_prop2_fg(F_FUNCTIONS, G_FUNCTIONS), layered_layout),
		("path", build_path(function_names)[0], line_layout),
	]
	root, id_maps = build_document(templates, F_FUNCTIONS, G_FUNCTIONS, queries(expected_state(function_names)))
	write_xml(root, filename)
	return id_maps


def file_name(function_names):
	return f"export_{'_'.join(function_names)}.xml"


def main():
	codes = action_codes(F_FUNCTIONS, G_FUNCTIONS)
	names = sys.argv[1:]
	unknown = [name for name in names if name not in codes]
	if unknown:
		print(f"Unknown function(s): {', '.join(unknown)}")
		print(f"Usage: python3 export_uppaal.py [functions...]   available: {', '.join(sorted(codes, key=codes.get))}")
		sys.exit(1)

	os.makedirs(EXPORT_FOLDER, exist_ok=True)
	for function_names in [names] if names else [names for _, names, _ in PATHS]:
		filename = os.path.join(EXPORT_FOLDER, file_name(function_names))
		export_xml(function_names, filename)
		print(f"{filename}: {' -> '.join(function_names)}, E<>( prop1.ok && prop2.{expected_state(function_names)})")


if __name__ == "__main__":
	main()
