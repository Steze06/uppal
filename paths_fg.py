from automaton import Node, Transition
from functions import F_FUNCTIONS, G_FUNCTIONS, action_codes
from path8 import walk

START_UPDATE = "action = 1, p = true, s = true, integ_r = true, integ_cr = false"
END_UPDATE = "action = 3, p = true, s = true, integ_r = false, integ_cr = true"

PATHS = [
	("f1 undone by inv_f1, then g2", ["f1", "inv_f1", "g2"], "g"),
	("f1 and f2 each undone, then g1", ["f1", "inv_f1", "f2", "inv_f2", "g1"], "g"),
	("g3, then f2 undone by inv_f2", ["g3", "f2", "inv_f2"], "g"),
	("inv_f2 undone by f2", ["inv_f2", "f2"], "invariant"),
	("f1 left applied", ["f1"], "f1"),
	("two g functions", ["g1", "g3"], "at_least_2_g"),
	("f1 applied twice", ["f1", "f1"], "unmanaged_f1_twice"),
	("f1 then f2", ["f1", "f2"], "unmanaged_f1_f2"),
	("f2 then g1", ["f2", "g1"], "unmanaged_f2_g"),
]


def function_update(action):
	return f"action = {action}, p = false, s = false, integ_r = false, integ_cr = false"


def build_path(function_names):
	codes = action_codes(F_FUNCTIONS, G_FUNCTIONS)
	updates = [START_UPDATE, *(function_update(codes[name]) for name in function_names), END_UPDATE]
	states = [Node(f"id{index}", f"state_{index + 1}") for index in range(len(updates))]
	end = Node(f"id{len(updates)}", "end")

	for state, target, update in zip(states, [*states[1:], end], updates):
		state.add_transition(Transition(target=target, sync="next_state!", update=update))
	end.add_transition(Transition(target=end, sync="next_state!", update=END_UPDATE))

	return states[0], end


if __name__ == "__main__":
	for description, function_names, _ in PATHS:
		print(f"=== {description}: {' -> '.join(function_names)} ===")
		walk(*build_path(function_names))
		print()
