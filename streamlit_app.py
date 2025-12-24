import pandas as pd
import streamlit as st
import plotly.express as px
import folium
import branca.colormap as cm
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# Configuração da página (deve ser a primeira coisa no Streamlit)
st.set_page_config(
    page_title="Logistica Pesada SP",
    page_icon="🚗",
    layout="wide"
)

# Função para classificar (Business Logic)
def classificar_perfil(row):
    ear = row['exerce_atividade_remunerada']
    cat = row['categoria_cnh']
    
    if ear == 'N':
        return 'Amador'

    # Verifica se existe C, D ou E na string da categoria (ex: 'AC', 'AE')
    if any(pesada in cat for pesada in ['C', 'D', 'E']):
        return 'Logística Pesada/Tradicional'
    
    # Se tem EAR e não é pesada, assumimos leve
    if any(leve in cat for leve in ['A', 'B']): # Cobre A, B e AB
        return 'Gig Economy/Apps'
    
    return 'Outros'

@st.cache_data
def carregar_dados():
    df = pd.read_csv('condutores_habilitados_ativos_incrementado.csv', sep=',')

    # Removemos condutores acima de 100 anos (estatisticamente improvável estarem ativos profissionalmente)
    df = df[~df['faixa_etaria'].isin(['101-120 ANOS', '+120 ANOS'])]

    df['tipo_atuacao'] = df.apply(classificar_perfil, axis=1)
    
    return df

