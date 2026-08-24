.PHONY: setup plan dry-run test lint check

setup:
	uv sync --extra dev

plan:
	uv run commute-podcast plan examples/pilot.md

dry-run:
	uv run commute-podcast generate examples/pilot.md --title "Pilot Episode" --dry-run

test:
	uv run pytest

lint:
	uv run ruff check .

check: lint test plan dry-run
