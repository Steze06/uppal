from collections import deque

from automaton import describe
from product import INITIAL_VARS, apply_update, holds
from path8 import build_path8
from prop1 import build_prop1
from prop2 import build_prop2

QUERIES = [
	("E<>( prop1.ok && prop2.f)", ("ok", "f")),
	("E<>( prop1.ok && prop2.g)", ("ok", "g")),
	("E<>( prop1.ok && prop2.at_least_2_g)", ("ok", "at_least_2_g"))
]


def receiver_choices(receivers, variables):
	choices = [()]
	for node in receivers:
		enabled = [t.target for t in node.transitions if holds(t.guard, variables)]
		choices = [choice + (target,) for choice in choices for target in (enabled or [node])]
	return choices


def successors(state):
	sender, receivers, variables = state
	variables = dict(variables)
	for edge in sender.transitions:
		updated_variables = tuple(sorted(apply_update(edge.update, variables).items()))
		for receiver_targets in receiver_choices(receivers, variables):
			yield edge, (edge.target, receiver_targets, updated_variables)


def is_target(state, target_names):
	_, receivers, _ = state
	return tuple(node.name for node in receivers) == target_names


def rebuild_trace(state, parents):
	steps = []
	while parents[state] is not None:
		previous, edge = parents[state]
		steps.append((edge, state))
		state = previous
	steps.reverse()
	return state, steps


def find_trace(sender, receivers, target_names):
	start = (sender, tuple(receivers), tuple(sorted(INITIAL_VARS.items())))
	parents = {start: None}
	queue = deque([start])
	while queue:
		state = queue.popleft()
		if is_target(state, target_names):
			return rebuild_trace(state, parents)
		for edge, successor in successors(state):
			if successor not in parents:
				parents[successor] = (state, edge)
				queue.append(successor)
	return None


def describe_state(state):
	sender, receivers, variables = state
	locations = " ".join(describe(node) for node in (sender, *receivers))
	values = " ".join(f"{name}={value}" for name, value in variables)
	return f"{locations} | {values}"


def print_trace(start, steps):
	print(f"0. {describe_state(start)}")
	previous = start
	for number, (edge, state) in enumerate(steps, start=1):
		print(f"   {describe(previous[0])} --[{edge.sync} {edge.update}]--> {describe(edge.target)}")
		print(f"{number}. {describe_state(state)}")
		previous = state


def main():
	path8_start, _ = build_path8()
	receivers = [build_prop1(), build_prop2()]
	for formula, target_names in QUERIES:
		print(f"=== {formula} ===")
		trace = find_trace(path8_start, receivers, target_names)
		if trace is None:
			print("NOT satisfied: no reachable state matches.")
		else:
			print_trace(*trace)
		print()


if __name__ == "__main__":
	main()
