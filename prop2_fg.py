from automaton import Node, Transition, print_transitions
from functions import F_FUNCTIONS, G_FUNCTIONS, inverse_name


def pending_states(f_functions):
	for function, (action, inverse_action) in f_functions.items():
		yield function, function, action, inverse_action
		yield function, inverse_name(function), inverse_action, action


def f_edges(f_functions, g_functions):
	pending = list(pending_states(f_functions))
	for function, name, repeat_action, cancel_action in pending:
		yield "invariant", repeat_action, name
		yield "g", repeat_action, f"g_{name}"
		yield name, cancel_action, "invariant"
		yield f"g_{name}", cancel_action, "g"
		for source in (name, f"g_{name}"):
			yield source, repeat_action, f"unmanaged_{name}_twice"
			for other_function, other_name, other_action, _ in pending:
				if other_function != function:
					yield source, other_action, f"unmanaged_{name}_{other_name}"
		for g_action in g_functions.values():
			yield name, g_action, f"unmanaged_{name}_g"
			yield f"g_{name}", g_action, "at_least_2_g"


def g_edges(g_functions):
	for g_action in g_functions.values():
		yield "invariant", g_action, "g"
		yield "g", g_action, "at_least_2_g"


def build_prop2_fg(f_functions, g_functions):
	locations = {}

	def location(name):
		if name not in locations:
			locations[name] = Node(f"l{len(locations)}", name)
		return locations[name]

	initial = location("")
	initial.add_transition(Transition(target=location("invariant"), sync="next_state?"))
	for source, action, target in [*f_edges(f_functions, g_functions), *g_edges(g_functions)]:
		location(source).add_transition(Transition(
			target=location(target),
			guard=f"action == {action}",
			sync="next_state?",
		))

	return initial


if __name__ == "__main__":
	print_transitions(build_prop2_fg(F_FUNCTIONS, G_FUNCTIONS))
