import streamlit as st
import utils
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="centered")

def main():
    st.title('Panorama geral da categoria')

    df = utils.load_data()

    # Filter for heavy vehicle drivers
    heavy_categories = ['C', 'D', 'E', 'AC', 'AD', 'AE']
    heavy_drivers_df = df[df['categoria_cnh'].isin(heavy_categories)].copy()

    # Logic for categories (Pre-processing)
    def simplify_category(cat):
        if 'E' in cat: return 'E'
        if 'D' in cat: return 'D'
        return 'C'
    heavy_drivers_df['categoria_simple'] = heavy_drivers_df['categoria_cnh'].apply(simplify_category)

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
    
    # --- ROW 1.5: Blocked Drivers (New Section) ---
    st.subheader("Saúde da Frota e Disponibilidade Legal")
    
    blocked_count = heavy_drivers_df[heavy_drivers_df['condutor_bloqueado'] == 'S']['qtd_condutores'].sum()
    blocked_pct = (blocked_count / total_heavy_drivers) * 100
    active_count = total_heavy_drivers - blocked_count
    
    col_b1, col_b2 = st.columns([1, 2])
    
    with col_b1:
        st.metric(
            label="Condutores Bloqueados", 
            value=f"{blocked_count:,}", 
            delta=f"-{blocked_pct:.2f}% da frota",
            delta_color="inverse",
            help="Motoristas com CNH suspensa, cassada ou vencida (Impedidos de dirigir)"
        )
        st.caption(f"De um total de {total_heavy_drivers:,} condutores, apenas {active_count:,} estão aptos legalmente.")

    with col_b2:
        df_block = heavy_drivers_df.groupby(['categoria_simple', 'condutor_bloqueado'])['qtd_condutores'].sum().unstack(fill_value=0)
        # Ensure columns exist
        for c in ['S', 'N']:
            if c not in df_block.columns: df_block[c] = 0
            
        # Calculate percentages for text
        df_block['Total'] = df_block['S'] + df_block['N']
        df_block['Pct_Block'] = (df_block['S'] / df_block['Total']) * 100
        
        fig_block = go.Figure()
        fig_block.add_trace(go.Bar(y=df_block.index, x=df_block['N'], name='Ativos (Aptos)', orientation='h', marker_color='#2ecc71'))
        fig_block.add_trace(go.Bar(
            y=df_block.index, x=df_block['S'], name='Bloqueados', orientation='h', marker_color='#e74c3c',
            text=df_block['Pct_Block'].apply(lambda x: f"{x:.1f}%"), textposition='auto'
        ))
        fig_block.update_layout(title="Taxa de Bloqueio por Categoria", barmode='stack', margin=dict(t=30, b=20, l=20, r=20), height=250)
        st.plotly_chart(fig_block, use_container_width=True)

    # --- Blocked by Age Group ---
    st.markdown("##### Bloqueios por Faixa Etária")
    df_block_age = heavy_drivers_df[heavy_drivers_df['condutor_bloqueado'] == 'S'].groupby('faixa_etaria')['qtd_condutores'].sum().reset_index()
    
    fig_block_age = go.Figure(go.Bar(
        x=df_block_age['faixa_etaria'],
        y=df_block_age['qtd_condutores'],
        marker_color='#e74c3c',
        text=df_block_age['qtd_condutores'],
        textposition='auto',
        texttemplate='%{text:.2s}'
    ))
    fig_block_age.update_layout(
        title="Volume de Condutores Bloqueados por Idade",
        xaxis=dict(tickangle=-45),
        margin=dict(t=30, b=50, l=20, r=20),
        height=300
    )
    st.plotly_chart(fig_block_age, use_container_width=True)

    st.divider()

    # --- ROW 2: Category & Professionalization ---
    st.subheader("Perfil da Categoria e Profissionalização")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**Distribuição por Categoria**")
        df_cat = heavy_drivers_df.groupby('categoria_simple')['qtd_condutores'].sum().reset_index()
        fig_donut = go.Figure(data=[go.Pie(
            labels=df_cat['categoria_simple'], 
            values=df_cat['qtd_condutores'], 
            hole=.5,
            textinfo='label+percent',
            marker_colors=['#3498db', '#e74c3c', '#9b59b6']
        )])
        fig_donut.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            height=300
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with c2:
        st.markdown("**Penetração do EAR**")
        # Calculate EAR stats per category
        df_ear_stats = heavy_drivers_df.groupby(['categoria_simple', 'exerce_atividade_remunerada'])['qtd_condutores'].sum().unstack(fill_value=0)
        
        if 'S' in df_ear_stats.columns:
            df_ear_stats['Total'] = df_ear_stats.sum(axis=1)
            
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=df_ear_stats.index, 
                y=df_ear_stats['Total'],
                name='Total Habilitados',
                marker_color='#95a5a6'
            ))
            fig_bar.add_trace(go.Bar(
                x=df_ear_stats.index, 
                y=df_ear_stats['S'],
                name='Com EAR',
                marker_color='#2ecc71'
            ))
            fig_bar.update_layout(
                barmode='overlay',
                margin=dict(t=20, b=60, l=20, r=20),
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                height=300,
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            st.write("")
        else:
            st.warning("Dados de EAR não encontrados.")

    st.divider()

    # --- ROW 4: Top 10 Hubs ---
    st.subheader("Top 10 Polos Logísticos (Municípios)")
    
    city_counts = heavy_drivers_df.groupby('descricao_municipio')['qtd_condutores'].sum().sort_values(ascending=False)
    top_city_name = city_counts.index[0]
    top_city_val = city_counts.iloc[0]
    
    # Toggle to handle the outlier (São Paulo)
    include_outlier = st.toggle(f"Incluir {top_city_name} (Líder Absoluto)", value=False)
    
    if not include_outlier:
        st.metric(label=f"🥇 {top_city_name}", value=f"{top_city_val:,}", help="Este município foi separado do gráfico por ter uma escala muito superior aos demais, o que dificultaria a visualização.")
        # Select 2nd to 11th place
        top_cities = city_counts.iloc[1:11].sort_values(ascending=True)
    else:
        top_cities = city_counts.head(10).sort_values(ascending=True)

    # Prepare data for stacked bar chart (EAR vs Non-EAR)
    selected_cities = top_cities.index
    
    # Filter for selected cities and pivot by EAR status
    df_hubs = heavy_drivers_df[heavy_drivers_df['descricao_municipio'].isin(selected_cities)]
    df_pivot = df_hubs.groupby(['descricao_municipio', 'exerce_atividade_remunerada'])['qtd_condutores'].sum().unstack(fill_value=0)
    
    # Ensure 'S' and 'N' columns exist
    for col in ['S', 'N']:
        if col not in df_pivot.columns:
            df_pivot[col] = 0
            
    # Reindex to match the sorted order (ascending for plot display)
    df_pivot = df_pivot.reindex(selected_cities)

    fig_hubs = go.Figure()
    
    # Trace: Com EAR
    fig_hubs.add_trace(go.Bar(
        y=df_pivot.index,
        x=df_pivot['S'],
        name='Com EAR',
        orientation='h',
        marker_color='#2ecc71',
        text=df_pivot['S'],
        textposition='auto',
        texttemplate='%{text:.2s}'
    ))
    
    # Trace: Sem EAR
    fig_hubs.add_trace(go.Bar(
        y=df_pivot.index,
        x=df_pivot['N'],
        name='Sem EAR',
        orientation='h',
        marker_color='#95a5a6',
        text=df_pivot['N'],
        textposition='auto',
        texttemplate='%{text:.2s}'
    ))

    fig_hubs.update_layout(
        barmode='stack',
        margin=dict(t=20, b=20, l=20, r=20),
        height=400,
        xaxis=dict(showgrid=True),
        yaxis=dict(title=''),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_hubs, use_container_width=True)
    
    # --- ROW 5: Diversity ---
    st.divider()
    st.subheader("Diversidade e Inclusão")
    
    # Check columns existence to prevent errors
    has_sexo = 'genero' in heavy_drivers_df.columns
    pcd_col = 'pessoa_com_deficiencia'
    has_pcd = pcd_col in heavy_drivers_df.columns
    
    if has_sexo or has_pcd:
        tab_women, tab_pcd = st.tabs(["👩 Mulheres", "♿ PCD"])
        
        # --- TAB: WOMEN ---
        if has_sexo:
            with tab_women:
                women_df = heavy_drivers_df[heavy_drivers_df['genero'].isin(['MULHER', 'FEMININO', 'F'])]
                women_count = women_df['qtd_condutores'].sum()
                women_ear = women_df[women_df['exerce_atividade_remunerada'] == 'S']['qtd_condutores'].sum()
                women_ear_pct = (women_ear / women_count * 100) if women_count > 0 else 0
                
                st.metric("Mulheres Habilitadas", f"{women_count:,}", f"{women_ear_pct:.1f}% com EAR")
                
                # Comparison with Category B
                df_b = df[df['categoria_cnh'] == 'B']
                total_b = df_b['qtd_condutores'].sum()
                women_b = df_b[df_b['genero'].isin(['MULHER', 'FEMININO', 'F'])]['qtd_condutores'].sum()
                pct_women_b = (women_b / total_b * 100) if total_b > 0 else 0
                pct_women_heavy = (women_count / total_heavy_drivers * 100) if total_heavy_drivers > 0 else 0

                st.info(f"💡 **Disparidade de Gênero:** Enquanto na Categoria B (carros de passeio) as mulheres representam **{pct_women_b:.1f}%** dos condutores, nas categorias pesadas essa participação é de apenas **{pct_women_heavy:.1f}%**.")

                if not women_df.empty:
                    c_w1, c_w2 = st.columns([1, 2])
                    
                    with c_w1:
                        st.markdown("##### Categoria CNH")
                        df_w_cat = women_df.groupby('categoria_simple')['qtd_condutores'].sum().reset_index()
                        fig_w_cat = go.Figure(data=[go.Pie(
                            labels=df_w_cat['categoria_simple'], 
                            values=df_w_cat['qtd_condutores'], 
                            hole=.5,
                            textinfo='label+percent',
                            marker_colors=['#3498db', '#e74c3c', '#9b59b6']
                        )])
                        fig_w_cat.update_layout(
                            margin=dict(t=20, b=20, l=20, r=20),
                            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                            height=300
                        )
                        st.plotly_chart(fig_w_cat, use_container_width=True)

                    with c_w2:
                        st.markdown("##### Distribuição Etária (Com vs Sem EAR)")
                        df_w_age = women_df.groupby(['faixa_etaria', 'exerce_atividade_remunerada'])['qtd_condutores'].sum().unstack(fill_value=0)
                        for c in ['S', 'N']:
                            if c not in df_w_age.columns: df_w_age[c] = 0
                        
                        fig_w = go.Figure()
                        fig_w.add_trace(go.Bar(x=df_w_age.index, y=df_w_age['S'], name='Com EAR', marker_color='#2ecc71'))
                        fig_w.add_trace(go.Bar(x=df_w_age.index, y=df_w_age['N'], name='Sem EAR', marker_color='#95a5a6'))
                        fig_w.update_layout(barmode='stack', height=350, margin=dict(t=20, b=20, l=20, r=20), legend=dict(orientation="h", y=1.1))
                        st.plotly_chart(fig_w, use_container_width=True)
                else:
                    st.info("Não há dados de mulheres para exibir.")

        # --- TAB: PCD ---
        if has_pcd:
            with tab_pcd:
                pcd_df = heavy_drivers_df[heavy_drivers_df[pcd_col] == 'S']
                pcd_count = pcd_df['qtd_condutores'].sum()
                pcd_ear = pcd_df[pcd_df['exerce_atividade_remunerada'] == 'S']['qtd_condutores'].sum()
                pcd_ear_pct = (pcd_ear / pcd_count * 100) if pcd_count > 0 else 0
                
                st.metric("Condutores PCD", f"{pcd_count:,}", f"{pcd_ear_pct:.1f}% com EAR")
                
                # Comparison with Category B
                df_b = df[df['categoria_cnh'] == 'B']
                total_b = df_b['qtd_condutores'].sum()
                pcd_b = df_b[df_b[pcd_col] == 'S']['qtd_condutores'].sum()
                pct_pcd_b = (pcd_b / total_b * 100) if total_b > 0 else 0
                pct_pcd_heavy = (pcd_count / total_heavy_drivers * 100) if total_heavy_drivers > 0 else 0

                st.info(f"💡 **Inclusão PCD:** Na Categoria B, motoristas PCD representam **{pct_pcd_b:.1f}%** do total. Nas categorias pesadas, essa proporção é de **{pct_pcd_heavy:.3f}%**.")
                
                if not pcd_df.empty:
                    c_pcd1, c_pcd2, c_pcd3 = st.columns([1, 1, 2])
                    
                    with c_pcd1:
                        st.markdown("##### Gênero")
                        if has_sexo:
                            df_pcd_sex = pcd_df.groupby('genero')['qtd_condutores'].sum().reset_index()
                            fig_pcd_sex = go.Figure(data=[go.Pie(labels=df_pcd_sex['genero'], values=df_pcd_sex['qtd_condutores'], hole=.4)])
                            fig_pcd_sex.update_layout(height=300, margin=dict(t=20, b=20, l=20, r=20), legend=dict(orientation="h", y=-0.2))
                            st.plotly_chart(fig_pcd_sex, use_container_width=True)
                        else:
                            st.info("Dados de gênero não disponíveis.")
                    
                    with c_pcd2:
                        st.markdown("##### Categoria CNH")
                        df_pcd_cat = pcd_df.groupby('categoria_simple')['qtd_condutores'].sum().reset_index()
                        fig_pcd_cat = go.Figure(data=[go.Pie(
                            labels=df_pcd_cat['categoria_simple'], 
                            values=df_pcd_cat['qtd_condutores'], 
                            hole=.5,
                            textinfo='label+percent',
                            marker_colors=['#3498db', '#e74c3c', '#9b59b6']
                        )])
                        fig_pcd_cat.update_layout(
                            margin=dict(t=20, b=20, l=20, r=20),
                            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                            height=300
                        )
                        st.plotly_chart(fig_pcd_cat, use_container_width=True)

                    with c_pcd3:
                        st.markdown("##### Distribuição Etária (Com vs Sem EAR)")
                        df_pcd_age = pcd_df.groupby(['faixa_etaria', 'exerce_atividade_remunerada'])['qtd_condutores'].sum().unstack(fill_value=0)
                        for c in ['S', 'N']:
                            if c not in df_pcd_age.columns: df_pcd_age[c] = 0
                        
                        fig_pcd_age = go.Figure()
                        fig_pcd_age.add_trace(go.Bar(x=df_pcd_age.index, y=df_pcd_age['S'], name='Com EAR', marker_color='#2ecc71'))
                        fig_pcd_age.add_trace(go.Bar(x=df_pcd_age.index, y=df_pcd_age['N'], name='Sem EAR', marker_color='#95a5a6'))
                        fig_pcd_age.update_layout(barmode='stack', height=350, margin=dict(t=20, b=20, l=20, r=20), legend=dict(orientation="h", y=1.1))
                        st.plotly_chart(fig_pcd_age, use_container_width=True)
                else:
                    st.info("Não há dados de PCD para exibir.")
    else:
        st.info("Dados detalhados de Gênero e PCD não disponíveis nesta visualização.")

    # --- ROW 6: Demographics ---
    st.divider()
    st.subheader("Distribuição Etária da Força de Trabalho")
    
    age_dist = heavy_drivers_df.groupby('faixa_etaria')['qtd_condutores'].sum().reset_index()
    
    fig_age = go.Figure(go.Bar(
        x=age_dist['faixa_etaria'],
        y=age_dist['qtd_condutores'],
        marker_color='#8e44ad'
    ))
    fig_age.update_layout(
        margin=dict(t=20, b=50, l=20, r=20),
        height=350,
        xaxis=dict(tickangle=-45)
    )
    st.plotly_chart(fig_age, use_container_width=True)

    st.divider()

    st.header('Onde estão esses profissionais?')
    st.subheader('Uma visão sobre a distribuição da força de trabalho ativa do estado')

    ear_heavy_drivers_df = heavy_drivers_df[heavy_drivers_df['exerce_atividade_remunerada'] == 'S']
    
    heatmap_data = ear_heavy_drivers_df.groupby(['descricao_municipio', 'lat', 'lon'])['qtd_condutores'].sum().reset_index()
    heatmap_data.dropna(subset=['lat', 'lon'], inplace=True)

    map_center = [-22.5, -48.5]
    m = folium.Map(location=map_center, zoom_start=7, tiles='CartoDB positron', scrollWheelZoom=False)

    heat_data = [[row['lat'], row['lon'], np.log1p(row['qtd_condutores'])] for index, row in heatmap_data.iterrows()]

    HeatMap(heat_data, radius=12, blur=8).add_to(m)

    st_folium(m, use_container_width=True)

if __name__ == '__main__':
    main()
