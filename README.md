# Utilização de Grafos na Definição de Pontos Estratégicos de Monitoramento Urbano em Russas-CE

Este repositório reúne os códigos, os dados e os resultados computacionais do Trabalho de Conclusão de Curso **“Utilização de Grafos na Definição de Pontos Estratégicos de Monitoramento Urbano no Centro da Cidade de Russas-CE”**.

A rede urbana foi modelada como um grafo não direcionado e não ponderado. Os vértices representam interseções, extremidades e pontos de conexão entre vias, enquanto as arestas representam segmentos de ruas e caminhos públicos de pedestres.

O projeto inclui:

- obtenção e preparação de dados do OpenStreetMap;
- validação da conectividade com Busca em Largura (BFS);
- aplicação de uma heurística gulosa para Cobertura de Vértices;
- comparação com a aproximação disponível no NetworkX;
- obtenção da solução ótima por programação inteira com SciPy/HiGHS;
- avaliação de escalabilidade em grafos sintéticos em grade.


## Área de estudo

A área analisada corresponde a uma região do centro comercial de Russas, no Ceará, situada entre a Praça da Igreja Matriz e o Mercado Novo.

O polígono da área de estudo está armazenado em `dados/area_estudo_russas_nova.kmz` e apresenta aproximadamente:

- 0,137 km² de área;
- 13,72 hectares;
- 1,49 km de perímetro;
- latitudes entre 4,935947° S e 4,940783° S;
- longitudes entre 37,971483° O e 37,976152° O.

## Dados utilizados

