import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import load_data
import folium
import branca.colormap as cm
from streamlit_folium import st_folium
import numpy as np

st.title('Apagão Logístico')

df = load_data()

#
# --- BLOCO 1: O ALERTA (HEADLINE) ---
#

# 1. Filtro de Escopo (Categorias Pesadas: C, D, E)
# Regex captura qualquer categoria que contenha C, D ou E (ex: AC, AD, AE)
df_alert = df[df['categoria_cnh'].str.contains('C|D|E', regex=True)]

# 2. Cálculo de Grupos (Novos Entrantes vs Veteranos)
new_entrants_ages = ['18-21 ANOS', '22-25 ANOS', '26-30 ANOS']
veterans_ages = ['51-60 ANOS', '61-70 ANOS']

count_new_entrants = df_alert[df_alert['faixa_etaria'].isin(new_entrants_ages)]['qtd_condutores'].sum()
count_veterans = df_alert[df_alert['faixa_etaria'].isin(veterans_ages)]['qtd_condutores'].sum()

# 3. Cálculo do Índice de Reposição
# Evita divisão por zero
replacement_index = count_new_entrants / count_veterans if count_veterans > 0 else 0.0

# 4. UI: Headline e Alerta
st.markdown('### 🚨 Alerta: Envelhecimento da Mão de Obra')

st.metric(
    label="Índice de Reposição de Motoristas",
    value=f"{replacement_index:.2f}",
    delta=f"{replacement_index - 1.0:.2f} (Déficit)" if replacement_index < 1.0 else f"+{replacement_index - 1.0:.2f}",
    help="Razão entre Novos Entrantes (18-30 anos) e Veteranos (51-70 anos). Valores abaixo de 1.0 indicam retração da força de trabalho."
)

# Texto Sociológico com estilização de alerta
alert_msg = (
    f"**Análise Crítica:** Para cada 1 motorista veterano (51-70 anos) próximo da aposentadoria, o mercado repõe apenas **{replacement_index:.2f}** novos condutores.\n\n"
    f"**Base de Comparação:** O cálculo confronta **{f'{count_veterans:,.0f}'.replace(',', '.')}** veteranos (51-70 anos) contra apenas **{f'{count_new_entrants:,.0f}'.replace(',', '.')}** novos entrantes (18-30 anos).\n\n"
    "Como incentivar os jovens a entrar no setor?"
)

if replacement_index < 0.5:
    st.error(alert_msg, icon="⚠️")
else:
    st.warning(alert_msg, icon="⚠️")

st.divider()

#
# --- BLOCO 2: O GAP DE SUBSTITUIÇÃO (TORNADO CHART) ---
#

