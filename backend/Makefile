.PHONY: tui fix mypy

tui:
	@uv run src/tui/main.py

fix:
	@uv tool run ruff check --extend-select I src/tui/ --fix . && uv tool run ruff format src/tui

mypy:
	@uv run mypy src/tui
