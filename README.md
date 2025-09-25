# Análise de Algoritmos de Busca em Grafos de Voos

Este projeto realiza a análise de desempenho de diferentes algoritmos de busca em grafos, utilizando dados reais de voos entre aeroportos internacionais.

## Pré-requisitos

- Python 3 ou Docker

## Execução com Docker (Recomendado)

1. Construa a imagem Docker:

Comando:

```bash
docker build -t grafo-voos .
```

Makefile:

```bash
make build
```

2. Execute o container montando um volume para salvar os resultados:

```bash
docker run --rm -v $(pwd)/resultados:/app/output grafo-voos
```

Makefile:

```bash
make run
```

Os arquivos de resultado serão salvos na pasta `resultados/` do diretório atual.

## Execução Local

### Instalação das dependências

Execute o comando abaixo na pasta do projeto:

```bash
pip install -r requirements.txt
```

### Como executar

1. Primeiro, extraia e processe os dados:

```bash
python3 extrai_dados.py
```

2. Execute o script principal:

```bash
python3 grafo.py
```

## O que o projeto faz

1. **Extração de dados** (`extrai_dados.py`):
   - Processa os arquivos `_airports.dat` e `_routes.dat`
   - Filtra aeroportos internacionais relevantes para a busca
   - Gera o arquivo `rotas_com_coordenadas.csv`

2. **Análise de grafos** (`grafo.py`):
   - Constrói o grafo não-direcionado com distâncias reais
   - Executa e mede os algoritmos de busca (Dijkstra, A*, Gulosa, DFS, BFS)
   - Salva as métricas em `resultados_metricas.csv`
   - Gera visualizações `grafo_aeroportos.html` utilizando Pyvis

## Dependências principais
- pandas
- numpy
- pyvis
- haversine