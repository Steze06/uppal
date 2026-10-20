from collections import deque

from automaton import Node, Transition, print_transitions
from path8 import build_path8
from prop1 import build_prop1
from prop2 import build_prop2

# initial values from the global declarations of the XML
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


def state_name(locations):
	return "(" + ", ".join(describe_location(location) for location in locations) + ")"


def describe_location(node):
	return node.name or node.id


def build_product(sender, receivers):
	"""Product of the sender (next_state!) with the receivers (next_state?).

	A product state is one location per automaton plus the values of the
	global variables. On each edge of the sender, every receiver takes one of
	its enabled edges (guards read the values before the sender's update), or
	stays where it is if none is enabled. The product starts in the initial
	location of every automaton with the initial values of the variables."""
	def key(locations, variables):
		return (tuple(location.id for location in locations), tuple(sorted(variables.items())))

	def get_state(locations, variables):
		k = key(locations, variables)
		if k not in states:
			node = Node(f"s{len(states)}", state_name(locations))
			node.locations = locations
			node.variables = variables
			states[k] = node
			queue.append(node)
		return states[k]

	states = {}
	queue = deque()
	initial = get_state((sender, *receivers), dict(INITIAL_VARS))

	while queue:
		state = queue.popleft()
		sender_node, *receiver_nodes = state.locations
		for edge in sender_node.transitions:
			choices = [[]]
			for node in receiver_nodes:
				enabled = [t for t in node.transitions if holds(t.guard, state.variables)]
				choices = [c + [t] for c in choices for t in (enabled or [None])]
			new_vars = apply_update(edge.update, state.variables)
			for choice in choices:
				targets = [t.target if t else node for t, node in zip(choice, receiver_nodes)]
				guard = " and ".join(f"({t.guard})" for t in choice if t and t.guard)
				target = get_state((edge.target, *targets), new_vars)
				state.add_transition(Transition(target, guard=guard, sync="next_state", update=edge.update))

	return initial, list(states.values())


def build_system():
	path8_start, _ = build_path8()
	return build_product(path8_start, [build_prop1(), build_prop2()])


if __name__ == "__main__":
	initial, states = build_system()
	print("Product of path8 x prop1 x prop2  (state = (path8, prop1, prop2))")
	print(f"Initial state: {initial.id} = {initial.name}  with {initial.variables}")
	print(f"{len(states)} states, {sum(len(s.transitions) for s in states)} transitions")
	print()
	print("States:")
	for state in states:
		print(f"  {state.id} = {state.name}  {state.variables}")
	print()
	print("Transitions:")
	print_transitions(initial)
