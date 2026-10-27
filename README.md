# International Project

We took a small UPPAAL model (`fichier_f_ref.xml`) and rebuilt it in plain Python, so we can follow what it does step by step without opening UPPAAL.

The model has three parts:

- **path8**: a fixed path of 8 steps. At each step it sets a few values (`action`, `p`, `s`, ...) and tells the others to move.
- **prop1** and **prop2**: two watchers. They follow path8 and move to a new state when they see a certain pattern.

The question we want answered: can path8 lead the watchers into certain states (for example `prop1` in `ok` and `prop2` in `f`)?

On top of that model there is an extended version with **two invertible functions (f1, f2)** and **three non-invertible functions (g1, g2, g3)**, with several paths to walk through it. See [Extended model: f1, f2, g1, g2, g3](#extended-model-f1-f2-g1-g2-g3).

## Files

Original model:

- `automaton.py`: the basic building blocks (states and the arrows between them).
- `path8.py`, `prop1.py`, `prop2.py`: the three parts of the model, written in Python.
- `product.py`: runs all three together and lists every situation they can reach.
- `check.py`: makes sure our Python version matches the XML, then answers the questions.
- `witness.py`: for each question, prints the exact steps that lead to the answer.

Extended model:

- `functions.py`: the list of functions (f1, f2, g1, g2, g3) and the action number of each one.
- `prop2_fg.py`: builds prop2 for any list of f and g functions.
- `paths_fg.py`: builds a path from a list of function names, plus the list of example paths.
- `iterations_fg.py`: runs every example path against prop1 and the extended prop2 and prints each step.

## How to run

You only need Python 3. Run the commands from this folder.

```bash
python3 check.py     # compare with the XML and answer the questions
python3 witness.py   # show the steps that lead to each answer
python3 product.py   # list everything the system can reach
```

Each of `path8.py`, `prop1.py` and `prop2.py` can also be run alone to print its own states.

For the extended model:

```bash
python3 iterations_fg.py   # walk every example path, step by step (the one to present)
python3 paths_fg.py        # print only the steps of every example path
python3 prop2_fg.py        # print every arrow of the extended prop2
```

The `uppaal-5.0.0-linux64` folder has the UPPAAL tool, if you want to open the original model and compare.

## How the model works

### The shared values

All the parts read and write the same global values, taken from the declarations in the XML:

| Value      | Type | Start | Meaning                                    |
|------------|------|-------|--------------------------------------------|
| `action`   | int  | `0`   | the kind of action done at this step       |
| `integ_r`  | bool | false | integrity is requested                     |
| `integ_cr` | bool | false | integrity control is requested             |
| `p`        | bool | false | the enclave is protected                   |
| `s`        | bool | false | the enclave offers a signature service     |

The `action` numbers come from the XML:

| `action` | Meaning                                             |
|----------|-----------------------------------------------------|
| 0        | undefined                                           |
| 1        | creation                                            |
| 2        | transition                                          |
| 3        | read                                                |
| 4        | non-deterministic write                             |
| 5        | store                                               |
| 6 to 6+2n-1 | the f functions and their inverses (n functions) |
| 6+2n to 6+2n+m-1 | the g functions (m functions)              |

In the XML `n = 1` and `m = 1`, so f is `6`, the inverse of f is `7` and g is `8`.

### How the parts move together

The path is the **sender**: at each step it sets new values and sends `next_state!`.

prop1 and prop2 are **receivers**: each time the path sends `next_state!`, each of them takes one arrow whose guard is true, if there is one. If none of their arrows is allowed, they stay where they are.

Guards are checked against the values **before** the path changes them. This means a watcher reacts to a value one step after the path sets it. You can see this in every trace: the path sets `action = 6` at one step, and prop2 moves to `f1` only at the next step.

### prop1

prop1 checks the protection values (`integ_r`, `integ_cr`, `p`, `s`). It reaches `ok` when integrity is requested on a protected enclave with a signature service, and later integrity control is requested on a protected enclave. It reaches `Error` if integrity is requested on an enclave that isn't protected.

prop1 is the same in the original and in the extended model.

### prop2

prop2 checks the order of the f and g functions:

- An f followed by its inverse (or the inverse followed by f) cancels out, and prop2 goes back to `invariant`.
- One g is fine (`g`). A second g leads to `at_least_2_g`.
- After a g, an f can still be applied and undone (`g_f`, `g_inv_f`), and prop2 goes back to `g`.
- Applying the same f twice, or a g while an f is still applied, is **unmanaged**: prop2 goes into an `unmanaged_*` state and stays there.

## Extended model: f1, f2, g1, g2, g3

### The functions

`functions.py` lists the functions. The f functions have an inverse, the g functions don't.

```python
F_FUNCTIONS = {"f1": (6, 7), "f2": (8, 9)}
G_FUNCTIONS = {"g1": 10, "g2": 11, "g3": 12}
```

With `n = 2` and `m = 3`, the XML numbering gives:

| Function | `action` | Inverse  | `action` |
|----------|----------|----------|----------|
| f1       | 6        | inv_f1   | 7        |
| f2       | 8        | inv_f2   | 9        |
| g1       | 10       | none     |          |
| g2       | 11       | none     |          |
| g3       | 12       | none     |          |

`action_codes(f_functions, g_functions)` turns these into one table from name to number (`{"f1": 6, "inv_f1": 7, ...}`), used to build the paths.

### The extended prop2

`build_prop2_fg(f_functions, g_functions)` builds prop2 from any list of f and g functions. It uses the same rules as the original prop2, repeated for each f:

| From state           | Action seen          | Goes to                     |
|----------------------|----------------------|-----------------------------|
| start                | anything             | `invariant`                 |
| `invariant`          | fi                   | `fi`                        |
| `invariant`          | inv_fi               | `inv_fi`                    |
| `invariant`          | any g                | `g`                         |
| `fi`                 | inv_fi               | `invariant`                 |
| `inv_fi`             | fi                   | `invariant`                 |
| `fi`                 | fi again             | `unmanaged_fi_twice`        |
| `inv_fi`             | inv_fi again         | `unmanaged_inv_fi_twice`    |
| `fi` / `inv_fi`      | any g                | `unmanaged_fi_g` / `unmanaged_inv_fi_g` |
| `fi` / `inv_fi`      | a different fj or inv_fj | `unmanaged_<first>_<second>`, e.g. `unmanaged_f1_inv_f2` |
| `g`                  | fi                   | `g_fi`                      |
| `g`                  | inv_fi               | `g_inv_fi`                  |
| `g`                  | any g                | `at_least_2_g`              |
| `g_fi`               | inv_fi               | `g`                         |
| `g_inv_fi`           | fi                   | `g`                         |
| `g_fi` / `g_inv_fi`  | the same function again | `unmanaged_fi_twice` / `unmanaged_inv_fi_twice` |
| `g_fi` / `g_inv_fi`  | any g                | `at_least_2_g`              |
| `g_fi` / `g_inv_fi`  | a different fj or inv_fj | `unmanaged_<first>_<second>` |

The g functions are treated as one group: g1, g2 and g3 all count as "a g", so `g1` then `g3` leads to `at_least_2_g`.

Any action not in the table (for example `1` or `3`) doesn't move prop2.

With f1, f2, g1, g2, g3 this gives **28 states and 71 arrows**:

- 1 start state, `invariant` and `g`
- 8 states with a function still applied: `f1`, `inv_f1`, `f2`, `inv_f2`, `g_f1`, `g_inv_f1`, `g_f2`, `g_inv_f2`
- 17 final states, which have no arrows out: `at_least_2_g` and 16 `unmanaged_*` states

Run `python3 prop2_fg.py` to see every arrow.

### Differences from the original prop2

With only one f and one g, the extended prop2 is the original prop2, except for these points:

1. **State names.** `unmanaged_f2` in the original means "f applied twice". With a function called `f2` that name would be confusing, so it is now `unmanaged_f1_twice` (and `unmanaged_inv_f1_twice` for `unmanaged_inv_f2`).
2. **Mixing two f functions.** The original has only one f, so it has no rule for this. In the extended model, applying a different f (or its inverse) while one is still applied leads to an `unmanaged_<first>_<second>` state.
3. **The `g_f` state.** In the XML, `g_f` goes to `unmanaged_f2` on a g (`action == 8`) and has no arrow for f applied again. That looks like a mistake in the XML, because `g_inv_f` goes to `unmanaged_inv_f2` when inv_f is applied again. The extended model follows `g_inv_f`: in `g_fi`, applying `fi` again leads to `unmanaged_fi_twice`. `prop2.py` is unchanged and still matches the XML.

### The paths

`build_path(function_names)` builds a path like path8 from a list of function names. Every path has the same shape:

1. **Start step**: `action = 1` (creation) with `p`, `s` and `integ_r` true. This lets prop1 start well.
2. **One step per function** in the list: `action` is the number of that function, all other values are false.
3. **End step**: `action = 3` (read) with `p`, `s` and `integ_cr` true. This lets prop1 reach `ok`.
4. **`end`**: repeats the end step forever, like path8.

The states are named `state_1`, `state_2`, ... and `end`, like in path8. For example, `build_path(["inv_f", "f", "inv_f", "f", "g"])` with the numbers of the original model rebuilds path8 exactly.

`PATHS` in `paths_fg.py` holds the example paths. Each one has a description, the list of functions, and the state prop2 should end in:

| # | Path                                   | Functions                               | prop2 ends in          |
|---|----------------------------------------|-----------------------------------------|------------------------|
| 1 | f1 undone by inv_f1, then g2           | f1 → inv_f1 → g2                        | `g`                    |
| 2 | f1 and f2 each undone, then g1         | f1 → inv_f1 → f2 → inv_f2 → g1          | `g`                    |
| 3 | g3, then f2 undone by inv_f2           | g3 → f2 → inv_f2                        | `g`                    |
| 4 | inv_f2 undone by f2                    | inv_f2 → f2                             | `invariant`            |
| 5 | f1 left applied                        | f1                                      | `f1`                   |
| 6 | two g functions                        | g1 → g3                                 | `at_least_2_g`         |
| 7 | f1 applied twice                       | f1 → f1                                 | `unmanaged_f1_twice`   |
| 8 | f1 then f2                             | f1 → f2                                 | `unmanaged_f1_f2`      |
| 9 | f2 then g1                             | f2 → g1                                 | `unmanaged_f2_g`       |

All 9 paths reach `prop1.ok` together with the prop2 state in the table.

### The iterations

`iterations_fg.py` runs every path from `PATHS` together with prop1 and the extended prop2. For each path it asks the question `E<>( prop1.ok && prop2.<expected state>)`: can the system reach a state where prop1 is in `ok` and prop2 is in the expected state? It then prints the shortest list of steps that gets there, or `NOT satisfied` if there is none.

It reuses `find_trace` and `print_trace` from `witness.py`, so the output looks the same as `python3 witness.py`.

### Reading the output

This is path 8 (`f1 → f2`):

```
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
```

- The numbered lines (`0.`, `1.`, ...) are the state of the whole system: the path, prop1, prop2, and then the values after `|`.
- Each state is written as `name(id)`. States without a name show only their id, for example `(id16)` is the start of prop1 and `(l0)` is the start of prop2.
- The indented lines are the step the path takes, with the values it sets.
- prop1 and prop2 react one line later than the values: `action=6` (f1) is set in line 2, and prop2 moves to `f1` in line 3. `action=8` (f2) is set in line 3, and prop2 moves to `unmanaged_f1_f2` in line 4.
- The last line is the state that answers the question: prop1 is in `ok` and prop2 is in `unmanaged_f1_f2`.

### Adding a function or a path

- **New f function**: add it to `F_FUNCTIONS` with its number and the number of its inverse, for example `"f3": (13, 14)`. Keep the numbers different from every other function.
- **New g function**: add it to `G_FUNCTIONS`, for example `"g4": 15`.
- **New path**: add a line to `PATHS` with a description, the list of function names and the state prop2 should end in, for example `("f2 undone, then two g", ["f2", "inv_f2", "g1", "g2"], "at_least_2_g")`.

`build_prop2_fg` and `build_path` pick up the changes on their own; then run `python3 iterations_fg.py` again.
