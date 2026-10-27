# International Project

We took a small UPPAAL model (`fichier_f_ref.xml`) and rebuilt it in plain Python, so we can follow what it does step by step without opening UPPAAL.

The model has three parts:

- **path8**: a fixed path of 8 steps. At each step it sets a few values (`action`, `p`, `s`, ...) and tells the others to move.
- **prop1** and **prop2**: two watchers. They follow path8 and move to a new state when they see a certain pattern.

The question we want answered: can path8 lead the watchers into certain states (for example `prop1` in `ok` and `prop2` in `f`)?

## Files

- `automaton.py`: the basic building blocks (states and the arrows between them).
- `path8.py`, `prop1.py`, `prop2.py`: the three parts of the model, written in Python.
- `product.py`: runs all three together and lists every situation they can reach.
- `check.py`: makes sure our Python version matches the XML, then answers the questions.
- `witness.py`: for each question, prints the exact steps that lead to the answer.

## How to run

You only need Python 3.

```bash
python3 check.py     # compare with the XML and answer the questions
python3 witness.py   # show the steps that lead to each answer
python3 product.py   # list everything the system can reach
```

Each of `path8.py`, `prop1.py` and `prop2.py` can also be run alone to print its own states.

The `uppaal-5.0.0-linux64` folder has the UPPAAL tool, if you want to open the original model and compare.
