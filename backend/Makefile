.PHONY: tui fix mypy

tui: mypy fix
	@uv run src/tui/main.py

fix:
	@uv tool run ruff check --extend-select I src/tui/ --fix . && uv tool run ruff format src/tui

mypy:
	@uv run mypy src/tui

prod:
	@BUILDIT_STORAGE="version_0_1" uv run src/tui/main.py

dump:
	@BUILDIT_STORAGE="dump" uv run src/tui/main.py
