import pandas as pd
import streamlit as st
import plotly.express as px
from utils import load_data

st.title('O Gargalo Profissional: Além da Habilitação')
st.markdown('### Analisando o descompasso entre a qualificação feminina e a ocupação real no mercado de transporte.')

df = load_data()

# --- PROCESSAMENTO DE DADOS ---

# 1. Filtro de Categorias (C, D, E)
heavy_filter = df['categoria_cnh'].str.contains('C|D|E', regex=True)
df_heavy = df[heavy_filter].copy()

# 2. Agrupamento Profissional
df_grouped = (
    df_heavy.groupby(['genero', 'exerce_atividade_remunerada'])['qtd_condutores']
    .sum()
    .reset_index()
)

# 3. Cálculo de Ativação e Métricas
# Pivotar: Index=Genero, Cols=EAR (S/N)
df_pivot = df_grouped.pivot(
    index='genero', columns='exerce_atividade_remunerada', values='qtd_condutores'
).fillna(0)

# Garantir colunas S e N
for col in ['S', 'N']:
    if col not in df_pivot.columns:
        df_pivot[col] = 0

df_pivot['Total'] = df_pivot['S'] + df_pivot['N']
df_pivot['Taxa_Ativacao'] = (df_pivot['S'] / df_pivot['Total']) * 100

# Extração de valores para KPIs
try:
    total_mulheres_cde = df_pivot.loc['FEMININO', 'Total']
    reserva_feminina = df_pivot.loc['FEMININO', 'N']
    ativacao_fem = df_pivot.loc['FEMININO', 'Taxa_Ativacao']
except KeyError:
    total_mulheres_cde = 0
    reserva_feminina = 0
    ativacao_fem = 0

try:
    ativacao_masc = df_pivot.loc['MASCULINO', 'Taxa_Ativacao']
except KeyError:
    ativacao_masc = 0

gap_insercao = ativacao_masc - ativacao_fem

# --- INTERFACE (KPIs) ---

col1, col2, col3 = st.columns(3)
col1.metric('Total de Mulheres Habilitadas (CDE)', f'{total_mulheres_cde:,.0f}'.replace(',', '.'))
col2.metric('Reserva de Talento Feminino', f'{reserva_feminina:,.0f}'.replace(',', '.'))
col3.metric('Diferença de Inserção', f'{gap_insercao:.1f} p.p.')

# --- GRÁFICO PRINCIPAL ---

df_chart = df_pivot.reset_index()
# Filtrar apenas M/F para visualização limpa
df_chart = df_chart[df_chart['genero'].isin(['MASCULINO', 'FEMININO'])]

fig = px.bar(
    df_chart,
    x='genero',
    y='Taxa_Ativacao',
    title='Taxa de Ativação Profissional por Gênero',
    color='genero',
    color_discrete_map={'MASCULINO': '#2c3e50', 'FEMININO': '#884EA0'},
    barmode='group',
    text_auto='.1f',
)
fig.update_layout(yaxis_range=[0, 100], yaxis_title='% com Atividade Remunerada (EAR)')
st.plotly_chart(fig, use_container_width=True)

# --- STORYTELLING ---

st.info(
    'Para obter uma CNH profissional (C, D ou E), o condutor realiza um alto investimento de tempo e dinheiro. '
    'No entanto, os dados revelam que possuir a habilitação não garante a entrada no mercado. '
    'A taxa de ativação feminina é significativamente menor que a masculina, indicando a existência de barreiras '
    'invisíveis de contratação ou falta de infraestrutura que impeça o aproveitamento de mais de 70 mil talentos '
    'femininos já qualificados em São Paulo.'
)

# --- SEÇÃO: MAPA DA OPORTUNIDADE ---

st.divider()
st.markdown('## Mapa da Oportunidade: Onde está a Reserva Feminina?')
st.markdown('Identificação geográfica dos maiores polos de mulheres qualificadas aguardando inserção.')

# 1. Filtro de Público Alvo: Mulheres, CNH Pesada, Sem EAR
df_reserve = df_heavy[
    (df_heavy['genero'] == 'FEMININO') & (df_heavy['exerce_atividade_remunerada'] == 'N')
].copy()

# 2. Agrupamento por Município
df_map_reserve = (
    df_reserve.groupby(['descricao_municipio', 'lat', 'lon'])['qtd_condutores']
    .sum()
    .reset_index()
)

# 3. Ranking Top 10
df_top10 = df_map_reserve.sort_values(by='qtd_condutores', ascending=False).head(10)

col_map, col_rank = st.columns([2, 1])

with col_map:
    fig_map = px.scatter_mapbox(
        df_map_reserve,
        lat='lat',
        lon='lon',
        size='qtd_condutores',
        hover_name='descricao_municipio',
        hover_data={'lat': False, 'lon': False, 'qtd_condutores': True},
        zoom=6,
        mapbox_style='carto-positron',
    )
    fig_map.update_layout(margin={'r': 0, 't': 0, 'l': 0, 'b': 0})
    st.plotly_chart(fig_map, use_container_width=True)