with st.container():
    st.subheader("O Abismo Geracional")

    # 1. Definição dos Grupos Etários
    young_ages = ['18-21 ANOS', '22-25 ANOS', '26-30 ANOS']
    vet_ages = ['51-60 ANOS', '61-70 ANOS']

    # Normalização de Categorias (Agrupamento Visual)
    def normalize_category(cat):
        if 'E' in cat: return 'Categoria E'
        if 'D' in cat: return 'Categoria D'
        if 'C' in cat: return 'Categoria C'
        return cat

    df_chart = df_alert.copy()
    df_chart['categoria_agrupada'] = df_chart['categoria_cnh'].apply(normalize_category)

    # 2. Agrupamento de Dados (Pandas)
    # Novos Entrantes (18-30)
    df_young = df_chart[df_chart['faixa_etaria'].isin(young_ages)].groupby('categoria_agrupada')['qtd_condutores'].sum().reset_index()
    df_young.rename(columns={'qtd_condutores': 'Novos Entrantes', 'categoria_agrupada': 'categoria_cnh'}, inplace=True)

    # Veteranos (51-70)
    df_vet = df_chart[df_chart['faixa_etaria'].isin(vet_ages)].groupby('categoria_agrupada')['qtd_condutores'].sum().reset_index()
    df_vet.rename(columns={'qtd_condutores': 'Veteranos', 'categoria_agrupada': 'categoria_cnh'}, inplace=True)

    # Merge e Ordenação
    df_tornado = pd.merge(df_vet, df_young, on='categoria_cnh', how='outer').fillna(0)
    df_tornado = df_tornado.sort_values('Veteranos', ascending=True)

    # 3. Preparação para o Gráfico Divergente (Inversão de Sinal)
    df_tornado['Veteranos_Neg'] = df_tornado['Veteranos'] * -1

    # 4. Construção do Gráfico (Plotly Graph Objects)
    fig = go.Figure()

    # Lado Esquerdo: Veteranos
    fig.add_trace(go.Bar(
        y=df_tornado['categoria_cnh'],
        x=df_tornado['Veteranos_Neg'],
        orientation='h',
        name='Veteranos (Saída)',
        marker_color='#2c3e50',  # Azul Escuro/Cinza
        customdata=df_tornado['Veteranos'],
        hovertemplate='%{y}: <b>%{customdata:,.0f}</b> Veteranos<extra></extra>',
        text=[f'{x:,.0f}'.replace(',', '.') for x in df_tornado['Veteranos']],
        textposition='auto'
    ))

    # Lado Direito: Novos Entrantes
    fig.add_trace(go.Bar(
        y=df_tornado['categoria_cnh'],
        x=df_tornado['Novos Entrantes'],
        orientation='h',
        name='Novos Entrantes (Entrada)',
        marker_color='#FF5733',  # Laranja/Coral
        hovertemplate='%{y}: <b>%{x:,.0f}</b> Novos<extra></extra>',
        text=[f'{x:,.0f}'.replace(',', '.') for x in df_tornado['Novos Entrantes']],
        textposition='outside'
    ))

    # Layout e Eixos Absolutos
    max_x = max(df_tornado['Veteranos'].max(), df_tornado['Novos Entrantes'].max()) * 1.1
    
    fig.update_layout(
        title='O Abismo Geracional: Veteranos vs. Novos Entrantes',
        barmode='overlay',
        xaxis=dict(
            title='Quantidade de Condutores',
            range=[-max_x, max_x],
            tickmode='array',
            tickvals=[-max_x, -max_x/2, 0, max_x/2, max_x],
            ticktext=[f'{abs(x):,.0f}'.replace(',', '.') for x in [-max_x, -max_x/2, 0, max_x/2, max_x]]
        ),
        yaxis=dict(title='Categoria CNH'),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor='center'),
        height=500,
        hovermode='y unified', # Added for touch UX
        margin=dict(l=20, r=20, t=80, b=20) # Added for touch UX
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption("Nota: A barra da esquerda representa a força de trabalho que se aposentará nos próximos 10-15 anos, enquanto a direita representa a renovação disponível. A escala dos veteranos é drasticamente superior.")

st.divider()

#
# --- BLOCO 3: ANÁLISE DE ATIVIDADE EAR (LOCAL VS PROFISSIONAL) ---
#

