.PHONY: tui

tui:
	@uv run src/tui/main.py

fix:
	@uv tool run ruff check --extend-select I src/tui/ --fix .