with col_rank:
    fig_rank = px.bar(
        df_top10,
        x='qtd_condutores',
        y='descricao_municipio',
        orientation='h',
        title='Top 10 Municípios',
        text_auto=True,
    )
    # categoryorder='total ascending' coloca o maior valor no topo do eixo Y
    fig_rank.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_rank, use_container_width=True)

st.success(
    'Conclusão da Análise: A alta concentração de talentos em polos industriais e logísticos '
    '(como São Paulo e Campinas) indica que a escassez de motoristas pode ser mitigada sem a '
    'necessidade de grandes deslocamentos migratórios. O talento já está presente nos grandes centros; '
    'o desafio reside na criação de políticas de contratação que tornem o ambiente atrativo e seguro '
    'para estas profissionais.'
)

# --- SEÇÃO: FOCO NA ESPECIALIZAÇÃO ---

st.divider()
st.markdown('## Foco na especialização')
st.markdown('### Onde está a maior reserva técnica? Analisando a qualificação por categoria.')

# 1. Filtro: Apenas Mulheres (já temos df_heavy filtrado por C, D, E)
df_women = df_heavy[df_heavy['genero'] == 'FEMININO'].copy()

# 2. Definição de Grupos de Categoria (Hierarquia E > D > C)
def categorize_license(cat):
    if 'E' in cat:
        return 'Categoria E (Articulados)'
    elif 'D' in cat:
        return 'Categoria D (Passageiros)'
    elif 'C' in cat:
        return 'Categoria C (Caminhão)'
    return 'Outros'

df_women['grupo_categoria'] = df_women['categoria_cnh'].apply(categorize_license)

# 3. Agrupamento
df_spec = (
    df_women.groupby(['grupo_categoria', 'exerce_atividade_remunerada'])['qtd_condutores']
    .sum()
    .reset_index()
)

# 4. Ajuste de Labels para o Gráfico
df_spec['exerce_atividade_remunerada'] = df_spec['exerce_atividade_remunerada'].map({
    'S': 'Com EAR (Ativa)',
    'N': 'Sem EAR (Reserva)'
})

# 5. Gráfico
fig_spec = px.bar(
    df_spec,
    x='grupo_categoria',
    y='qtd_condutores',
    color='exerce_atividade_remunerada',
    title='Distribuição de Mulheres por Categoria e Atividade Remunerada',
    labels={'qtd_condutores': 'Quantidade de Condutoras', 'grupo_categoria': 'Categoria'},
    color_discrete_map={'Com EAR (Ativa)': '#2c3e50', 'Sem EAR (Reserva)': '#884EA0'},
    text_auto=True
)

st.plotly_chart(fig_spec, use_container_width=True)

st.info(
    '💡 **O que os dados nos dizem?**\n\n'
    'Enquanto a Categoria D é um exemplo consolidado de inserção feminina e a Cat. E mostra que a especialização garante o emprego, '
    'a Categoria C revela um "gigante adormecido": 92% das habilitadas não exercem atividade remunerada. '
    'Por que esse talento está parado? Vamos investigar a faixa etária dessas condutoras para entender se o gargalo é geracional ou de início de carreira.'
)

# --- SEÇÃO: MERGULHO NA CATEGORIA C ---

st.divider()
st.markdown('## 🕵️‍♀️ Mergulho na Categoria C: Quem é essa reserva?')

# 1. Filtro: Mulheres, Categoria C (Grupo), Sem EAR
# Utilizamos o 'grupo_categoria' criado na seção anterior para manter a consistência dos dados
df_cat_c_reserve = df_women[
    (df_women['grupo_categoria'] == 'Categoria C (Caminhão)') &
    (df_women['exerce_atividade_remunerada'] == 'N')
].copy()

# 2. Agrupamento Etário
df_c_age = (
    df_cat_c_reserve.groupby('faixa_etaria')['qtd_condutores']
    .sum()
    .reset_index()
)

# 3. Ordenação Lógica das Faixas Etárias
age_order = [
    '18-21 ANOS', '22-25 ANOS', '26-30 ANOS', '31-40 ANOS',
    '41-50 ANOS', '51-60 ANOS', '61-70 ANOS', '71-80 ANOS',
    '81-90 ANOS', '91-100 ANOS'
]
df_c_age['faixa_etaria'] = pd.Categorical(
    df_c_age['faixa_etaria'], categories=age_order, ordered=True
)
df_c_age = df_c_age.sort_values('faixa_etaria')

# 4. Visualização
fig_c_age = px.bar(
    df_c_age,
    x='faixa_etaria',
    y='qtd_condutores',
    title='Distribuição Etária da Reserva Técnica (Categoria C)',
    labels={'qtd_condutores': 'Quantidade de Condutoras', 'faixa_etaria': 'Faixa Etária'},
    color_discrete_sequence=['#D35400'],  # Cor de destaque (Abóbora/Bronze)
    text_auto=True
)
fig_c_age.update_layout(xaxis_tickangle=-45)

st.plotly_chart(fig_c_age, use_container_width=True)