with st.container():
    st.subheader("Vocação Profissional: Quem realmente dirige?")
    st.markdown("Análise da proporção de condutores habilitados que efetivamente possuem a observação **EAR (Exerce Atividade Remunerada)** na CNH.")

    # 1. Preparação dos Dados
    # Agrupamento por idade e status de EAR
    df_ear = df_alert.groupby(['faixa_etaria', 'exerce_atividade_remunerada'])['qtd_condutores'].sum().reset_index()

    # 2. Ordenação Cronológica (Crucial para o Eixo X)
    age_order = [
        '18-21 ANOS', '22-25 ANOS', '26-30 ANOS', '31-40 ANOS',
        '41-50 ANOS', '51-60 ANOS', '61-70 ANOS', '71-80 ANOS',
        '81-90 ANOS', '91-100 ANOS'
    ]
    
    # Mapeamento de Labels para Legenda
    df_ear['Status'] = df_ear['exerce_atividade_remunerada'].map({'S': 'Profissional (EAR)', 'N': 'Apenas Habilitado'})

    # 3. Preparação para Gráfico Combinado (Barras + Linha)
    # Pivotar para calcular % de conversão
    df_pivot = df_ear.pivot(index='faixa_etaria', columns='Status', values='qtd_condutores').fillna(0).reset_index()
    
    # Garantir existência das colunas (caso algum grupo não tenha dados)
    for col in ['Profissional (EAR)', 'Apenas Habilitado']:
        if col not in df_pivot.columns: df_pivot[col] = 0
        
    df_pivot['Total'] = df_pivot['Profissional (EAR)'] + df_pivot['Apenas Habilitado']
    df_pivot['Pct_EAR'] = (df_pivot['Profissional (EAR)'] / df_pivot['Total']) * 100
    
    # Ordenação Categórica
    df_pivot['faixa_etaria'] = pd.Categorical(df_pivot['faixa_etaria'], categories=age_order, ordered=True)
    df_pivot = df_pivot.sort_values('faixa_etaria')

    # Construção do Gráfico Dual Axis
    fig_ear = go.Figure()

    # Barra Única (Volume Total)
    fig_ear.add_trace(go.Bar(
        x=df_pivot['faixa_etaria'], y=df_pivot['Total'],
        name='Total de Condutores', marker_color='#2c3e50'
    ))

    # Linha de Percentual (Eixo Secundário)
    fig_ear.add_trace(go.Scatter(
        x=df_pivot['faixa_etaria'], y=df_pivot['Pct_EAR'],
        name='% Conversão EAR', yaxis='y2',
        mode='lines+markers+text',
        line=dict(color='#D50000', width=3), # Vermelho para destaque
        text=[f'{x:.0f}%' for x in df_pivot['Pct_EAR']],
        textposition='top center',
        hovertemplate='&#37; Conversão EAR: <b>%{y:.0f}%</b><extra></extra>'
    ))
    
    fig_ear.update_layout(
        title='Conversão Profissional: Volume vs Taxa de Atividade',
        xaxis=dict(title='Faixa Etária', tickangle=-45),
        yaxis=dict(title='Quantidade de Condutores'),
        yaxis2=dict(
            title='% Conversão EAR', overlaying='y', side='right',
            range=[0, 115], showgrid=False
        ),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor='center'),
        height=500,
        hovermode='x unified', # Added for touch UX
        margin=dict(l=20, r=20, t=80, b=100) # Added for touch UX
    )

    st.plotly_chart(fig_ear, use_container_width=True)
    st.info("💡 **Insight:** Note como a taxa de conversão (Linha Vermelha) tende a se manter alta nas faixas centrais, mas a base total de condutores jovens é drasticamente menor.")

#
# --- BLOCO 4: TABELA DE RISCO REGIONAL ---
#

