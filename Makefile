run:
	python3 -m tests.test_run

t_replay:
	python3 -m tests.test_replay

scratch:
	python3 -m tests.scratch
	cat rb

# t_something is short for test_something
t_all:
	pytest tests/test_logic.py
	pytest tests/test_map.py
	python3 -m tests.parallel_api_test

t_game:
	pytest tests/test_logic.py

t_map:
	pytest tests/test_map.py

t_parallel:
	python3 -m tests.parallel_api_test
