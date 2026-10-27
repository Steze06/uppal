"""Run any sequence of functions through prop1 and the extended prop2.

Usage:
    python3 run_path.py f1 inv_f1 g2
    python3 run_path.py f2 g1
"""
import sys

from functions import F_FUNCTIONS, G_FUNCTIONS, action_codes
from paths_fg import build_path
from product import holds
from prop1 import build_prop1
from prop2_fg import build_prop2_fg
from witness import find_trace, print_trace


def explain(state):
	if state == "invariant":
		return "every f was undone and no g was applied: the data is back to its original form"
	if state == "g":
		return "exactly one g was applied and every f was undone: allowed"
	if state == "at_least_2_g":
		return "two or more g functions were applied (final state)"
	if state.startswith("unmanaged_"):
		return "an unmanaged sequence: prop2 is stuck here (final state)"
	if state.startswith("g_"):
		return f"one g was applied, then {state[2:]} was left applied (not undone)"
	return f"{state} was applied and never undone"


def final_prop2_state(prop2, actions):
	"""Follow prop2 alone over the sequence of action values it sees."""
	node = prop2
	for action in actions:
		enabled = [t.target for t in node.transitions if holds(t.guard, {"action": action})]
		if enabled:
			node = enabled[0]
	return node.name


def main():
	codes = action_codes(F_FUNCTIONS, G_FUNCTIONS)
	names = sys.argv[1:]
	unknown = [name for name in names if name not in codes]
	if not names or unknown:
		if unknown:
			print(f"Unknown function(s): {', '.join(unknown)}")
		print(f"Usage: python3 run_path.py <functions...>   available: {', '.join(sorted(codes, key=codes.get))}")
		sys.exit(1)

	prop2 = build_prop2_fg(F_FUNCTIONS, G_FUNCTIONS)
	# prop2 sees: the initial value 0, the creation (1), each function, then the read (3)
	target = final_prop2_state(prop2, [0, 1, *(codes[name] for name in names), 3])

	print(f"=== Path: {' -> '.join(names)} ===")
	print("Action codes: " + ", ".join(f"{name}={codes[name]}" for name in names))
	print(f"E<>( prop1.ok && prop2.{target})")
	print()

	path_start, _ = build_path(names)
	trace = find_trace(path_start, [build_prop1(), prop2], ("ok", target))
	if trace is None:
		print("NOT satisfied: no reachable state matches.")
		return
	print_trace(*trace)
	print()
	print(f"Result: prop1 = ok, prop2 = {target}")
	print(f"Meaning: {explain(target)}")


if __name__ == "__main__":
	main()