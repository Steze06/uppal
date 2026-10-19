from automaton import Node, Transition, print_transitions


def build_prop2():
    initial = Node("id33", "")
    invariant = Node("id34", "invariant")
    inv_f = Node("id35", "inv_f")
    f = Node("id36", "f")
    unmanaged_inv_f2 = Node("id37", "unmanaged_inv_f2")
    unmanaged_f2 = Node("id38", "unmanaged_f2")
    g = Node("id39", "g")
    g_inv_f = Node("id40", "g_inv_f")
    g_f = Node("id41", "g_f")
    at_least_2_g = Node("id42", "at_least_2_g")
    unmanaged_inv_f_g = Node("id43", "unmanaged_inv_f_g")
    unmanaged_f_g = Node("id44", "unmanaged_f_g")

    initial.add_transition(Transition(
        target=invariant,
        sync="next_state?",
    ))

    invariant.add_transition(Transition(
        target=f,
        guard="action == 6",
        sync="next_state?",
    ))
    invariant.add_transition(Transition(
        target=inv_f,
        guard="action == 7",
        sync="next_state?",
    ))
    invariant.add_transition(Transition(
        target=g,
        guard="action == 8",
        sync="next_state?",
    ))

    f.add_transition(Transition(
        target=unmanaged_f2,
        guard="action == 6",
        sync="next_state?",
    ))
    f.add_transition(Transition(
        target=invariant,
        guard="action == 7",
        sync="next_state?",
    ))
    f.add_transition(Transition(
        target=unmanaged_f_g,
        guard="action == 8",
        sync="next_state?",
    ))

    inv_f.add_transition(Transition(
        target=invariant,
        guard="action == 6",
        sync="next_state?",
    ))
    inv_f.add_transition(Transition(
        target=unmanaged_inv_f2,
        guard="action == 7",
        sync="next_state?",
    ))
    inv_f.add_transition(Transition(
        target=unmanaged_inv_f_g,
        guard="action == 8",
        sync="next_state?",
    ))

    g.add_transition(Transition(
        target=g_f,
        guard="action == 6",
        sync="next_state?",
    ))
    g.add_transition(Transition(
        target=g_inv_f,
        guard="action == 7",
        sync="next_state?",
    ))
    g.add_transition(Transition(
        target=at_least_2_g,
        guard="action == 8",
        sync="next_state?",
    ))

    g_f.add_transition(Transition(
        target=g,
        guard="action == 7",
        sync="next_state?",
    ))
    g_f.add_transition(Transition(
        target=unmanaged_f2,
        guard="action == 8",
        sync="next_state?",
    ))
    g_f.add_transition(Transition(
        target=at_least_2_g,
        guard="action == 8",
        sync="next_state?",
    ))

    g_inv_f.add_transition(Transition(
        target=g,
        guard="action == 6",
        sync="next_state?",
    ))
    g_inv_f.add_transition(Transition(
        target=unmanaged_inv_f2,
        guard="action == 7",
        sync="next_state?",
    ))
    g_inv_f.add_transition(Transition(
        target=at_least_2_g,
        guard="action == 8",
        sync="next_state?",
    ))

    return initial


if __name__ == "__main__":
    print_transitions(build_prop2())
