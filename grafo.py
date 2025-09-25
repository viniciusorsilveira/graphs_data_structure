import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
import pandas as pd
import numpy as np
import heapq
import time
import tracemalloc
from pyvis.network import Network
from collections import deque
from haversine import haversine, Unit

# Rotas aéreas com coordenadas dos aeroportos
url_dados = "./rotas_com_coordenadas.csv"
dados = pd.read_csv(url_dados)

# Dicionário com nomes completos dos aeroportos (hardcoded, pois não está no novo CSV)
legendas_aeroportos = {
    'GRU': 'Aeroporto Internacional de Guarulhos (São Paulo)',
    'GIG': 'Aeroporto Internacional do Galeão (Rio de Janeiro)',
    'JFK': 'Aeroporto Internacional John F. Kennedy (Nova York)',
    'LAX': 'Aeroporto Internacional de Los Angeles',
    'CDG': 'Aeroporto Charles de Gaulle (Paris)',
    'FRA': 'Aeroporto de Frankfurt',
    'AMS': 'Aeroporto Schiphol de Amsterdã',
    'DXB': 'Aeroporto Internacional de Dubai',
    'DOH': 'Aeroporto Internacional Hamad (Doha)',
    'IST': 'Aeroporto de Istambul',
    'HND': 'Aeroporto Internacional de Haneda (Tóquio)',
    'NRT': 'Aeroporto Internacional de Narita (Tóquio)'
}

# Dicionário para armazenar coordenadas para a heurística
coordenadas_aeroportos = {}
for _, linha in dados.iterrows():
    coordenadas_aeroportos[linha['origin_iata']] = (linha['origin_lat'], linha['origin_lon'])
    coordenadas_aeroportos[linha['destination_iata']] = (linha['destination_lat'], linha['destination_lon'])

# Construir grafo não-direcionado usando a distância de haversine como peso
grafo_voos = {}
for _, linha in dados.iterrows():
    origem = linha['origin_iata']
    destino = linha['destination_iata']
    
    # Usar coordenadas para calcular a distância real como peso da aresta
    distancia = haversine(
        (linha['origin_lat'], linha['origin_lon']),
        (linha['destination_lat'], linha['destination_lon']),
        unit=Unit.KILOMETERS,
    )
    
    # Adicionar aresta nos dois sentidos (grafo não-direcionado)
    grafo_voos.setdefault(origem, {})[destino] = distancia
    grafo_voos.setdefault(destino, {})[origem] = distancia

print(f"Total de aeroportos no grafo: {len(grafo_voos)}")

# Heurística para A* e Gulosa usando coordenadas reais
# Haversine é um algoritmo que calcula a distância do "grande círculo" 
# entre dois pontos na superfície de uma esfera, dado suas latitudes e longitudes.
def heuristica_haversine(aeroporto_a, aeroporto_b):
    # safety-check: verificar se os aeroportos existem nas coordenadas previamente carregadas
    if aeroporto_a not in coordenadas_aeroportos or aeroporto_b not in coordenadas_aeroportos:
        return 0
    lat1, lon1 = coordenadas_aeroportos[aeroporto_a]
    lat2, lon2 = coordenadas_aeroportos[aeroporto_b]

    # retorna a distância em quilômetros entre os dois aeroportos utilizando a fórmula de Haversine
    return haversine((lat1, lon1), (lat2, lon2), unit=Unit.KILOMETERS)

# Algoritmo de Dijkstra
def dijkstra_medido(grafo, origem, destino, contador):
    # safety-check: verificar se os aeroportos existem no grafo
    if origem not in grafo or destino not in grafo: return None, np.nan
    # fila de prioridade
    heap, visitados = [(0.0, origem, [])], set()
    while heap:
        # extrai o nó com menor custo da fila de prioridade
        custo, aeroporto, caminho = heapq.heappop(heap)
        # se o aeroporto já estiver visitado, pular a execução
        if aeroporto in visitados: continue
        contador['expandidos'] += 1
        caminho = caminho + [aeroporto]
        if aeroporto == destino: return caminho, custo
        visitados.add(aeroporto)
        # para cada vizinho, se não visitado, calcular o custo e adicionar na fila
        # o peso é a distancia previamente calculada
        for vizinho, peso in grafo.get(aeroporto, {}).items():
            if vizinho not in visitados: heapq.heappush(heap, (custo + peso, vizinho, caminho))
    return None, np.nan

