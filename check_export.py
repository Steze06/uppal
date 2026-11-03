"""
Check export_uppaal.py:
1. round trip: every exported template has the same locations, initial location and edges as the Python objects
2. the original model exported again matches fichier_f_ref.xml
3. verifyta (if installed) agrees with the Python model on every query
"""
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from check import XML_FILE, clean, compare, edges_from_xml, locations_from_xml
from export_uppaal import build_document, export_xml, expected_state, file_name, layered_layout, line_layout, write_xml
from functions import F_FUNCTIONS, G_FUNCTIONS
from path8 import build_path8
from paths_fg import PATHS, build_path
from product import build_product
from prop1 import build_prop1
from prop2 import build_prop2
from prop2_fg import build_prop2_fg
from witness import find_trace

VERIFYTA = "uppaal-5.0.0-linux64/bin/verifyta"


def templates_by_name(root):
	return {template.findtext("name"): template for template in root.findall("template")}


def ids_are_unique(root):
	ids = [element.get("id") for element in root.iter() if element.get("id")]
	return len(ids) == len(set(ids))


def restore_ids(template, id_map):
	"""Rename the XML ids back to the Python ids so check.py can compare them."""
	back = {xml_id: python_id for python_id, xml_id in id_map.items()}
	for location in template.findall("location"):
		location.set("id", back[location.get("id")])
	template.find("init").set("ref", back[template.find("init").get("ref")])
	for transition in template.findall("transition"):
		for end in ("source", "target"):
			transition.find(end).set("ref", back[transition.find(end).get("ref")])


def check_round_trip(function_names, filename):
	id_maps = export_xml(function_names, filename)
	root = ET.parse(filename).getroot()
	templates = templates_by_name(root)
	expected = {
		"prop1": build_prop1(),
		"prop2": build_prop2_fg(F_FUNCTIONS, G_FUNCTIONS),
		"path": build_path(function_names)[0],
	}
	ok = ids_are_unique(root)
	print(f"{filename}: ids unique across the document -> {'yes' if ok else 'NO'}")
	for name, initial in expected.items():
		restore_ids(templates[name], id_maps[name])
		ok = compare(f"  {name}", templates[name], initial) and ok
	return ok


def check_original(filename):
	reference = ET.parse(XML_FILE).getroot()
	reference_queries = [(query.findtext("formula"), "") for query in reference.iter("query")]
	path8_start, _ = build_path8()
	templates = [
		("prop1", build_prop1(), layered_layout),
		("prop2", build_prop2(), layered_layout),
		("path8", path8_start, line_layout),
	]
	root, id_maps = build_document(templates, {"f": (6, 7)}, {"g": 8}, reference_queries)
	write_xml(root, filename)
	exported = ET.parse(filename).getroot()

	checks = [
		("declarations", clean(exported.findtext("declaration")) == clean(reference.findtext("declaration"))),
		("system line", clean(exported.findtext("system")) == clean(reference.findtext("system"))),
		("query formulas", [q.findtext("formula") for q in exported.iter("query")] == [f for f, _ in reference_queries]),
	]
	exported_templates = templates_by_name(exported)
	for name, template in templates_by_name(reference).items():
		restore_ids(exported_templates[name], id_maps[name])
		mine = exported_templates[name]
		checks.append((f"{name} locations", locations_from_xml(mine) == locations_from_xml(template)))
		checks.append((f"{name} initial location", mine.find("init").get("ref") == template.find("init").get("ref")))
		checks.append((f"{name} edges", edges_from_xml(mine) == edges_from_xml(template)))
	for label, ok in checks:
		print(f"  {label}: {'MATCH' if ok else 'DIFFERENT'}")
	return all(ok for _, ok in checks)


def python_answers(function_names):
	"""What the Python model says for the 3 exported queries, in the same order."""
	path_start, _ = build_path(function_names)
	receivers = [build_prop1(), build_prop2_fg(F_FUNCTIONS, G_FUNCTIONS)]
	reaches = find_trace(path_start, receivers, ("ok", expected_state(function_names))) is not None
	_, states = build_product(build_path(function_names)[0], [build_prop1(), build_prop2_fg(F_FUNCTIONS, G_FUNCTIONS)])
	no_deadlock = all(state.transitions for state in states)
	error = any(state.locations[1].name == "Error" for state in states)
	return [reaches, no_deadlock, error]


def verifyta_answers(filename):
	result = subprocess.run([VERIFYTA, "-q", filename], capture_output=True, text=True)
	answers = []
	for line in result.stdout.splitlines():
		if "Formula is satisfied" in line:
			answers.append(True)
		elif "Formula is NOT satisfied" in line:
			answers.append(False)
	return answers, result


def check_queries(function_names, filename):
	expected = python_answers(function_names)
	words = lambda answers: ", ".join("satisfied" if a else "NOT satisfied" for a in answers)
	print(f"{filename}")
	print(f"  python:   {words(expected)}")
	if not os.path.exists(VERIFYTA):
		return True
	answers, result = verifyta_answers(filename)
	if result.returncode != 0 or len(answers) != len(expected):
		print(f"  verifyta failed (exit {result.returncode}):\n{result.stdout}{result.stderr}")
		return False
	print(f"  verifyta: {words(answers)} -> {'MATCH' if answers == expected else 'DIFFERENT'}")
	return answers == expected


def main():
	results = []
	with tempfile.TemporaryDirectory() as folder:
		print("=== 1. Round trip: exported XML vs Python objects ===")
		for _, function_names, _ in PATHS:
			results.append(check_round_trip(function_names, os.path.join(folder, file_name(function_names))))
		print()

		print("=== 2. Original model (path8, prop1, prop2, n = 1, m = 1) vs fichier_f_ref.xml ===")
		results.append(check_original(os.path.join(folder, "export_original.xml")))
		print()

		print("=== 3. Queries: E<>( prop1.ok && prop2.<state>), A[] not deadlock, E<> prop1.Error ===")
		if not os.path.exists(VERIFYTA):
			print(f"verifyta NOT FOUND at {VERIFYTA}: UPPAAL was not run, only the Python answers are shown.")
		for _, function_names, _ in PATHS:
			results.append(check_queries(function_names, os.path.join(folder, file_name(function_names))))
	print()
	print("All checks passed." if all(results) else "Some checks FAILED.")


if __name__ == "__main__":
	main()