Os dados da rede urbana foram obtidos do [OpenStreetMap](https://www.openstreetmap.org/) em 24 de agosto de 2026, por meio da biblioteca OSMnx.

A rede bruta utilizada nos experimentos está preservada em:

```text
dados/rede_osm_bruta.graphml
```

Esse arquivo deve ser utilizado para reproduzir os resultados do TCC. Como o OpenStreetMap é atualizado continuamente, uma nova coleta pode gerar uma rede diferente.

## Tecnologias

- Python 3.13.5;
- OSMnx 2.1.1;
- NetworkX 3.6.1;
- Matplotlib 3.10.8;
- SciPy 1.18.1;
- GeoPandas 1.1.4;
- HiGHS, utilizado pelo SciPy na solução do modelo de programação inteira.

As versões completas das dependências estão registradas em `requirements.txt`.

## Estrutura do repositório

```text
tcc_grafos_russas/
├── dados/
│   ├── area_estudo_russas_nova.kmz
│   └── rede_osm_bruta.graphml
├── resultados/
│   ├── comparacao_metodos_referencia.csv
│   ├── comparacao_metodos_referencia.txt
│   ├── heuristica_cobertura_vertices.png
│   ├── mapa_vertices_numerados.png
│   ├── numeracao_vertices.csv
│   ├── rede_osm_ajustada.graphml
│   ├── rede_osm_ajustada.png
│   ├── rede_osm_bruta.png
│   ├── rede_osm_topologica.graphml
│   ├── rede_osm_topologica.png
│   ├── resultado_escalabilidade_referencias.csv
│   ├── resultado_escalabilidade_referencias.txt
│   ├── resultado_heuristica.csv
│   ├── resultado_heuristica.txt
│   └── validacao_rede.txt
├── scripts/
│   ├── 01_verificar_area.py
│   ├── 02_coletar_rede.py
│   ├── 03_visualizar_rede.py
│   ├── 04_preparar_topologia.py
│   ├── 05_consolidar_araujo_lima.py
│   ├── 06_validar_rede_bfs.py
│   ├── 07_aplicar_heuristica.py
│   ├── 08_comparar_metodos_referencia.py
│   ├── 09_gerar_mapa_vertices_numerados.py
│   ├── 10_escalabilidade_metodos_referencia.py
│   ├── algoritmos_cobertura.py
│   └── utilitarios_vertices.py
├── .gitignore
├── README.md
└── requirements.txt
```

## Preparação do ambiente

Abra o PowerShell na pasta do projeto e execute:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Quando o ambiente estiver ativo, o terminal apresentará `(.venv)` no início da linha.

## Reprodução dos resultados

Para reproduzir os resultados com a rede bruta preservada, execute os scripts a partir da raiz do projeto:

```powershell
python scripts\01_verificar_area.py
python scripts\03_visualizar_rede.py
python scripts\04_preparar_topologia.py
python scripts\05_consolidar_araujo_lima.py
python scripts\06_validar_rede_bfs.py
python scripts\07_aplicar_heuristica.py
python scripts\08_comparar_metodos_referencia.py
python scripts\09_gerar_mapa_vertices_numerados.py
python scripts\10_escalabilidade_metodos_referencia.py
```

> [!IMPORTANT]
> O script `02_coletar_rede.py` não deve ser executado para reproduzir exatamente os resultados do TCC. Ele realiza uma nova consulta ao OpenStreetMap e substitui `dados/rede_osm_bruta.graphml`.

## Função dos scripts

| Script | Função |
|---|---|
| `01_verificar_area.py` | Valida o polígono e calcula área, perímetro e limites geográficos. |
| `02_coletar_rede.py` | Realiza uma nova coleta no OpenStreetMap. Seu uso é opcional. |
| `03_visualizar_rede.py` | Gera a imagem da rede bruta preservada. |
| `04_preparar_topologia.py` | Mantém os caminhos de pedestres relevantes, remove elementos pontuais de acessibilidade e simplifica a rede. |
| `05_consolidar_araujo_lima.py` | Consolida a Avenida Coronel Araújo Lima e produz o grafo final. |
| `06_validar_rede_bfs.py` | Verifica a estrutura do grafo e sua conectividade com BFS. |
| `07_aplicar_heuristica.py` | Executa a heurística gulosa de Cobertura de Vértices. |
| `08_comparar_metodos_referencia.py` | Compara a heurística com o NetworkX e a solução exata do SciPy/HiGHS. |
| `09_gerar_mapa_vertices_numerados.py` | Numera os vértices e destaca a solução da heurística. |
| `10_escalabilidade_metodos_referencia.py` | Avalia os métodos em grafos sintéticos de diferentes tamanhos. |
| `algoritmos_cobertura.py` | Reúne as implementações compartilhadas pelos experimentos. |
| `utilitarios_vertices.py` | Padroniza a numeração geográfica dos vértices. |

## Preparação topológica

Na preparação da rede:

- a Travessa Afonso Lima e dois becos públicos destinados a pedestres foram mantidos;
- duas passagens pontuais de acessibilidade que não representam vias independentes foram removidas;
- nós intermediários sem relevância topológica foram simplificados;
- a Avenida Coronel Araújo Lima foi consolidada em uma única via;
- a Avenida Don Lino permaneceu representada por duas pistas devido ao canteiro central.

A rede bruta possui 56 vértices e 122 arestas direcionadas. Após a preparação topológica, passou a possuir 38 vértices e 90 arestas direcionadas. O grafo final não direcionado possui 26 vértices e 37 arestas.

## Resultados principais

### Validação do grafo

| Medida | Resultado |
|---|---:|
| Vértices | 26 |
| Arestas | 37 |
| Componentes conexas | 1 |
| Vértices isolados | 0 |
| Laços | 0 |
| Arestas paralelas | 0 |
| Grau mínimo | 2 |
| Grau máximo | 4 |
| Grau médio | 2,85 |
| Vértices visitados pelo BFS | 26 |

### Comparação das soluções

| Método | Vértices selecionados | Diferença para o ótimo | Razão em relação ao ótimo |
|---|---:|---:|---:|
| Heurística proposta | 14 | 0 | 1,0000 |
| Aproximação do NetworkX | 23 | 9 | 1,6429 |
| Solução exata SciPy/HiGHS | 14 | 0 | 1,0000 |

A heurística encontrou uma solução ótima para o grafo da área de estudo. O SciPy/HiGHS confirmou valor objetivo 14, diferença de otimalidade igual a zero e status de solução ótima.

Os 14 vértices selecionados pela heurística foram:

```text
V02, V04, V06, V07, V08, V09, V10,
V15, V16, V18, V19, V20, V23, V24
```

Todas as 37 arestas foram cobertas, correspondendo a 100% de cobertura. A solução exata pode selecionar um conjunto diferente com a mesma quantidade de vértices, pois podem existir múltiplas coberturas mínimas.

### Escalabilidade em grafos sintéticos

| Grade | Vértices | Arestas | Heurística | NetworkX | Solução ótima |
|---|---:|---:|---:|---:|---:|
| 5 × 5 | 25 | 40 | 13 | 24 | 12 |
| 7 × 7 | 49 | 84 | 25 | 48 | 24 |
| 10 × 10 | 100 | 180 | 50 | 99 | 50 |
| 15 × 15 | 225 | 420 | 113 | 224 | 112 |
| 20 × 20 | 400 | 760 | 200 | 399 | 200 |

Os tempos variam conforme o equipamento. As medições completas estão disponíveis em `comparacao_metodos_referencia.csv` e `resultado_escalabilidade_referencias.csv`.

## Numeração dos vértices

Os rótulos de `V01` a `V26` são gerados de maneira determinística a partir das coordenadas geográficas, seguindo a ordem do norte para o sul e, em seguida, do oeste para o leste. O identificador interno é utilizado como último critério de desempate.

Essa regra está centralizada em `scripts/utilitarios_vertices.py`, garantindo que relatórios, arquivos CSV e imagens utilizem a mesma numeração.

## Limitações

O modelo possui foco topológico. Portanto:

- não considera o sentido de circulação das vias;
- não modela alcance, orientação ou campo de visão das câmeras;
- não considera obstáculos físicos, como árvores, postes e edificações;
- não utiliza dados de criminalidade ou fluxo de pessoas e veículos;
- não determina a quantidade física de câmeras necessária em cada ponto;
- representa a cobertura das arestas do grafo, e não a cobertura visual real do espaço urbano.

Os vértices selecionados devem ser interpretados como pontos candidatos ao monitoramento e ainda necessitam de avaliação técnica em campo.