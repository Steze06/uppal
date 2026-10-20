from automaton import Node, Transition


def build_path8():
	state_1 = Node("id0", "state_1")
	state_2 = Node("id1", "state_2")
	state_3 = Node("id2", "state_3")
	state_4 = Node("id3", "state_4")
	state_5 = Node("id5", "state_5")
	state_6 = Node("id6", "state_6")
	state_7 = Node("id7", "state_7")
	end = Node("id4", "end")

	state_1.add_transition(Transition(
		target=state_2,
		sync="next_state!",
		update="action = 1, p = true, s = true, integ_r = true, integ_cr = false",
	))
	state_2.add_transition(Transition(
		target=state_3,
		sync="next_state!",
		update="action = 7, p = false, s = false, integ_r = false, integ_cr = false",
	))
	state_3.add_transition(Transition(
		target=state_4,
		sync="next_state!",
		update="action = 6, p = false, s = false, integ_r = false, integ_cr = false",
	))
	state_4.add_transition(Transition(
		target=state_5,
		sync="next_state!",
		update="action = 7, p = false, s = false, integ_r = false, integ_cr = false",
	))
	state_5.add_transition(Transition(
		target=state_6,
		sync="next_state!",
		update="action = 6, p = false, s = false, integ_r = false, integ_cr = false",
	))
	state_6.add_transition(Transition(
		target=state_7,
		sync="next_state!",
		update="action = 8, p = false, s = false, integ_r = false, integ_cr = false",
	))
	state_7.add_transition(Transition(
		target=end,
		sync="next_state!",
		update="action = 3, p = true, s = true, integ_r = false, integ_cr = true",
	))
	end.add_transition(Transition(
		target=end,
		sync="next_state!",
		update="action = 3, p = true, s = true, integ_r = false, integ_cr = true",
	))

	return state_1, end


def walk(start, end):
	node = start
	while node is not end and node.transitions:
		transition = node.transitions[0]
		print(f"{node.name} --[{transition.sync} {transition.update}]--> {transition.target.name}")
		node = transition.target
	print(f"reached {node.name}")


if __name__ == "__main__":
	initial, end = build_path8()
	walk(initial, end)
