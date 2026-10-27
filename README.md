# International Project

We took a small UPPAAL model (fichier_f_ref.xml) and rewrote it in Python so we can follow what it does step by step without opening UPPAAL.

The model has 3 parts:
- path8: a fixed path of 8 steps. At each step it sets some values (action, p, s, ...) and tells the others to move.
- prop1 and prop2: two watchers. They follow path8 and change state when they see a certain pattern.

The question is: can path8 lead the watchers into certain states (for example prop1 in ok and prop2 in f)?

We also made an extended version with two invertible functions (f1, f2) and three functions that can't be undone (g1, g2, g3), plus some paths to test it. This is explained further down.


## Files

Original model:
- automaton.py - the basic building blocks (states and arrows between them)
- path8.py, prop1.py, prop2.py - the three parts of the model in Python
- product.py - runs all three together and lists every situation they can reach
- check.py - checks that the Python version matches the XML, then answers the questions
- witness.py - for each question, prints the steps that lead to the answer

Extended model:
- functions.py - the list of functions (f1, f2, g1, g2, g3) and the action number of each one
- prop2_fg.py - builds prop2 for any list of f and g functions
- paths_fg.py - builds a path from a list of function names, and has the example paths
- iterations_fg.py - runs every example path against prop1 and the extended prop2 and prints each step


## How to run

You only need Python 3. Run the commands from this folder.

    python3 check.py      (compare with the XML and answer the questions)
    python3 witness.py    (show the steps that lead to each answer)
    python3 product.py    (list everything the system can reach)

path8.py, prop1.py and prop2.py can also be run alone to print their states.

For the extended model:

    python3 iterations_fg.py   (walk every example path step by step, this is the one to present)
    python3 paths_fg.py        (print only the steps of every example path)
    python3 prop2_fg.py        (print every arrow of the extended prop2)


## How the model works

Shared values

All the parts read and write the same global values. They come from the declarations at the top of the XML and they all start at 0 or false:
- action (number, starts at 0): what kind of action happens at this step
- integ_r (true/false): integrity is requested
- integ_cr (true/false): integrity control is requested
- p (true/false): the enclave is protected
- s (true/false): the enclave offers a signature service

The numbers for action are also defined in the XML:
- 0 undefined, 1 creation, 2 transition, 3 read, 4 non-deterministic write, 5 store
- from 6 on come the f functions, each one followed by its inverse. With n f functions they take the numbers 6 to 6 + 2n - 1
- after them come the g functions. With m g functions they take the numbers 6 + 2n to 6 + 2n + m - 1

The XML has n = 1 and m = 1, so f is 6, its inverse is 7 and g is 8.

How the parts move together

The path drives everything. At each step it sets new values and sends next_state!.

prop1 and prop2 listen. Every time the path sends next_state!, each of them looks at its arrows and takes one whose guard is true. If none is allowed it stays where it is.

Note: the guards are checked against the values from before the path changes them. So a watcher always reacts one step after the path sets a value. You can see it in every trace: the path sets action = 6 at one step and prop2 only moves to f1 at the next one.

prop1

prop1 looks at the protection values (integ_r, integ_cr, p, s).

It gets to ok when integrity is first requested on a protected enclave with a signature service, and later integrity control is requested while the enclave is still protected. It goes to Error if integrity is requested on an enclave that isn't protected.

prop1 is the same in the original and in the extended model.

prop2

prop2 looks at the order in which the f and g functions are applied:
- an f followed by its inverse (or the inverse followed by f) cancels out and prop2 goes back to invariant
- one g is fine and prop2 goes to g. A second g sends it to at_least_2_g
- after a g you can still apply an f and undo it (g_f, g_inv_f) and prop2 comes back to g
- applying the same f twice, or a g while an f is still applied, is "unmanaged": prop2 goes into one of the unmanaged_* states and stays there


## Extended model (f1, f2, g1, g2, g3)

The functions

They are in functions.py. The f functions have an inverse, the g functions don't:

    F_FUNCTIONS = {"f1": (6, 7), "f2": (8, 9)}
    G_FUNCTIONS = {"g1": 10, "g2": 11, "g3": 12}

