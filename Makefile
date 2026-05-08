COMPOSE := docker compose
SERVICE := api
APP_URL := http://localhost:8000

.DEFAULT_GOAL := help

.PHONY: help build up start down stop restart rebuild logs ps shell health test clean

help: ## Lista os comandos disponiveis
	@echo "Comandos disponiveis:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  make %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Constroi/reconstroi a imagem Docker
	@$(COMPOSE) build

up: ## Sobe a API em segundo plano
	@$(COMPOSE) up -d
	@echo "API em $(APP_URL)"

start: up ## Alias para subir a API

down: ## Derruba containers e rede do projeto
	@$(COMPOSE) down

stop: down ## Alias para derrubar a API

restart: down up ## Reinicia a API

rebuild: down build up ## Reconstroi e sobe a API do zero

logs: ## Mostra os logs da API
	@$(COMPOSE) logs -f $(SERVICE)

ps: ## Mostra o status dos containers
	@$(COMPOSE) ps

shell: ## Abre um shell dentro do container da API
	@$(COMPOSE) exec $(SERVICE) sh

health: ## Testa a rota /health
	@curl -sS $(APP_URL)/health
	@echo

test: ## Roda os testes no Docker
	@$(COMPOSE) run --rm $(SERVICE) uv run pytest

clean: ## Remove containers, rede e volumes do projeto
	@$(COMPOSE) down -v --remove-orphans
