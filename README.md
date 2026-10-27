# International Project

We took a small UPPAAL model (`fichier_f_ref.xml`) and rebuilt it in plain Python. That way we can follow what it does step by step, check the answers UPPAAL gives us, and see *why* each answer is what it is, without opening UPPAAL.

## The model

The model has three parts that work together:

- **path8**: a fixed path of 8 steps (`state_1` to `state_7`, then `end`). At each step it sets a few shared values (`action`, `p`, `s`, `integ_r`, `integ_cr`) and sends a signal telling the others to move.
- **prop1**: a watcher that looks at `p`, `s`, `integ_r` and `integ_cr`. If things happen in the right order it ends up in `ok`. If not, it ends up in `Error`.
- **prop2**: a watcher that looks at `action`. It counts which actions (6, 7 or 8) show up and in what order, and moves through states like `f`, `g` or `at_least_2_g`.

Every time path8 takes a step, both watchers look at the shared values and move too (or stay where they are if nothing matches).

## The questions

The XML comes with a few questions. Each one asks: "is there a way to end up in this situation?"

- Can `prop1` be in `ok` while `prop2` is in `f`?
- Can `prop1` be in `ok` while `prop2` is in `g`?
- Can `prop1` be in `ok` while `prop2` is in `at_least_2_g`?

## How it works

1. **Build the parts.** Each part of the model is written as a set of states with arrows between them (`path8.py`, `prop1.py`, `prop2.py`).
2. **Make sure we copied them right.** `check.py` reads the XML and compares it with our Python version, arrow by arrow. If anything is missing or extra, it says so.
3. **Run them together.** `product.py` starts all three parts at the beginning and tries every possible move, keeping track of where each part is and what the shared values are. It stops when there is nothing new left to reach.
4. **Answer the questions.** We look through everything that can be reached and check whether the situation from each question shows up.
5. **Show the way there.** `witness.py` does the same search, but remembers how it got to each place. When a question is answered "yes", it prints the shortest list of steps that leads there.

## What we found

| Question | Answer |
|---|---|
| `prop1` in `ok` and `prop2` in `f` | No |
| `prop1` in `ok` and `prop2` in `g` | Yes, after 8 steps |
| `prop1` in `ok` and `prop2` in `at_least_2_g` | No |

In total, the three parts together can only be in 10 different situations, so the search is quick.

## Reading the output of `witness.py`

Each numbered line shows where every part is and the current values:

```
7. end(id4) (id17) g(id39) | action=3 integ_cr=True integ_r=False p=True s=True
   end(id4) --[next_state! action = 3, ...]--> end(id4)
8. end(id4) ok(id18) g(id39) | action=3 integ_cr=True integ_r=False p=True s=True
```

The first three names are the positions of path8, prop1 and prop2 (states without a name only show their id). The line in between shows the step path8 took to get from one situation to the next.

## Files

- `automaton.py`: the basic building blocks (states and the arrows between them).
- `path8.py`, `prop1.py`, `prop2.py`: the three parts of the model, written in Python.
- `product.py`: runs all three together and lists every situation they can reach.
- `check.py`: makes sure our Python version matches the XML, then answers the questions.
- `witness.py`: for each question, prints the exact steps that lead to the answer.
- `fichier_f_ref.xml`: the original UPPAAL model.

## How to run

You only need Python 3. No extra packages.

```bash
python3 check.py     # compare with the XML and answer the questions
python3 witness.py   # show the steps that lead to each answer
python3 product.py   # list everything the system can reach
```

Each of `path8.py`, `prop1.py` and `prop2.py` can also be run alone to print its own states and arrows.

The `uppaal-5.0.0-linux64` folder has the UPPAAL tool itself. You can open the original model with `./uppaal-5.0.0-linux64/uppaal` and compare its answers with ours.