with st.container():
    st.divider()
    st.subheader("📍 Mapa de Risco: Onde o Apagão é Iminente?")
    st.markdown("Identifique os municípios com a maior idade média da frota de condutores pesados.")

    # 1. Lógica de Cálculo da Idade Média Ponderada
    age_midpoints = {
        '18-21 ANOS': 19.5, '22-25 ANOS': 23.5, '26-30 ANOS': 28.0,
        '31-40 ANOS': 35.5, '41-50 ANOS': 45.5, '51-60 ANOS': 55.5,
        '61-70 ANOS': 65.5, '71-80 ANOS': 75.5, '81-90 ANOS': 85.5,
        '91-100 ANOS': 95.5, 'MAIOR DE 100 ANOS': 100.0
    }

    df_risk = df_alert.copy()
    df_risk['idade_media_faixa'] = df_risk['faixa_etaria'].map(age_midpoints)
    
    # Cálculo Ponderado: (Idade * Qtd)
    df_risk['soma_ponderada'] = df_risk['idade_media_faixa'] * df_risk['qtd_condutores']

    # Agrupamento por Município
    df_city_risk = df_risk.groupby('descricao_municipio').agg(
        Total_Condutores=('qtd_condutores', 'sum'),
        Soma_Ponderada=('soma_ponderada', 'sum')
    ).reset_index()

    # Idade Média Final
    df_city_risk['Idade_Media'] = df_city_risk['Soma_Ponderada'] / df_city_risk['Total_Condutores']
    df_city_risk['Status_Risco'] = df_city_risk['Idade_Media'].apply(lambda x: '🚨 Crítico' if x > 50 else '⚠️ Atenção' if x > 45 else '✅ Estável')

    # 2. UI Interativa (Default: Top 10, Opcional: Comparação)
    df_city_risk = df_city_risk.sort_values('Idade_Media', ascending=False)

    compare_mode = st.toggle("Quero comparar municípios específicos")

    if compare_mode:
        selected_cities = st.multiselect(
            "Selecione os municípios para comparar",
            options=sorted(df_city_risk['descricao_municipio'].unique()),
            default=[]
        )
        # Show dataframe only if cities are selected
        if selected_cities:
            df_display = df_city_risk[df_city_risk['descricao_municipio'].isin(selected_cities)]
            st.dataframe(
                df_display[['descricao_municipio', 'Total_Condutores', 'Idade_Media', 'Status_Risco']],
                column_config={
                    "descricao_municipio": "Município",
                    "Total_Condutores": st.column_config.NumberColumn("Total CNH (C/D/E)", format="%d"),
                    "Idade_Media": st.column_config.ProgressColumn(
                        "Idade Média (Anos)",
                        format="%.1f",
                        min_value=df_city_risk['Idade_Media'].min(),
                        max_value=df_city_risk['Idade_Media'].max(),
                    ),
                    "Status_Risco": "Nível de Alerta"
                },
                use_container_width=True,
                hide_index=True
            )
    else:
        with st.expander("🏆 Top 10 Municípios por Idade Média de Motoristas", expanded=True):
            top_10_cities = df_city_risk.head(10)
            
            # Helper para criar colunas dinamicamente e evitar erro se houver menos de 10 cidades
            num_cities = len(top_10_cities)
            if num_cities > 0:
                # Create 2 rows of 5 columns for the top 10
                st.write("Top 1-5")
                cols_1 = st.columns(5)
                for i in range(min(5, num_cities)):
                    row = top_10_cities.iloc[i]
                    cols_1[i].metric(
                        label=f"{i + 1}. {row['descricao_municipio']}",
                        value=f"{row['Idade_Media']:.1f} anos",
                        help=f"Total de motoristas: {row['Total_Condutores']}"
                    )
                
                if num_cities > 5:
                    st.write("Top 6-10")
                    cols_2 = st.columns(5)
                    for i in range(5, num_cities):
                        row = top_10_cities.iloc[i]
                        cols_2[i-5].metric(
                            label=f"{i + 1}. {row['descricao_municipio']}",
                            value=f"{row['Idade_Media']:.1f} anos",
                            help=f"Total de motoristas: {row['Total_Condutores']}"
                        )
            else:
                st.write("Nenhum dado de cidade para exibir.")

# 1. DATA PREPARATION (Recalculating with Lat/Lon)

# Reuse df_alert (C, D, E filtered)
# Define midpoints (same as block above)
df_map_age = df_alert.copy()
df_map_age['idade_media_faixa'] = df_map_age['faixa_etaria'].map(age_midpoints)
df_map_age['soma_ponderada'] = df_map_age['idade_media_faixa'] * df_map_age['qtd_condutores']

