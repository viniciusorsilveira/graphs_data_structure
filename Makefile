IMAGE_NAME = grafo-voos
OUTPUT_DIR = ./resultados

.PHONY: all
all: build run

.PHONY: build
build:
	@echo "Construindo imagem docker ($(IMAGE_NAME))..."
	docker build -t $(IMAGE_NAME) .

.PHONY: run
run:
	@echo "Criando pasta para os resultados..."
	@mkdir -p $(OUTPUT_DIR)
	@echo "Executando container..."
	docker run --rm -v $(shell pwd)/$(OUTPUT_DIR):/app/output $(IMAGE_NAME)
	@echo "Resultados salvos em $(OUTPUT_DIR)/"

.PHONY: help
help:
	@echo "Opções disponíveis:"
	@echo "  build        - Constrói a imagem docker"
	@echo "  run          - Executa o container e cria a pasta de resultados"