# Busca Gulosa
def busca_gulosa_medido(grafo, origem, destino, contador):
    # safety-check: verificar se os aeroportos existem no grafo
    if origem not in grafo or destino not in grafo: return None, np.nan

    # fila de prioridade (distancia em km, aeroporto, caminho)
    heap, visitados = [(heuristica_haversine(origem, destino), origem, [])], set()
    while heap:
        # extrai o nó com menor custo da fila de prioridade
        # neste caso, o custo é apenas a heurística, ou seja, desconsidera o custo do caminho até o nó atual
        # sempre percorrerá o caminho que parece mais rápido
        _, aeroporto, caminho = heapq.heappop(heap)
        # se o aeroporto já estiver visitado, pular a execução
        if aeroporto in visitados: continue
        contador['expandidos'] += 1
        caminho = caminho + [aeroporto]
        if aeroporto == destino:
            # soma o custo do caminho encontrado iterando sobre os pares de aeroportos no caminho e somando as distâncias
            custo = sum(grafo[caminho[i]][caminho[i+1]] for i in range(len(caminho)-1))
            return caminho, custo
        visitados.add(aeroporto)
        for vizinho in grafo.get(aeroporto, {}).keys():
            if vizinho not in visitados: heapq.heappush(heap, (heuristica_haversine(vizinho, destino), vizinho, caminho))
    return None, np.nan

# Algoritmo A*
# Combina a busca de Dijkstra com a heurística para guiar a busca
def a_estrela_medido(grafo, origem, destino, contador):
    # safety-check: verificar se os aeroportos existem no grafo
    if origem not in grafo or destino not in grafo: return None, np.nan
    # f, g, aeroporto, caminho
    heap, visitados = [(heuristica_haversine(origem, destino), 0.0, origem, [])], set() 
    while heap:
        # extrai o nó com menor custo da fila de prioridade (f)
        # f = g + h
        # g = custo do caminho até o nó atual
        # h = heurística (distância estimada até o destino)
        _, g, aeroporto, caminho = heapq.heappop(heap)
        if aeroporto in visitados: continue
        contador['expandidos'] += 1
        caminho = caminho + [aeroporto]
        if aeroporto == destino: return caminho, g
        visitados.add(aeroporto)
        for vizinho, peso in grafo.get(aeroporto, {}).items():
            if vizinho not in visitados:
                g_novo = g + peso
                # soma o peso do vizinho com o custo acumulado (g) 
                # mais a heurística (h) até o destino
                f_novo = g_novo + heuristica_haversine(vizinho, destino)
                heapq.heappush(heap, (f_novo, g_novo, vizinho, caminho))
    return None, np.nan

# Busca em Profundidade (DFS)
def busca_profundidade_medido(grafo, origem, destino, contador):
    # safety-check: verificar se os aeroportos existem no grafo
    if origem not in grafo or destino not in grafo: return None, np.nan
    pilha, visitados = [(origem, [])], set()
    while pilha:
        aeroporto, caminho = pilha.pop()
        if aeroporto in visitados: continue
        contador['expandidos'] += 1
        caminho = caminho + [aeroporto]
        if aeroporto == destino:
            # soma o custo do caminho encontrado iterando sobre os pares de aeroportos no caminho e somando as distâncias
            custo = sum(grafo[caminho[i]][caminho[i+1]] for i in range(len(caminho)-1))
            return caminho, custo
        visitados.add(aeroporto)

        # nesse caso, a ordenação é feita em ordem alfabética
        # a cada iteração, adiciona os vizinhos em ordem reversa para que o menor 
        # fique no topo da pilha.
        # como a busca sempre retira do topo da pilha, isso garante a exploração 
        # do último nó inserido (profundidade)
        for vizinho in sorted(grafo.get(aeroporto, {}).keys(), reverse=True):
            # adiciona todos os vizinhos não visitados na pilha
            if vizinho not in visitados: pilha.append((vizinho, caminho))
    return None, np.nan