# Group by City AND Lat/Lon
df_city_age = df_map_age.groupby(['descricao_municipio', 'lat', 'lon']).agg(
    total_pesados=('qtd_condutores', 'sum'),
    soma_ponderada=('soma_ponderada', 'sum')
).reset_index()

df_city_age['idade_media'] = df_city_age['soma_ponderada'] / df_city_age['total_pesados']

# 2. MAP CONFIGURATION

risk_map = folium.Map(
    location=[-22.5, -48.5],
    zoom_start=7,
    tiles='cartodbpositron',  # 'Clean' style (light gray) to highlight heatmap colors
    scrollWheelZoom=False # Disable scroll wheel zoom for mobile optimization
)

# Color Scale: Green (<40) -> Yellow (45) -> Red (>50)
colormap = cm.LinearColormap(
    colors=['#00FF00', '#FFFF00', '#FF0000'],
    index=[40, 45, 50],
    vmin=40,
    vmax=50,
    caption='Idade Média dos Motoristas (Anos)',
)
risk_map.add_child(colormap)

# 3. CIRCLE PLOTTING

for _, row in df_city_age.iterrows():
    # Visual filter: Shows only cities with minimal relevance (e.g., > 50 heavy drivers)
    if row['total_pesados'] > 50:
        # Size: Log to control visual scale
        radius = np.log1p(row['total_pesados']) * 1.8

        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=radius,
            color=None,
            fill=True,
            fill_color=colormap(row['idade_media']),
            fill_opacity=0.8,
            popup=folium.Popup(
                f"""
                <b>{row['descricao_municipio']}</b><br>
                Frota Pesada: {int(row['total_pesados']):,}<br>
                Idade Média: {row['idade_media']:.1f} anos
            """,
                max_width=200,
            ),
            tooltip=f'{row["descricao_municipio"]}: {row["idade_media"]:.1f} anos (média)',
        ).add_to(risk_map)

st_folium(risk_map, width=None, height=500, use_container_width=True)

st.divider()
st.header("🚀 O Caminho Adiante: Recomendações Estratégicas")

# CSS para estilização dos cards
st.markdown("""
<style>
    .consulting-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #e6e9ef;
        height: 100%; /* Default for desktop */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
    }
    .consulting-card h4 {
        color: #0e1117;
        font-weight: 700;
        margin-bottom: 10px;
        padding-bottom: 5px;
        border-bottom: 2px solid #ff4b4b;
    }
    .consulting-card p {
        font-size: 1rem;
        color: #31333F;
        flex-grow: 1;
    }

    /* Media query for mobile devices */
    @media (max-width: 768px) {
        .consulting-card {
            height: auto; /* Override for mobile */
            margin-bottom: 1rem; /* Add space between stacked cards */
        }
    }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="consulting-card">
        <h4>🎯 Gestão de Talentos</h4>
        <p>Diante do índice de <b>{replacement_index:.2f}</b>, é urgente a criação de programas de 'Jovem Aprendiz da Estrada'. Recomendamos o subsídio para a mudança de categoria (B para D/E) e parcerias com centros de formação para reduzir a barreira de entrada financeira da Geração Z.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="consulting-card">
        <h4>🏛️ Infraestrutura e Estado</h4>
        <p>O envelhecimento da frota exige estradas mais seguras e pontos de descanso dignos. Sugerimos incentivos fiscais para transportadoras que comprovem diversidade etária e programas de saúde focados no motorista sênior para prolongar sua vida profissional com qualidade.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="consulting-card">
        <h4>⚙️ Tecnologia Assistiva</h4>
        <p>Para atrair nativos digitais e apoiar veteranos, a frota deve investir em telemetria avançada e automação de nível 2. A tecnologia deve atuar como um redutor de esforço físico e um atrativo de modernidade para o setor.</p>
    </div>
    """, unsafe_allow_html=True)

st.info("A crise de mão de obra não é apenas falta de pessoas, é uma crise de atratividade. O dado é o diagnóstico; a ação é a cura.")