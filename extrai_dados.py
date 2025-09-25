import csv

# Script para extrair dados de aeroportos e rotas, e gerar um CSV com coordenadas
def _carregar_mapa_aeroportos(arq_aeroportos, iata_alvo):
    mapa_aeroportos = {}
    try:
        with open(arq_aeroportos, 'r', encoding='utf-8') as f_aeroportos:
            leitor = csv.reader(f_aeroportos)
            for linha in leitor:
                if len(linha) > 4 and linha[4] in iata_alvo:
                    iata = linha[4]
                    mapa_aeroportos[iata] = {
                        "lat": float(linha[6]),
                        "lon": float(linha[7])
                    }
        print(f"Mapeamento de {len(mapa_aeroportos)} aeroportos concluído.")
        print(f"Exemplo: {list(mapa_aeroportos.items())[0]}")

        return mapa_aeroportos
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{arq_aeroportos}' não encontrado.")
        return None

# Escreve o cabeçalho do CSV de saída
def _escrever_cabecalho_csv(escritor_csv):
    cabecalho = [
        'origin_iata', 'destination_iata', 
        'origin_lat', 'origin_lon', 
        'destination_lat', 'destination_lon'
    ]
    escritor_csv.writerow(cabecalho)

# Processa uma linha de rota e escreve no CSV se esta for válida
def _processar_linha_rota(linha, mapa_aeroportos, arestas_unicas, escritor_csv):
    if len(linha) < 5:
        return False
    
    source_iata = linha[2]
    dest_iata = linha[4]

    if source_iata in mapa_aeroportos and dest_iata in mapa_aeroportos:
        
        # Cria uma tupla ordenada para evitar duplicatas
        # Exemplo: A rota JFK->GRU é a mesma que GRU->JFK
        aresta = tuple(sorted((source_iata, dest_iata)))
        if aresta not in arestas_unicas:
            
            # Buscar as coordenadas no mapa
            origem_coords = mapa_aeroportos[source_iata]
            destino_coords = mapa_aeroportos[dest_iata]

            # Montar a linha para o novo CSV
            linha_saida = [
                source_iata,
                dest_iata,
                origem_coords['lat'],
                origem_coords['lon'],
                destino_coords['lat'],
                destino_coords['lon']
            ]

            escritor_csv.writerow(linha_saida)
            arestas_unicas.add(aresta)
            return True
    return False

# Processa o arquivo de rotas e gera o CSV de saída
def _processar_rotas(arq_rotas, arq_saida, mapa_aeroportos):
    rotas_processadas = 0
    try:
        with open(arq_rotas, 'r', encoding='utf-8') as f_rotas, \
             open(arq_saida, 'w', newline='', encoding='utf-8') as f_saida:
            
            leitor_rotas = csv.reader(f_rotas)
            escritor_csv = csv.writer(f_saida)

            _escrever_cabecalho_csv(escritor_csv)
            
            # Conjunto para evitar escrever arestas duplicadas (ex: GRU->JFK e JFK->GRU)
            arestas_unicas = set()

            # Processar cada linha do arquivo de rotas
            for linha in leitor_rotas:
                if _processar_linha_rota(linha, mapa_aeroportos, arestas_unicas, escritor_csv):
                    rotas_processadas += 1


        print(f"Processamento concluído. {rotas_processadas} rotas únicas foram salvas em '{arq_saida}'.")
        return rotas_processadas

    except FileNotFoundError:
        print(f"ERRO: Arquivo '{arq_rotas}' não encontrado.")
        return 0

def gerar_csv_com_coordenadas(arq_aeroportos, arq_rotas, arq_saida):
    # 1. Definir os nós (aeroportos) do nosso grafo
    iata_alvo = {
        "GRU", "GIG", "JFK", "LAX", "CDG", "FRA",
        "AMS", "DXB", "DOH", "IST", "HND", "NRT"
    }
    
    # 2. Carregar mapeamento de aeroportos
    mapa_aeroportos = _carregar_mapa_aeroportos(arq_aeroportos, iata_alvo)
    if mapa_aeroportos is None:
        return

    # 3. Processar rotas e gerar CSV
    _processar_rotas(arq_rotas, arq_saida, mapa_aeroportos)

if __name__ == "__main__":
    gerar_csv_com_coordenadas(
        arq_aeroportos="_airports.dat",
        arq_rotas="_routes.dat",
        arq_saida="rotas_com_coordenadas.csv"
    )
