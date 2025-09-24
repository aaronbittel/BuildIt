.PHONY: tui

tui:
	@uv run src/tui/main.py

watch:
	@uv run watchmedo auto-restart --patterns="*.py" -- uv run src/tui/main.py
