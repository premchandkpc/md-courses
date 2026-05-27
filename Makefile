.PHONY: help serve clean

help:
	@echo "Engineering Knowledge Universe"
	@echo ""
	@echo "Usage:"
	@echo "  make serve       Start HTTP server on http://localhost:3000"
	@echo "  make help        Show this help"

serve:
	@cd data && node server.js

.DEFAULT_GOAL := help
