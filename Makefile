.PHONY: ruff format check

fmt: 
	ruff format
	ruff check --fix

chk: fmt
	pytest