So with n = 2 and m = 3, following the numbering from the XML:
- f1 is 6 and its inverse inv_f1 is 7
- f2 is 8 and its inverse inv_f2 is 9
- g1 is 10, g2 is 11, g3 is 12, no inverse

action_codes(f_functions, g_functions) puts all of these in one dictionary from name to number ({"f1": 6, "inv_f1": 7, ...}). The paths use it to turn names into numbers.

The extended prop2

build_prop2_fg(f_functions, g_functions) builds prop2 for whatever f and g functions you give it. The rules are the same as in the original prop2, just repeated for every f. Below, fi means any f function and fj means a different one.

From the start, prop2 always goes to invariant on the first step.

From invariant:
- fi goes to fi, inv_fi goes to inv_fi
- any g goes to g

From fi (an f is applied and not undone yet):
- inv_fi undoes it and goes back to invariant
- fi again goes to unmanaged_fi_twice
- any g goes to unmanaged_fi_g
- a different function fj or inv_fj goes to unmanaged_fi_fj or unmanaged_fi_inv_fj, for example unmanaged_f1_inv_f2

From inv_fi it's the same but mirrored:
- fi undoes it and goes back to invariant
- inv_fi again goes to unmanaged_inv_fi_twice
- any g goes to unmanaged_inv_fi_g
- a different function goes to unmanaged_inv_fi_fj or unmanaged_inv_fi_inv_fj

From g:
- fi goes to g_fi, inv_fi goes to g_inv_fi
- any g goes to at_least_2_g