def main():
    st.title("Panaroma de condutores C, D e E em São Paulo")
    st.markdown("Uma visão analítica sobre condutores da logistica pesada no estado.")

    df = carregar_dados()

    # 
    # --- CÁLCULO DE MÉTRICAS (KPIs) ---
    # Linha de valores gerais
    # 

    # 1. Total Geral
    total_condutores = df['qtd_condutores'].sum()

    # 2. Total EAR (Atividade Remunerada)
    # Filtramos onde EAR é 'S' e somamos a quantidade
    total_ear = df[df['exerce_atividade_remunerada'] == 'S']['qtd_condutores'].sum()
    pct_ear = (total_ear / total_condutores) * 100

    # 3. Total Categorias Pesadas (C, D, E e combinações)
    # Usamos string method para achar quem contém C, D ou E
    filtro_pesados = df['categoria_cnh'].str.contains('C|D|E', regex=True)
    total_pesados = df[filtro_pesados]['qtd_condutores'].sum()
    pct_pesados = (total_pesados / total_condutores) * 100

    # Cria 3 colunas para os cartões de métricas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total de Condutores", 
            value=f"{total_condutores:,.0f}".replace(",", "."),
            help="Incluindo Motos, Carros de passeio e Pesados"
        )

    with col2:
        st.metric(
            label="Exercem Atividade Remunerada", 
            value=f"{total_ear:,.0f}".replace(",", "."),
            help=f"Condutores com EAR, necessário para qualquer categoria",
        )
        st.caption(f"ℹ️ {pct_ear:.1f}% do total de condutores")

    with col3:
        st.metric(
            label="Habilitação Pesada (C, D, E)", 
            value=f"{total_pesados:,.0f}".replace(",", "."),
            help=f"Condutores que podem dirigir veículos pesados",
        )
        st.caption(f"ℹ️ {pct_pesados:.1f}% do total de condutores")

    # ==============================================================================
    # SEÇÃO: PAINEL DE LOGÍSTICA E TRANSPORTE PROFISSIONAL
    # ==============================================================================
    
    st.divider()
    st.subheader("🚚 Motoristas de pesados (C, D e E)")
    st.markdown("""
    Seguimos uma hierarquia, onde quem tem a categoria E, acumula as permissões de B, C e D. A categoria 'A' não segue essa lógica, sendo uma permissão diferente.
    * **Grupo E:** Carretas e Articulados (Carga Pesada).
    * **Grupo D:** Ônibus e Vans (Passageiros).
    * **Grupo C:** Caminhões (Carga Média/Urbana).
    """)

    # 1. PREPARAÇÃO DOS DADOS (O "Backend" da análise)
    # Filtramos apenas quem tem C, D ou E
    df_pesados = df[df['categoria_cnh'].str.contains('C|D|E', regex=True)].copy()

    # Criamos uma coluna auxiliar de HIERARQUIA para os gráficos ficarem limpos
    # Se tem E, é E. Se não tem E mas tem D, é D. Se só tem C, é C.
    def definir_grupo_logistico(cat):
        if 'E' in cat: return 'Grupo E (Articulados)'
        if 'D' in cat: return 'Grupo D (Passageiros)'
        if 'C' in cat: return 'Grupo C (Caminhão)'
        return 'Outros'

    df_pesados['grupo_logistico'] = df_pesados['categoria_cnh'].apply(definir_grupo_logistico)

    # --- LINHA 1: RESUMO EXECUTIVO (CARDS) ---
    
    # KPI 1: Profissionais Ativos (Pesados + EAR Sim)
    total_profissionais = df_pesados[df_pesados['exerce_atividade_remunerada'] == 'S']['qtd_condutores'].sum()

    # KPI 2: Topo da Pirâmide (Qualquer categoria que contenha E)
    total_cat_E = df_pesados[df_pesados['grupo_logistico'] == 'Grupo E (Articulados)']['qtd_condutores'].sum()
    
    # KPI 3: Diversidade (% Mulheres na frota pesada)
    total_pesados_geral = df_pesados['qtd_condutores'].sum()
    total_mulheres_pesado = df_pesados[df_pesados['genero'] == 'FEMININO']['qtd_condutores'].sum()
    pct_mulheres = (total_mulheres_pesado / total_pesados_geral) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Motoristas de pesados com EAR", f"{total_profissionais:,.0f}".replace(",", "."))
    col2.metric("Topo da Pirâmide (Grupo E)", f"{total_cat_E:,.0f}".replace(",", "."))
    with col3:
        st.metric(
            label="Mulheres na Logística", 
            value=f"{total_mulheres_pesado:,.0f}",
        )
        st.caption(f"ℹ️ {pct_mulheres:.2f}% do setor")

    # --- LINHA 2: DISTRIBUIÇÃO E ESPECIALIDADE ---
    
    st.divider()
    st.subheader("📊 Motoristas Ativos e Reserva Técnica")
    
    # 1. CRIAÇÃO DO FILTRO (WIDGET)
    # Pegamos as faixas únicas e ordenamos para ficar bonito no selectbox
    # Adicionamos a opção 'Todas' no início da lista
    opcoes_idade = sorted(df_pesados['faixa_etaria'].unique().tolist())
    opcoes_idade.insert(0, "Todas")
    
    # O st.selectbox retorna a string escolhida pelo usuário
    faixa_selecionada = st.selectbox(
        "Filtrar análise por Faixa Etária:", 
        options=opcoes_idade,
        index=0 # Padrão: Todas
    )

    # 2. APLICAÇÃO DO FILTRO (Lógica de Backend)
    if faixa_selecionada == "Todas":
        df_charts = df_pesados # Usa o dataframe completo
        texto_apoio = "Visualizando **toda a base** de condutores pesados."
    else:
        # Filtra apenas a faixa escolhida
        df_charts = df_pesados[df_pesados['faixa_etaria'] == faixa_selecionada]
        texto_apoio = f"Visualizando apenas condutores entre **{faixa_selecionada}**."

    st.caption(texto_apoio)

    # 3. GERAÇÃO DOS GRÁFICOS (Baseado no df_charts filtrado)
    c_left, c_right = st.columns(2)

    with c_left:
        # Gráfico de Pizza: Composição por Grupo Logístico
        # Importante: O groupby agora é feito no df_charts (filtrado)
        df_pizza = df_charts.groupby('grupo_logistico')['qtd_condutores'].sum().reset_index()
        
        # Tratamento de erro: Caso o filtro não retorne dados (ex: faixa etária vazia para Categoria E)
        if not df_pizza.empty:
            fig_pizza = px.pie(
                df_pizza, 
                values='qtd_condutores', 
                names='grupo_logistico',
                title=f'Distribuição ({faixa_selecionada})',
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.warning("Não há dados para esta combinação.")

    with c_right:
        # Gráfico de Barras: EAR vs Não-EAR por Grupo
        df_barras = df_charts.groupby(['grupo_logistico', 'exerce_atividade_remunerada'])['qtd_condutores'].sum().reset_index()
        
        if not df_barras.empty:
            df_barras['exerce_atividade_remunerada'] = df_barras['exerce_atividade_remunerada'].map({'S': 'Profissional (EAR)', 'N': 'Sem EAR'})
            
            fig_barras = px.bar(
                df_barras, 
                x='grupo_logistico', 
                y='qtd_condutores', 
                color='exerce_atividade_remunerada',
                title=f'Profissionais vs Reserva ({faixa_selecionada})',
                barmode='group',
                text_auto='.2s'
            )
            st.plotly_chart(fig_barras, use_container_width=True)
        else:
            st.warning("Não há dados para esta combinação.")

    # ==============================================================================
    # LINHA 3: INTELIGÊNCIA REGIONAL (BUSCÁVEL)
    # ==============================================================================
    
    st.divider()
    st.subheader("📍 Onde estão esses profissionais?")

    st.markdown("""
    Visualização geoespacial da concentração de motoristas profissionais de carga e transporte (Categorias C, D, E).
    Usado normalização Logarítmica para a capital não ofuscar o restante do mapa
    """)

    # 1. FILTRAGEM DE DADOS (Business Rule)
    # Apenas EAR = Sim E Categorias Pesadas
    filtro_mapa = (
        (df['exerce_atividade_remunerada'] == 'S') & 
        (df['categoria_cnh'].str.contains('C|D|E', regex=True))
    )

    # Criamos um DF limpo apenas com o necessário para o mapa
    # Agrupamos por Município/Lat/Lon para somar a quantidade total naquela cidade
    df_mapa = df[filtro_mapa].groupby(['descricao_municipio', 'lat', 'lon'])['qtd_condutores'].sum().reset_index()

    # Normalização Logarítmica (Opcional, mas recomendado)
    # SP Capital tem tantos motoristas que "apaga" o resto do estado se usarmos o valor bruto.
    # Para visualização, o Log ajuda a ver hubs médios (como Ribeirão Preto ou Campinas).
    # Se preferir bruto, use: df_mapa['weight'] = df_mapa['qtd_condutores']
    import numpy as np
    df_mapa['weight'] = np.log1p(df_mapa['qtd_condutores']) 

    # normalizamos entre 0 e 1 para o Folium entender melhor a intensidade
    df_mapa['weight'] = df_mapa['weight'] / df_mapa['weight'].max()

    # 2. CONFIGURAÇÃO DO MAPA BASE (FOLIUM)
    # Coordenadas médias do Estado de SP para centralizar a câmera
    mapa_sp = folium.Map(
        location=[-22.1, -48.9], # Centro aproximado de SP
        zoom_start=7,
        tiles="cartodbpositron" # Estilo 'Clean' (cinza claro) para destacar as cores do heatmap
    )

    # 3. CRIAÇÃO DA CAMADA DE CALOR (HEATMAP)
    # O Folium espera uma lista de listas: [Lat, Lon, Peso]
    dados_heatmap = df_mapa[['lat', 'lon', 'weight']].values.tolist()

    HeatMap(
        dados_heatmap,
        radius=15,       # Tamanho da "mancha" de cada ponto
        blur=20,         # O quanto a mancha se espalha (suavidade)
        min_opacity=0.3, # Transparência mínima
        gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'} # Gradiente de cor
    ).add_to(mapa_sp)

    # Adicionar Tooltips (Opcional: Círculos invisíveis para mostrar nome da cidade ao passar o mouse)
    for _, row in df_mapa.iterrows():
        folium.Circle(
            location=[row['lat'], row['lon']],
            radius=row['qtd_condutores'] * 0.05, # Raio proporcional (ajuste o multiplicador conforme necessidade)
            color=None, # Invisível
            fill=False,
            tooltip=f"{row['descricao_municipio']}: {row['qtd_condutores']:,.0f} motoristas"
        ).add_to(mapa_sp)

    # 4. RENDERIZAÇÃO NO STREAMLIT
    # st_folium é o componente que conecta o Folium ao Streamlit
    st_folium(mapa_sp, width=None, height=500, use_container_width=True)

    st.info("💡 **Análise:** Note como a mancha vermelha segue as principais rodovias (Anhanguera/Bandeirantes e Dutra).")




    st.markdown("Pesquise sua cidade abaixo para entender a vocação logística da sua região.")

    # Função Helper para renderizar tabelas com busca
    # Como você é Senior, sabe que DRY (Don't Repeat Yourself) é vida.
    def renderizar_ranking(df_source, grupo_filtro, titulo, key_sulfix):
        
        # 1. Preparação dos dados (Agrupamento e Ordenação)
        # Filtra pelo grupo logístico desejado
        df_filtered = df_source[df_source['grupo_logistico'] == grupo_filtro]
        
        # Agrupa por cidade e soma
        df_rank = df_filtered.groupby('descricao_municipio')[['qtd_condutores']].sum()
        
        # Ordena do maior para o menor
        df_rank = df_rank.sort_values(by='qtd_condutores', ascending=False).reset_index()
        
        # Renomeia colunas para ficar bonito na UI
        df_rank.columns = ['Município', 'Total Condutores']

        # 2. Interface de Busca
        st.markdown(f"**{titulo}**")
        
        # O 'key' deve ser único para cada widget no Streamlit, senão dá conflito
        search_term = st.text_input(f"🔍 Buscar cidade ({titulo})", key=f"search_{key_sulfix}")

        # 3. Filtragem Dinâmica
        if search_term:
            # Filtro case-insensitive
            mask = df_rank['Município'].str.contains(search_term.upper(), na=False)
            df_display = df_rank[mask]
        else:
            df_display = df_rank

        # 4. Renderização da Tabela
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True, # Esconde o índice numérico (0, 1, 2...)
            height=300, # Define uma altura fixa com scroll
            column_config={
                "Município": st.column_config.TextColumn("Cidade"),
                "Total Condutores": st.column_config.NumberColumn(
                    "Qtd. Habilitados",
                    format="%d", # Formatação inteira
                )
            }
        )

    # Layout em duas colunas
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        # Chama a função para o Grupo E (Carga Pesada)
        renderizar_ranking(
            df_pesados, 
            'Grupo E (Articulados)', 
            "🚛 Gigantes das Estradas (Grupo E)", 
            "grupo_e"
        )

    with col_b:
        # Chama a função para o Grupo D (Passageiros)
        renderizar_ranking(
            df_pesados, 
            'Grupo D (Passageiros)', 
            "🚌 Mestres do Transporte (Grupo D)", 
            "grupo_d"
        )

    with col_c:
        # Chama a função para o Grupo C (Carga leve)
        renderizar_ranking(
            df_pesados, 
            'Grupo C (Caminhão)', 
            "🚚 Mestres da Distribuição (Grupo C)", 
            "grupo_c"
        )

    # ==============================================================================
    # LINHA 4: DEMOGRAFIA LOGÍSTICA (TESE DO APAGÃO) - SIMPLIFICADO
    # ==============================================================================
    
    st.divider()
    st.header("⚡ Possível Apagão Logístico")
    st.markdown("""
    Análise da distribuição etária dos motoristas de pesados.
    A hipótese é que a força de trabalho está concentrada em faixas etárias mais altas.
    """)

    # 1. PREPARAÇÃO DOS DADOS
    
    # Definindo a ORDEM CRONOLÓGICA manualmente.
    # Isso é CRUCIAL para os gráficos não ficarem em ordem alfabética (ex: 18 depois de 100).
    # Ajuste as strings exatamente como estão no seu CSV.
    ordem_faixas = [
        '18-21 ANOS', 
        '22-25 ANOS', 
        '26-30 ANOS', 
        '31-40 ANOS', 
        '41-50 ANOS', 
        '51-60 ANOS', 
        '61-70 ANOS', 
        '71-80 ANOS', 
        '81-90 ANOS', 
        '91-100 ANOS'
    ]

    # Filtrar apenas Categorias Pesadas (C, D, E)
    filtro_pesado = (df['categoria_cnh'].str.contains('C|D|E', regex=True))
    df_pesados_total = df[filtro_pesado].copy() # Inclui EAR Sim e Não
    
    # Dataset específico para Profissionais (EAR = Sim)
    df_pesados_ear = df_pesados_total[df_pesados_total['exerce_atividade_remunerada'] == 'S'].copy()

    # --- KPI CARDS DE RISCO E RENOVAÇÃO ---
    
    total_profissionais_pesados = df_pesados_ear['qtd_condutores'].sum()
    
    # Definição de grupos (Adapte as listas se necessário)
    faixas_jovens = ['18-21 ANOS', '22-25 ANOS', '26-30 ANOS'] 
    faixas_seniores = ['61-70 ANOS', '71-80 ANOS', '81-90 ANOS', '91-100 ANOS']

    qtd_jovens = df_pesados_ear[df_pesados_ear['faixa_etaria'].isin(faixas_jovens)]['qtd_condutores'].sum()
    qtd_seniores = df_pesados_ear[df_pesados_ear['faixa_etaria'].isin(faixas_seniores)]['qtd_condutores'].sum()

    pct_jovens = (qtd_jovens / total_profissionais_pesados) * 100
    pct_seniores = (qtd_seniores / total_profissionais_pesados) * 100

    # Exibição dos Cards
    c1, c2 = st.columns(2)
    
    with c1:
        st.metric(
            label="👴 Risco de Aposentadoria (60+)", 
            value=f"{pct_seniores:.1f}%",
        )
        st.caption(f"{qtd_seniores:,.0f} condutores".replace(",", "."))
    
    with c2:
        st.metric(
            label="👶 Taxa de Renovação (18-30)", 
            value=f"{pct_jovens:.1f}%",
        )
        st.caption(f"{qtd_jovens:,.0f} condutores".replace(",", "."))       

    # --- O MURO DEMOGRÁFICO (Gráfico de Barras Empilhadas) ---
    st.subheader("Distribuição Etária")
    
    # Agrupamento por Faixa e EAR
    df_chart_bar = df_pesados_total.groupby(['faixa_etaria', 'exerce_atividade_remunerada'])['qtd_condutores'].sum().reset_index()
    
    # Aplica a ordenação categórica
    df_chart_bar['faixa_etaria'] = pd.Categorical(
        df_chart_bar['faixa_etaria'], 
        categories=ordem_faixas, 
        ordered=True
    )
    df_chart_bar = df_chart_bar.sort_values('faixa_etaria')
    
    # Renomear Legenda para ficar amigável
    df_chart_bar['exerce_atividade_remunerada'] = df_chart_bar['exerce_atividade_remunerada'].map(
        {'S': 'Profissional Ativo', 'N': 'Reserva (Sem EAR)'}
    )

    fig_wall = px.bar(
        df_chart_bar,
        x='faixa_etaria',
        y='qtd_condutores',
        color='exerce_atividade_remunerada',
        title='Volume de Condutores Pesados por Idade',
        # Cores contrastantes: Laranja forte para Ativos, Azul suave para Reserva
        color_discrete_map={'Profissional Ativo': '#EF553B', 'Reserva (Sem EAR)': '#636EFA'}, 
        barmode='stack'
    )
    st.plotly_chart(fig_wall, use_container_width=True)

    # --- GRÁFICO DO PENHASCO DEMOGRÁFICO ---
    st.divider()
    st.subheader("A Escolha dos Jovens")
    st.markdown("""
    Comparativo direto entre profissionais (EAR) de categorias **Leves (B/AB)** contra **Pesadas (C/D/E)**.
    Os jovens estão optando pela flexibilidade (e menor barreira de entrada) dos aplicativos em vez da carreira de motorista profissional tradicional?
    """)

    # 1. Preparar os dados (Apenas quem tem EAR)
    df_ear = df[df['exerce_atividade_remunerada'] == 'S'].copy()

    # 2. Definir os grupos (Leves vs Pesados)
    def classificar_penhasco(cat):
        # Se tiver C, D ou E é Pesado
        if any(x in cat for x in ['C', 'D', 'E']):
            return 'Pesadas (C, D, E)'
        # Se for A, B ou AB é Leve (Apps/Motos)
        # Nota: Incluímos A e AB pois também fazem parte da "Gig Economy" (Motoboys/Uber)
        elif cat in ['B', 'AB', 'A']: 
            return 'Leves (A, B, AB)'
        return 'Outros'

    df_ear['grupo_comparativo'] = df_ear['categoria_cnh'].apply(classificar_penhasco)

    # Filtrar fora "Outros" e agrupar
    df_penhasco = df_ear[df_ear['grupo_comparativo'] != 'Outros']
    df_chart_cliff = df_penhasco.groupby(['faixa_etaria', 'grupo_comparativo'])['qtd_condutores'].sum().reset_index()

    # 3. Ordenação (Crucial: Usar a lista ordem_faixas definida anteriormente)
    df_chart_cliff['faixa_etaria'] = pd.Categorical(
        df_chart_cliff['faixa_etaria'],
        categories=ordem_faixas,
        ordered=True
    )
    df_chart_cliff = df_chart_cliff.sort_values('faixa_etaria')

    # 4. O Gráfico (Side-by-Side)
    fig_cliff = px.bar(
        df_chart_cliff,
        x='faixa_etaria',
        y='qtd_condutores',
        color='grupo_comparativo',
        barmode='group', # Importante: Coloca as barras lado a lado, não empilhadas
        title='Apps vs Tradicional',
        labels={'qtd_condutores': 'Qtd. Motoristas Profissionais', 'faixa_etaria': 'Idade'},
        # Cores: Verde (Tech/Apps) vs Laranja/Vermelho (Tradicional/Alerta)
        color_discrete_map={
            'Leves (A, B, AB)': '#00CC96', 
            'Pesadas (C, D, E)': '#EF553B'
        }
    )
    
    # Ajustes finos de layout
    fig_cliff.update_layout(xaxis_tickangle=-45) # Inclina o texto do eixo X se ficar apertado
    
    st.plotly_chart(fig_cliff, use_container_width=True)
    
    # Análise automática (Texto dinâmico)
    # Pegamos o pico de cada grupo para comentar
    pico_leve = df_chart_cliff[df_chart_cliff['grupo_comparativo'] == 'Leves (A, B, AB)'].sort_values('qtd_condutores', ascending=False).iloc[0]['faixa_etaria']
    pico_pesado = df_chart_cliff[df_chart_cliff['grupo_comparativo'] == 'Pesadas (C, D, E)'].sort_values('qtd_condutores', ascending=False).iloc[0]['faixa_etaria']

    # ==============================================================================
    # SEÇÃO: Risco Demográfico Logístico (Scatter Map Filtrado)
    # ==============================================================================

    st.divider()
    st.subheader("👴 Onde os Caminhoneiros estão Envelhecendo?")
    st.markdown("""
    **Risco de Apagão Local (Apenas Carga e Transporte Pesado):**
    * **Tamanho do Círculo:** Volume de motoristas profissionais (C, D, E).
    * **Cor do Círculo:** Porcentagem destes motoristas que já têm **60 anos ou mais**.
    * **Vermelho:** >20% da frota tem mais de 60 anos.
    * **Amarelo:** >10% e <20% da frota tem mais de 60 anos
    * **Verde:** <10% da frota tem mais de 60 anos.
    """)

    # 1. FILTRAGEM RIGOROSA (O "Pulo do Gato")
    # Primeiro, isolamos apenas o universo de Logística Pesada
    # Isso garante que não estamos contando jovens de moto/carro na estatística
    filtro_pesados = df['categoria_cnh'].str.contains('C|D|E', regex=True)
    df_mapa_target = df[filtro_pesados].copy()

    # 2. PREPARAÇÃO DOS DADOS

    # Faixas de Risco (60+)
    faixas_60_plus = [
        '61-70 ANOS', '71-80 ANOS', '81-90 ANOS', 
        '91-100 ANOS', 'MAIOR DE 100 ANOS' # Ajuste conforme seu unique()
    ]

    # Agrupamento Base: Total de Motoristas PESADOS por cidade
    df_city_total = df_mapa_target.groupby(['descricao_municipio', 'lat', 'lon'])['qtd_condutores'].sum().reset_index()
    df_city_total.rename(columns={'qtd_condutores': 'total_pesados'}, inplace=True)

    # Agrupamento Risco: Total de Motoristas PESADOS 60+ por cidade
    df_idosos = df_mapa_target[df_mapa_target['faixa_etaria'].isin(faixas_60_plus)].groupby('descricao_municipio')['qtd_condutores'].sum().reset_index()
    df_idosos.rename(columns={'qtd_condutores': 'total_60_plus'}, inplace=True)

    # Merge (Left Join para garantir que cidades sem idosos não sumam, fiquem com 0)
    df_scatter = pd.merge(df_city_total, df_idosos, on='descricao_municipio', how='left')
    df_scatter['total_60_plus'] = df_scatter['total_60_plus'].fillna(0)

    # Cálculo da Porcentagem de Risco
    # (Total Idosos Pesados / Total Pesados da Cidade)
    df_scatter['pct_risco'] = (df_scatter['total_60_plus'] / df_scatter['total_pesados']) * 100

    # 3. CONFIGURAÇÃO DO MAPA

    mapa_risco = folium.Map(
        location=[-22.5, -48.5], 
        zoom_start=7,
        tiles="cartodbdark_matter" # Fundo escuro para destacar o vermelho/verde
    )

    # Escala de Cores: Verde (0%) -> Amarelo (15%) -> Vermelho (30%)
    # Aumentei a régua para 30% pois o setor de transporte já é naturalmente mais velho.
    colormap = cm.LinearColormap(
        colors=['#00FF00', '#FFFF00', '#FF0000'], 
        index=[0, 15, 30], 
        vmin=0, 
        vmax=30,
        caption='% de Caminhoneiros/Motoristas 60+'
    )
    mapa_risco.add_child(colormap)

    # 4. PLOTAGEM DOS CÍRCULOS

    for _, row in df_scatter.iterrows():
        # Filtro visual: Mostra apenas cidades com relevância mínima (ex: > 50 motoristas pesados)
        if row['total_pesados'] > 50:
            
            # Tamanho: Log para controlar a escala visual
            raio = np.log1p(row['total_pesados']) * 1.8
            
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=raio,
                color=None,
                fill=True,
                fill_color=colormap(row['pct_risco']), # A cor agora reflete o envelhecimento DO SETOR
                fill_opacity=0.8,
                popup=folium.Popup(f"""
                    <b>{row['descricao_municipio']}</b><br>
                    Frota Pesada: {int(row['total_pesados']):,}<br>
                    Idosos (60+): {row['pct_risco']:.1f}%
                """, max_width=200),
                tooltip=f"{row['descricao_municipio']}: {row['pct_risco']:.1f}% em risco"
            ).add_to(mapa_risco)

    st_folium(mapa_risco, width=None, height=500, use_container_width=True)


if __name__ == "__main__":
    main()