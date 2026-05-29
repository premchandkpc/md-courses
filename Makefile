.PHONY: help serve frontend frontend-build frontend-typecheck viz clean

help:
	@echo "Engineering Knowledge Universe — Interactive Platform"
	@echo ""
	@echo "Usage:"
	@echo "  make serve              Start API server on :3000"
	@echo "  make frontend           Start Vite dev server on :5173"
	@echo "  make frontend-build     Build frontend for production"
	@echo "  make frontend-typecheck TypeScript type check"
	@echo "  make viz                Run API server + frontend concurrently"
	@echo "  make clean              Remove frontend node_modules + dist"
	@echo "  make help               Show this help"

serve:
	@cd data && node server.js

frontend:
	@npm run dev --prefix frontend

frontend-build:
	@npm run build --prefix frontend

frontend-typecheck:
	@cd frontend && npx tsc --noEmit

viz:
	@echo "Starting API server on :3000 and frontend on :5173..."
	@cd data && node server.js 3000 & sleep 1 && npm run dev --prefix frontend

clean:
	@rm -rf frontend/node_modules frontend/dist
	@echo "Cleaned frontend/ dependencies and build output"

.DEFAULT_GOAL := help