From g_fi (a g was applied, then an f that isn't undone yet):
- inv_fi undoes the f and goes back to g
- fi again goes to unmanaged_fi_twice
- any g goes to at_least_2_g
- a different function goes to the same unmanaged_fi_... state as from fi

From g_inv_fi it's the mirror of g_fi: fi goes back to g, inv_fi again goes to unmanaged_inv_fi_twice, any g goes to at_least_2_g, and a different function goes to unmanaged_inv_fi_...

Other things:
- g1, g2 and g3 are all treated the same, as "a g". So g1 then g3 also ends in at_least_2_g.
- actions that aren't functions, like 1 or 3, don't move prop2
- at_least_2_g and all the unmanaged_* states are final, prop2 never leaves them

With f1, f2, g1, g2, g3 there are 28 states and 71 arrows: the start, invariant and g, then 8 states where a function is still applied (f1, inv_f1, f2, inv_f2, g_f1, g_inv_f1, g_f2, g_inv_f2), and 17 final states (at_least_2_g and 16 unmanaged_* ones). Run python3 prop2_fg.py to see every arrow.

Differences from the original prop2

With only one f and one g, the extended prop2 is the same as the original except for 3 things:

1. Names. In the original, unmanaged_f2 means "f applied twice". Now there is a function called f2 so that name would be confusing, so it's now unmanaged_f1_twice. Same for unmanaged_inv_f2, which is now unmanaged_inv_f1_twice.
2. Mixing two f functions. The original only has one f so it never had this case. Here, if you apply a different f (or its inverse) while one is still applied, prop2 goes to an unmanaged_<first>_<second> state.
3. The g_f state. In the XML, g_f goes to unmanaged_f2 when it sees a g (action == 8), and it has no arrow for f being applied again. We think that's a mistake in the XML, because g_inv_f does go to unmanaged_inv_f2 when inv_f is applied again. So the extended model does it like g_inv_f: in g_fi, applying fi again goes to unmanaged_fi_twice. prop2.py is not changed and still matches the XML.

The paths

build_path(function_names) builds a path like path8 from a list of function names. Every path looks like this:

1. a start step with action = 1 (creation) and p, s and integ_r set to true. This gets prop1 started correctly.
2. one step for each function in the list. action is the function's number, everything else is false.
3. an end step with action = 3 (read) and p, s and integ_cr set to true. This lets prop1 reach ok.
4. the end state, which keeps repeating the end step, like in path8.

The states are named state_1, state_2, ... and end, like in path8. As a check, build_path(["inv_f", "f", "inv_f", "f", "g"]) with the numbers from the original model gives back path8 exactly.

The example paths are in PATHS in paths_fg.py. Each one has a description, the functions it applies, and the state prop2 should end in:

1. f1 undone by inv_f1, then g2: f1 -> inv_f1 -> g2, ends in g
2. f1 and f2 each undone, then g1: f1 -> inv_f1 -> f2 -> inv_f2 -> g1, ends in g
3. g3, then f2 undone by inv_f2: g3 -> f2 -> inv_f2, ends in g
4. inv_f2 undone by f2: inv_f2 -> f2, ends in invariant
5. f1 left applied: f1, ends in f1
6. two g functions: g1 -> g3, ends in at_least_2_g
7. f1 applied twice: f1 -> f1, ends in unmanaged_f1_twice
8. f1 then f2: f1 -> f2, ends in unmanaged_f1_f2
9. f2 then g1: f2 -> g1, ends in unmanaged_f2_g

All 9 reach prop1.ok together with the prop2 state above.

The iterations

iterations_fg.py takes every path from PATHS and runs it with prop1 and the extended prop2.

For each path it asks E<>( prop1.ok && prop2.<expected state>), meaning: can the system get to a point where prop1 is in ok and prop2 is in the expected state? If yes it prints the shortest list of steps that gets there. If not it prints NOT satisfied.

It uses find_trace and print_trace from witness.py, so the output looks the same as python3 witness.py.

Reading the output

This is path 8 (f1 -> f2):

    === f1 then f2: f1 -> f2 ===
    E<>( prop1.ok && prop2.unmanaged_f1_f2)
    0. state_1(id0) (id16) (l0) | action=0 integ_cr=False integ_r=False p=False s=False
       state_1(id0) --[next_state! action = 1, p = true, s = true, integ_r = true, integ_cr = false]--> state_2(id1)
    1. state_2(id1) (id19) invariant(l1) | action=1 integ_cr=False integ_r=True p=True s=True
       state_2(id1) --[next_state! action = 6, p = false, s = false, integ_r = false, integ_cr = false]--> state_3(id2)
    2. state_3(id2) (id17) invariant(l1) | action=6 integ_cr=False integ_r=False p=False s=False
       state_3(id2) --[next_state! action = 8, p = false, s = false, integ_r = false, integ_cr = false]--> state_4(id3)
    3. state_4(id3) (id17) f1(l2) | action=8 integ_cr=False integ_r=False p=False s=False
       state_4(id3) --[next_state! action = 3, p = true, s = true, integ_r = false, integ_cr = true]--> end(id4)
    4. end(id4) (id17) unmanaged_f1_f2(l6) | action=3 integ_cr=True integ_r=False p=True s=True
       end(id4) --[next_state! action = 3, p = true, s = true, integ_r = false, integ_cr = true]--> end(id4)
    5. end(id4) ok(id18) unmanaged_f1_f2(l6) | action=3 integ_cr=True integ_r=False p=True s=True

How to read it:
- the numbered lines (0., 1., ...) show where the whole system is: first the path, then prop1, then prop2, and after the | the current values
- every state is written as name(id). States with no name only show the id, for example (id16) is where prop1 starts and (l0) is where prop2 starts
- the indented lines are the step the path takes and the values it sets
- the watchers are always one line behind the values. action=6 (f1) is set on line 2 and prop2 moves to f1 on line 3. Then action=8 (f2) is set on line 3 and prop2 moves to unmanaged_f1_f2 on line 4
- the last line is the answer: prop1 is in ok and prop2 is in unmanaged_f1_f2

Adding a function or a path

- new f function: add it to F_FUNCTIONS with its number and the number of its inverse, for example "f3": (13, 14). The numbers must not be used by another function.
- new g function: add it to G_FUNCTIONS, for example "g4": 15
- new path: add a line to PATHS with a description, the function names and the state prop2 should end in, for example ("f2 undone, then two g", ["f2", "inv_f2", "g1", "g2"], "at_least_2_g")

build_prop2_fg and build_path pick up the changes by themselves. Then run python3 iterations_fg.py again.