# Busca em Largura (BFS)
def busca_largura_medido(grafo, origem, destino, contador):
    # safety-check: verificar se os aeroportos existem no grafo
    if origem not in grafo or destino not in grafo: return None, np.nan
    # ao contrário do DFS, aqui utilizamos uma fila dupla para explorar os nós
    fila, visitados = deque([(origem, [])]), set()
    while fila:
        aeroporto, caminho = fila.popleft()
        if aeroporto in visitados: continue
        contador['expandidos'] += 1
        caminho = caminho + [aeroporto]
        if aeroporto == destino:
            custo = sum(grafo[caminho[i]][caminho[i+1]] for i in range(len(caminho)-1))
            return caminho, custo
        visitados.add(aeroporto)

        # nesse caso, a ordenação é feita em ordem alfabética
        # a cada iteração, adiciona os vizinhos em ordem normal
        # ---------------------------
        # como a busca sempre retira do início da fila, isso garante a exploração 
        # de todos os vizinhos do nó atual antes de ir para o próximo nível (largura)
        for vizinho in sorted(grafo.get(aeroporto, {}).keys()):
            # adiciona todos os vizinhos não visitados na fila
            if vizinho not in visitados: fila.append((vizinho, caminho))
    return None, np.nan


# Função para medir desempenho
def medir_algoritmo(funcao, grafo, origem, destino, rodadas=5):
    tempos, nos_expandidos, tamanhos_caminho, custos_caminho, memorias = [], [], [], [], []
    caminho_final = None  # Variável para armazenar o caminho da primeira execução

    # para cada rodada, medir tempo, memória, nós expandidos, tamanho e custo do caminho
    for i in range(rodadas):
        contador = {'expandidos': 0}
        # medir memória com tracemalloc
        tracemalloc.start()
        tempo_inicio = time.time()
        caminho, custo = funcao(grafo, origem, destino, contador)
        tempo_fim = time.time()
        # medir pico de memória
        _, mem_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        if i == 0: # Salva o caminho da primeira rodada
            caminho_final = caminho

        tempos.append(tempo_fim - tempo_inicio)
        nos_expandidos.append(contador['expandidos'])
        tamanhos_caminho.append(len(caminho) if caminho else np.nan)
        custos_caminho.append(custo if custo else np.nan)
        memorias.append(mem_peak)
    
    metricas = {
        'tempo_medio': np.nanmean(tempos), 'tempo_std': np.nanstd(tempos),
        'nos_medio': np.nanmean(nos_expandidos), 'nos_std': np.nanstd(nos_expandidos),
        'tamanho_medio': np.nanmean(tamanhos_caminho), 'tamanho_std': np.nanstd(tamanhos_caminho),
        'custo_medio': np.nanmean(custos_caminho), 'custo_std': np.nanstd(custos_caminho),
        'mem_medio': np.nanmean(memorias), 'mem_std': np.nanstd(memorias),
        'caminho_final': caminho_final
    }
    return metricas

def separador(simples=False):
    if simples:
        print("-"*80)
    else:
        print("="*80+ "\n")

