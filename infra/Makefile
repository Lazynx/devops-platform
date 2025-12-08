SERVICES := auth-service deployment-service observability-service project-service secrets-service

.PHONY: migrate-all migrate-%

migrate-all:
	@for service in $(SERVICES); do \
		echo "Migrating $$service..."; \
		docker compose exec $$service uv run alembic upgrade head || exit 1; \
		echo "Done."; \
	done
	@echo "All migrations completed successfully."

migrate-%:
	@echo "Migrating $*..."
	@docker compose exec $* uv run alembic upgrade head
