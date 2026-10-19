from automaton import Node, Transition, print_transitions


def build_prop1():
    initial = Node("id16", "")
    location_17 = Node("id17", "")
    location_19 = Node("id19", "")
    location_20 = Node("id20", "")
    location_22 = Node("id22", "")
    ok = Node("id18", "ok")
    error = Node("id21", "Error")

    initial.add_transition(Transition(
        target=location_19,
        sync="next_state?",
    ))

    location_19.add_transition(Transition(
        target=location_17,
        guard="integ_r == true and p == true and s == true",
        sync="next_state?",
    ))
    location_19.add_transition(Transition(
        target=location_20,
        guard="integ_r == true and p == true and s == false",
        sync="next_state?",
    ))
    location_19.add_transition(Transition(
        target=error,
        guard="integ_r == true and p == false",
        sync="next_state?",
    ))

    location_20.add_transition(Transition(
        target=location_17,
        guard="p == true and s == true",
        sync="next_state?",
    ))
    location_20.add_transition(Transition(
        target=error,
        guard="p == false",
        sync="next_state?",
    ))

    location_17.add_transition(Transition(
        target=location_22,
        guard="p == true and s == true",
        sync="next_state?",
    ))
    location_17.add_transition(Transition(
        target=ok,
        guard="integ_cr == true and p == true",
        sync="next_state?",
    ))

    location_22.add_transition(Transition(
        target=location_17,
        guard="p == false",
        sync="next_state?",
    ))
    location_22.add_transition(Transition(
        target=ok,
        guard="p == true and integ_cr == true",
        sync="next_state?",
    ))

    return initial


if __name__ == "__main__":
    print_transitions(build_prop1())
