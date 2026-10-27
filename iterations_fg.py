from functions import F_FUNCTIONS, G_FUNCTIONS
from paths_fg import PATHS, build_path
from prop1 import build_prop1
from prop2_fg import build_prop2_fg
from witness import find_trace, print_trace


def main():
	receivers = [build_prop1(), build_prop2_fg(F_FUNCTIONS, G_FUNCTIONS)]
	for description, function_names, prop2_target in PATHS:
		print(f"=== {description}: {' -> '.join(function_names)} ===")
		print(f"E<>( prop1.ok && prop2.{prop2_target})")
		path_start, _ = build_path(function_names)
		trace = find_trace(path_start, receivers, ("ok", prop2_target))
		if trace is None:
			print("NOT satisfied: no reachable state matches.")
		else:
			print_trace(*trace)
		print()


if __name__ == "__main__":
	main()
