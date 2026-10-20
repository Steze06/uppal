import xml.etree.ElementTree as ET
from collections import deque

from automaton import Node
from path8 import build_path8
from prop1 import build_prop1
from prop2 import build_prop2

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


# --- simulation of the system "prop1, prop2, path8" -------------------------

INITIAL_VARS = {"action": 0, "integ_r": False, "integ_cr": False, "p": False, "s": False}


def holds(guard, variables):
	if not guard:
		return True
	return eval(guard, {"true": True, "false": False}, dict(variables))


def apply_update(update, variables):
	variables = dict(variables)
	for assignment in filter(None, update.split(",")):
		var, value = (part.strip() for part in assignment.split("="))
		variables[var] = {"true": True, "false": False}.get(value, None)
		if variables[var] is None:
			variables[var] = int(value)
	return variables


def reachable_states(sender, receivers):
	"""Every edge of the sender broadcasts next_state!; each receiver takes one
	enabled next_state? edge (guards read the values before the update) or stays."""
	start = (sender, tuple(receivers), tuple(sorted(INITIAL_VARS.items())))
	seen = {start}
	queue = deque([start])
	while queue:
		sender_node, receiver_nodes, variables = queue.popleft()
		variables = dict(variables)
		for edge in sender_node.transitions:
			choices = [[]]
			for node in receiver_nodes:
				enabled = [t.target for t in node.transitions if holds(t.guard, variables)]
				choices = [c + [target] for c in choices for target in (enabled or [node])]
			new_vars = tuple(sorted(apply_update(edge.update, variables).items()))
			for choice in choices:
				state = (edge.target, tuple(choice), new_vars)
				if state not in seen:
					seen.add(state)
					queue.append(state)
	return seen


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
	print("=== 2. Queries from the XML, checked by simulating the Python models ===")
	states = reachable_states(path8_start, [prop1_start, prop2_start])
	print(f"{len(states)} reachable states")
	queries = [
		("E<>( prop1.ok && prop2.f)", "ok", "f"),
		("E<>( prop1.ok && prop2.g)", "ok", "g"),
	]
	for formula, prop1_name, prop2_name in queries:
		satisfied = any(r[0].name == prop1_name and r[1].name == prop2_name for _, r, _ in states)
		print(f"{formula}: {'satisfied' if satisfied else 'NOT satisfied'}")


if __name__ == "__main__":
	main()