def imprimir_metricas_organizadas(resultados, pares_conectados, lista_algoritmos):
    print("\nRELATÓRIO DE DESEMPENHO DOS ALGORITMOS DE BUSCA")
    separador()
    for i, par in enumerate(pares_conectados, 1):
        origem, destino = par
        nome_origem = legendas_aeroportos.get(origem, origem)
        nome_destino = legendas_aeroportos.get(destino, destino)
        
        print(f"{i}. ROTA: {origem} => {destino}")
        print(f"{nome_origem} => {nome_destino}")
        separador()
        
        # Cabeçalho da tabela
        print(f"{'ALGORITMO':<30} {'TEMPO(s)':<10} {'NÓS EXP.':<10} {'CAMINHO':<10} {'CUSTO(km)':<12} {'MEMÓRIA(B)':<12}")
        separador()

        # Dados de cada algoritmo
        for nome_alg, _ in lista_algoritmos:
            r = resultados[par][nome_alg]
            
            # Formatação dos valores
            tempo = f"{r['tempo_medio']:.4f}" if not np.isnan(r['tempo_medio']) else "N/A"
            nos = f"{r['nos_medio']:.1f}" if not np.isnan(r['nos_medio']) else "N/A"
            tamanho = f"{r['tamanho_medio']:.1f}" if not np.isnan(r['tamanho_medio']) else "N/A"
            custo = f"{r['custo_medio']:.0f}" if not np.isnan(r['custo_medio']) else "N/A"
            memoria = f"{r['mem_medio']:.0f}" if not np.isnan(r['mem_medio']) else "N/A"

            print(f"{nome_alg.upper():<30} {tempo:<10} {nos:<10} {tamanho:<10} {custo:<12} {memoria:<12}")
            print(f"Caminho encontrado: {r['caminho_final'] if r['caminho_final'] else 'N/A'}")
            separador(True)

# Pares de aeroportos atualizados para o novo dataset
pares_conectados = [
    ('GRU', 'HND'),  # Rota principal Guarulhos -> Tóquio
    ('GIG', 'NRT'),  # Rio de Janeiro -> Tóquio
    ('GRU', 'DXB'),  # Guarulhos -> Dubai
    ('DOH', 'IST'),  # Doha -> Istambul
    ('DOH', 'HND')   # Doha -> Tóquio
]

print("Pares de aeroportos usados:", pares_conectados)

# Execução da análise
lista_algoritmos = [('dijkstra', dijkstra_medido), ('a_estrela', a_estrela_medido), ('busca_gulosa', busca_gulosa_medido), ('busca_profundidade', busca_profundidade_medido), ('busca_largura', busca_largura_medido)]
resultados, rodadas = {}, 5
for par in pares_conectados:
    resultados[par] = {}
    for nome_alg, funcao in lista_algoritmos:
        print(f"Medindo {nome_alg} para {par}...")
        resultados[par][nome_alg] = medir_algoritmo(funcao, grafo_voos, par[0], par[1], rodadas=rodadas)

# Salvar resultados em CSV
linhas = []
for par in pares_conectados:
    for nome_alg, _ in lista_algoritmos:
        r = resultados[par][nome_alg]
        linha = {'par': f"{par[0]}->{par[1]}", 'algoritmo': nome_alg}
        linha.update(r)
        linhas.append(linha)
df_resultados = pd.DataFrame(linhas)
df_resultados.to_csv("resultados_metricas.csv", index=False)
print("Resultados salvos em resultados_metricas.csv")

# Imprimir métricas organizadas no console
imprimir_metricas_organizadas(resultados, pares_conectados, lista_algoritmos)

# Visualizar grafo com pyvis
rede = Network(notebook=True, height="800px", width="100%", bgcolor="#222222", font_color="white")
for aeroporto in grafo_voos.keys():
    legenda = legendas_aeroportos.get(aeroporto, aeroporto)
    rede.add_node(aeroporto, label=aeroporto, title=legenda)

for origem, destinos in grafo_voos.items():
    for destino, distancia in destinos.items():
        # Evitar adicionar arestas duplicadas na visualização
        if origem < destino:
            legenda_aresta = f"{legendas_aeroportos.get(origem, origem)} ---- {legendas_aeroportos.get(destino, destino)} ({distancia:.0f} km)"
            rede.add_edge(origem, destino, value=distancia, title=legenda_aresta)

rede.show_buttons(filter_=['physics'])
rede.save_graph("grafo_aeroportos.html")

print("O arquivo grafo_aeroportos.html foi salvo.")
