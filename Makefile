test:
	pytest

typecheck:
	mypy -p articlesa --check-untyped-defs --install-types