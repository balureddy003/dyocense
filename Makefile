.PHONY: dev prod stop logs ps shell-kernel shell-api shell-client

DEV_COMPOSE=docker compose -f docker-compose.yml -f docker-compose.dev.yml
PROD_COMPOSE=docker compose

## Start full stack in development mode (with hot reload)
dev:
	$(DEV_COMPOSE) up -d --build

## Start full stack in production mode
prod:
	$(PROD_COMPOSE) up -d --build

## Stop all containers (dev or prod)
stop:
	$(PROD_COMPOSE) down

## Tail logs from all services
logs:
	$(PROD_COMPOSE) logs -f

## Show container status
ps:
	$(PROD_COMPOSE) ps

## Open a shell inside the kernel container
shell-kernel:
	$(PROD_COMPOSE) exec kernel /bin/sh

## Open a shell inside the API container
shell-api:
	$(PROD_COMPOSE) exec api /bin/sh

## Open a shell inside the client container
shell-client:
	$(PROD_COMPOSE) exec client /bin/sh
