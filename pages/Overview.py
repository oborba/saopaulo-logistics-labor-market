import streamlit as st
import utils
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import numpy as np

st.set_page_config(layout="centered")

def main():
    st.title('Panorama geral da categoria')

    df = utils.load_data()

    # Filter for heavy vehicle drivers
    heavy_categories = ['C', 'D', 'E', 'AC', 'AD', 'AE']
    heavy_drivers_df = df[df['categoria_cnh'].isin(heavy_categories)]

    total_heavy_drivers = heavy_drivers_df['qtd_condutores'].sum()
    ear_heavy_drivers = heavy_drivers_df[heavy_drivers_df['exerce_atividade_remunerada'] == 'S']['qtd_condutores'].sum()
    
    # Calculations for the third metric's helper
    age_group_counts = heavy_drivers_df.groupby('faixa_etaria')['qtd_condutores'].sum().sort_values(ascending=False)
    predominant_age_group = age_group_counts.index[0]
    predominant_age_group_count = age_group_counts.iloc[0]
    predominant_age_group_percentage = (predominant_age_group_count / total_heavy_drivers) * 100
    
    helper_faixa_etaria = f'{predominant_age_group_count:,} condutores, que representam {predominant_age_group_percentage:.2f}% da categoria, com ou sem EAR'

    st.header('Indicadores chave')

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label='Motoristas de pesados (C, D ou E)', value=f'{total_heavy_drivers:,}', help='Incluindo as combinações AC, AD e AE')

    with col2:
        st.metric(label='Motoristas de pesados com EAR', value=f'{ear_heavy_drivers:,}', help='Exerce Atividade Remunerada - Quem de fato está trabalhando no setor')

    with col3:
        st.metric(label='Faixa etária predominante', value=predominant_age_group, help=helper_faixa_etaria)
    
    st.divider()
    
    st.header('Onde estão esses profissionais?')
    st.subheader('Uma visão sobre a distribuição da força de trabalho ativa do estado')

    ear_heavy_drivers_df = heavy_drivers_df[heavy_drivers_df['exerce_atividade_remunerada'] == 'S']
    
    heatmap_data = ear_heavy_drivers_df.groupby(['descricao_municipio', 'lat', 'lon'])['qtd_condutores'].sum().reset_index()
    heatmap_data.dropna(subset=['lat', 'lon'], inplace=True)

    map_center = [-22.5, -48.5]
    m = folium.Map(location=map_center, zoom_start=7, tiles='CartoDB positron', scrollWheelZoom=False)

    heat_data = [[row['lat'], row['lon'], np.log1p(row['qtd_condutores'])] for index, row in heatmap_data.iterrows()]

    HeatMap(heat_data).add_to(m)

    st_folium(m, use_container_width=True)

if __name__ == '__main__':
    main()
