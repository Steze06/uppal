F_FUNCTIONS = {"f1": (6, 7), "f2": (8, 9)}
G_FUNCTIONS = {"g1": 10, "g2": 11, "g3": 12}


def inverse_name(name):
	return f"inv_{name}"


def action_codes(f_functions, g_functions):
	codes = dict(g_functions)
	for name, (action, inverse_action) in f_functions.items():
		codes[name] = action
		codes[inverse_name(name)] = inverse_action
	return codes
