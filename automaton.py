class Node:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.transitions = []

    def add_transition(self, transition):
        self.transitions.append(transition)


class Transition:
    def __init__(self, target, guard="", sync="", update=""):
        self.target = target
        self.guard = guard
        self.sync = sync
        self.update = update


def describe(node):
    return f"{node.name}({node.id})"


def print_transitions(initial):
    visited_ids = set()
    to_visit = [initial]
    while to_visit:
        node = to_visit.pop(0)
        if node.id in visited_ids:
            continue
        visited_ids.add(node.id)
        for transition in node.transitions:
            labels = " ".join(filter(None, [transition.guard, transition.sync, transition.update]))
            print(f"{describe(node)} --[{labels}]--> {describe(transition.target)}")
            to_visit.append(transition.target)
