.PHONY: help serve frontend frontend-build frontend-typecheck viz python clean frontmatter

help:
	@echo "Engineering Knowledge Universe — Interactive Platform"
	@echo ""
	@echo "Usage:"
	@echo "  make serve              Start API server on :3000"
	@echo "  make frontend           Start Vite dev server on :5173"
	@echo "  make frontend-build     Build frontend for production"
	@echo "  make frontend-typecheck TypeScript type check"
	@echo "  make python             Start Python server on :3000"
	@echo "  make viz                Run API server + frontend concurrently"
	@echo "  make frontmatter        Add/regen YAML frontmatter on all .md files"
	@echo "  make clean              Remove frontend node_modules + dist"
	@echo "  make help               Show this help"

serve:
	@node packages/api-server/server.js

frontend:
	@npm run dev -w packages/react-frontend

frontend-build:
	@npm run build -w packages/react-frontend

frontend-typecheck:
	@npm run typecheck -w packages/react-frontend

python:
	@/opt/homebrew/bin/python3 packages/python-server/server.py

viz:
	@echo "Starting API server on :3000 and frontend on :5173..."
	@node packages/api-server/server.js 3000 & sleep 1 && npm run dev -w packages/react-frontend

frontmatter:
	@python3 scripts/add-frontmatter.py --apply
	@echo "YAML frontmatter added/updated on all .md files"

clean:
	@rm -rf packages/react-frontend/node_modules packages/react-frontend/dist
	@echo "Cleaned react-frontend dependencies and build output"

.DEFAULT_GOAL := help
