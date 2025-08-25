.PHONY: backend frontend

backend:
	cd backend && uv run uvicorn src.main:app --reload --log-level=debug

frontend:
	cd frontend && npm run dev
