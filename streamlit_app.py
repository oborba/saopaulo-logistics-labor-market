import pandas as pd
import streamlit as st
import plotly.express as px
import folium
import branca.colormap as cm
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# Page configuration (must be the first thing in Streamlit)
st.set_page_config(
    page_title="Logistica Pesada SP",
    page_icon="🚗",
    layout="wide"
)

# Function to classify (Business Logic)
def classify_profile(row):
    ear = row['exerce_atividade_remunerada']
    cat = row['categoria_cnh']
    
    if ear == 'N':
        return 'Amador'

    # Checks if C, D, or E exists in the category string (e.g., 'AC', 'AE')
    if any(pesada in cat for pesada in ['C', 'D', 'E']):
        return 'Logística Pesada/Tradicional'
    
    # If it has EAR and is not heavy, we assume light
    if any(leve in cat for leve in ['A', 'B']): # Covers A, B, and AB
        return 'Gig Economy/Apps'
    
    return 'Outros'

@st.cache_data
def load_data():
    df = pd.read_csv('condutores_habilitados_ativos_incrementado.csv', sep=',')

    # Remove drivers over 100 years old (statistically unlikely to be professionally active)
    df = df[~df['faixa_etaria'].isin(['101-120 ANOS', '+120 ANOS'])]

    df['tipo_atuacao'] = df.apply(classify_profile, axis=1)
    
    return df

def main():
    st.title("Panaroma de condutores C, D e E em São Paulo")
    st.markdown("Uma visão analítica sobre condutores da logistica pesada no estado.")

    df = load_data()

    # 
    # --- METRICS CALCULATION (KPIs) ---
    # General values line
    # 

    # 1. Grand Total
    total_drivers = df['qtd_condutores'].sum()

    # 2. Total EAR (Paid Activity)
    # Filter where EAR is 'S' and sum the quantity
    total_paid_activity = df[df['exerce_atividade_remunerada'] == 'S']['qtd_condutores'].sum()
    pct_paid_activity = (total_paid_activity / total_drivers) * 100

    # 3. Total Heavy Categories (C, D, E and combinations)
    # Use string method to find who contains C, D, or E
    heavy_license_filter = df['categoria_cnh'].str.contains('C|D|E', regex=True)
    total_heavy_licenses = df[heavy_license_filter]['qtd_condutores'].sum()
    pct_heavy_licenses = (total_heavy_licenses / total_drivers) * 100

    # Create 3 columns for metric cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total de Condutores", 
            value=f"{total_drivers:,.0f}".replace(",", "."),
            help="Incluindo Motos, Carros de passeio e Pesados"
        )

    with col2:
        st.metric(
            label="Exercem Atividade Remunerada", 
            value=f"{total_paid_activity:,.0f}".replace(",", "."),
            help=f"Condutores com EAR, necessário para qualquer categoria",
        )
        st.caption(f"ℹ️ {pct_paid_activity:.1f}% do total de condutores")

    with col3:
        st.metric(
            label="Habilitação Pesada (C, D, E)", 
            value=f"{total_heavy_licenses:,.0f}".replace(",", "."),
            help=f"Condutores que podem dirigir veículos pesados",
        )
        st.caption(f"ℹ️ {pct_heavy_licenses:.1f}% do total de condutores")

    # ==============================================================================
    # SECTION: LOGISTICS AND PROFESSIONAL TRANSPORT DASHBOARD
    # ==============================================================================
    
    st.divider()
    st.subheader("🚚 Motoristas de pesados (C, D e E)")
    st.markdown("""
    Seguimos uma hierarquia, onde quem tem a categoria E, acumula as permissões de B, C e D. A categoria 'A' não segue essa lógica, sendo uma permissão diferente.
    * **Grupo E:** Carretas e Articulados (Carga Pesada).
    * **Grupo D:** Ônibus e Vans (Passageiros).
    * **Grupo C:** Caminhões (Carga Média/Urbana).
    """)

    # 1. DATA PREPARATION (The "Backend" of the analysis)
    # Filter only those who have C, D, or E
    df_heavy = df[df['categoria_cnh'].str.contains('C|D|E', regex=True)].copy()

    # Create an auxiliary HIERARCHY column for cleaner charts
    # If it has E, it's E. If it doesn't have E but has D, it's D. If it only has C, it's C.
    def define_logistics_group(cat):
        if 'E' in cat: return 'Grupo E (Articulados)'
        if 'D' in cat: return 'Grupo D (Passageiros)'
        if 'C' in cat: return 'Grupo C (Caminhão)'
        return 'Outros'

    df_heavy['grupo_logistico'] = df_heavy['categoria_cnh'].apply(define_logistics_group)

    # --- ROW 1: EXECUTIVE SUMMARY (CARDS) ---
    
    # KPI 1: Active Professionals (Heavy + EAR Yes)
    total_professionals = df_heavy[df_heavy['exerce_atividade_remunerada'] == 'S']['qtd_condutores'].sum()

    # KPI 2: Top of the Pyramid (Any category containing E)
    total_cat_e = df_heavy[df_heavy['grupo_logistico'] == 'Grupo E (Articulados)']['qtd_condutores'].sum()
    
    # KPI 3: Diversity (% Women in heavy fleet)
    total_heavy_general = df_heavy['qtd_condutores'].sum()
    total_women_heavy = df_heavy[df_heavy['genero'] == 'FEMININO']['qtd_condutores'].sum()
    pct_women = (total_women_heavy / total_heavy_general) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Motoristas de pesados com EAR", f"{total_professionals:,.0f}".replace(",", "."))
    col2.metric("Topo da Pirâmide (Grupo E)", f"{total_cat_e:,.0f}".replace(",", "."))
    with col3:
        st.metric(
            label="Mulheres na Logística", 
            value=f"{total_women_heavy:,.0f}",
        )
        st.caption(f"ℹ️ {pct_women:.2f}% do setor")

    # --- ROW 2: DISTRIBUTION AND SPECIALTY ---
    
    st.divider()
    st.subheader("📊 Motoristas Ativos e Reserva Técnica")
    
    # 1. FILTER CREATION (WIDGET)
    # Get unique ranges and sort for better display in selectbox
    # Add 'All' option at the beginning of the list
    age_options = sorted(df_heavy['faixa_etaria'].unique().tolist())
    age_options.insert(0, "Todas")
    
    # st.selectbox returns the string chosen by the user
    selected_age_range = st.selectbox(
        "Filtrar análise por Faixa Etária:", 
        options=age_options,
        index=0 # Default: All
    )

    # 2. FILTER APPLICATION (Backend Logic)
    if selected_age_range == "Todas":
        df_charts = df_heavy # Use the complete dataframe
        support_text = "Visualizando **toda a base** de condutores pesados."
    else:
        # Filter only the chosen range
        df_charts = df_heavy[df_heavy['faixa_etaria'] == selected_age_range]
        support_text = f"Visualizando apenas condutores entre **{selected_age_range}**."

    st.caption(support_text)

    # 3. CHART GENERATION (Based on filtered df_charts)
    c_left, c_right = st.columns(2)

    with c_left:
        # Pie Chart: Composition by Logistics Group
        # Important: groupby is now done on df_charts (filtered)
        df_pie = df_charts.groupby('grupo_logistico')['qtd_condutores'].sum().reset_index()
        
        # Error handling: In case the filter returns no data (e.g., empty age range for Category E)
        if not df_pie.empty:
            fig_pie = px.pie(
                df_pie, 
                values='qtd_condutores', 
                names='grupo_logistico',
                title=f'Distribuição ({selected_age_range})',
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("Não há dados para esta combinação.")

    with c_right:
        # Bar Chart: EAR vs Non-EAR by Group
        df_bars = df_charts.groupby(['grupo_logistico', 'exerce_atividade_remunerada'])['qtd_condutores'].sum().reset_index()
        
        if not df_bars.empty:
            df_bars['exerce_atividade_remunerada'] = df_bars['exerce_atividade_remunerada'].map({'S': 'Profissional (EAR)', 'N': 'Sem EAR'})
            
            fig_bars = px.bar(
                df_bars, 
                x='grupo_logistico', 
                y='qtd_condutores', 
                color='exerce_atividade_remunerada',
                title=f'Profissionais vs Reserva ({selected_age_range})',
                barmode='group',
                text_auto='.2s'
            )
            st.plotly_chart(fig_bars, use_container_width=True)
        else:
            st.warning("Não há dados para esta combinação.")

    # ==============================================================================
    # ROW 3: REGIONAL INTELLIGENCE (SEARCHABLE)
    # ==============================================================================
    
    st.divider()
    st.subheader("📍 Onde estão esses profissionais?")

    st.markdown("""
    Visualização geoespacial da concentração de motoristas profissionais de carga e transporte (Categorias C, D, E).
    Usado normalização Logarítmica para a capital não ofuscar o restante do mapa
    """)

    # 1. DATA FILTERING (Business Rule)
    # Only EAR = Yes AND Heavy Categories
    map_filter = (
        (df['exerce_atividade_remunerada'] == 'S') & 
        (df['categoria_cnh'].str.contains('C|D|E', regex=True))
    )

    # Create a clean DF with only what's necessary for the map
    # Group by Municipality/Lat/Lon to sum the total quantity in that city
    df_map = df[map_filter].groupby(['descricao_municipio', 'lat', 'lon'])['qtd_condutores'].sum().reset_index()

    # Logarithmic Normalization (Optional, but recommended)
    # SP Capital has so many drivers that it "drowns out" the rest of the state if we use raw values.
    # For visualization, Log helps to see medium hubs (like Ribeirão Preto or Campinas).
    # If you prefer raw, use: df_map['weight'] = df_map['qtd_condutores']
    import numpy as np
    df_map['weight'] = np.log1p(df_map['qtd_condutores']) 

    # normalize between 0 and 1 for Folium to better understand intensity
    df_map['weight'] = df_map['weight'] / df_map['weight'].max()

    # 2. BASE MAP CONFIGURATION (FOLIUM)
    # Average coordinates of SP State to center the camera
    map_sp = folium.Map(
        location=[-22.1, -48.9], # Approximate center of SP
        zoom_start=7,
        tiles="cartodbpositron" # 'Clean' style (light gray) to highlight heatmap colors
    )

    # 3. HEATMAP LAYER CREATION
    # Folium expects a list of lists: [Lat, Lon, Weight]
    heatmap_data = df_map[['lat', 'lon', 'weight']].values.tolist()

    HeatMap(
        heatmap_data,
        radius=15,       # Size of the "spot" for each point
        blur=20,         # How much the spot spreads (smoothness)
        min_opacity=0.3, # Minimum opacity
        gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'} # Color gradient
    ).add_to(map_sp)

    # Add Tooltips (Optional: Invisible circles to show city name on hover)
    for _, row in df_map.iterrows():
        folium.Circle(
            location=[row['lat'], row['lon']],
            radius=row['qtd_condutores'] * 0.05, # Proportional radius (adjust multiplier as needed)
            color=None, # Invisible
            fill=False,
            tooltip=f"{row['descricao_municipio']}: {row['qtd_condutores']:,.0f} motoristas"
        ).add_to(map_sp)

    # 4. RENDERING IN STREAMLIT
    # st_folium is the component that connects Folium to Streamlit
    st_folium(map_sp, width=None, height=500, use_container_width=True)

    st.info("💡 **Análise:** Note como a mancha vermelha segue as principais rodovias (Anhanguera/Bandeirantes e Dutra).")




    st.markdown("Pesquise sua cidade abaixo para entender a vocação logística da sua região.")

    # Helper function to render tables with search
    # As a Senior, you know DRY (Don't Repeat Yourself) is life.
    def render_ranking(df_source, grupo_filtro, titulo, key_sulfix):
        
        # 1. Data Preparation (Grouping and Sorting)
        # Filter by desired logistics group
        df_filtered = df_source[df_source['grupo_logistico'] == grupo_filtro]
        
        # Group by city and sum
        df_rank = df_filtered.groupby('descricao_municipio')[['qtd_condutores']].sum()
        
        # Sort from largest to smallest
        df_rank = df_rank.sort_values(by='qtd_condutores', ascending=False).reset_index()
        
        # Rename columns for better UI
        df_rank.columns = ['Município', 'Total Condutores']

        # 2. Search Interface
        st.markdown(f"**{titulo}**")
        
        # The 'key' must be unique for each widget in Streamlit, otherwise it conflicts
        search_term = st.text_input(f"🔍 Buscar cidade ({titulo})", key=f"search_{key_sulfix}")

        # 3. Dynamic Filtering
        if search_term:
            # Case-insensitive filter
            mask = df_rank['Município'].str.contains(search_term.upper(), na=False)
            df_display = df_rank[mask]
        else:
            df_display = df_rank

        # 4. Table Rendering
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True, # Hide numeric index (0, 1, 2...)
            height=300, # Define fixed height with scroll
            column_config={
                "Município": st.column_config.TextColumn("Cidade"),
                "Total Condutores": st.column_config.NumberColumn(
                    "Qtd. Habilitados",
                    format="%d", # Integer formatting
                )
            }
        )

    # Layout em duas colunas
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        # Call function for Group E (Heavy Cargo)
        render_ranking(
            df_heavy, 
            'Grupo E (Articulados)', 
            "🚛 Gigantes das Estradas (Grupo E)", 
            "grupo_e"
        )

    with col_b:
        # Call function for Group D (Passengers)
        render_ranking(
            df_heavy, 
            'Grupo D (Passageiros)', 
            "🚌 Mestres do Transporte (Grupo D)", 
            "grupo_d"
        )

    with col_c:
        # Call function for Group C (Light Cargo)
        render_ranking(
            df_heavy, 
            'Grupo C (Caminhão)', 
            "🚚 Mestres da Distribuição (Grupo C)", 
            "grupo_c"
        )

    # ==============================================================================
    # ROW 4: LOGISTICS DEMOGRAPHICS (BLACKOUT THESIS) - SIMPLIFIED
    # ==============================================================================
    
    st.divider()
    st.header("⚡ Possível Apagão Logístico")
    st.markdown("""
    Análise da distribuição etária dos motoristas de pesados.
    A hipótese é que a força de trabalho está concentrada em faixas etárias mais altas.
    """)

    # 1. DATA PREPARATION
    
    # Defining CHRONOLOGICAL ORDER manually.
    # This is CRUCIAL so charts don't get alphabetical order (e.g., 18 after 100).
    # Adjust strings exactly as they are in your CSV.
    age_group_order = [
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

    # Filter only Heavy Categories (C, D, E)
    heavy_filter = (df['categoria_cnh'].str.contains('C|D|E', regex=True))
    df_heavy_total = df[heavy_filter].copy() # Includes EAR Yes and No
    
    # Specific dataset for Professionals (EAR = Yes)
    df_heavy_paid = df_heavy_total[df_heavy_total['exerce_atividade_remunerada'] == 'S'].copy()

    # --- RISK AND RENEWAL KPI CARDS ---
    
    total_heavy_professionals = df_heavy_paid['qtd_condutores'].sum()
    
    # Group definitions (Adapt lists if necessary)
    young_age_ranges = ['18-21 ANOS', '22-25 ANOS', '26-30 ANOS'] 
    senior_age_ranges = ['61-70 ANOS', '71-80 ANOS', '81-90 ANOS', '91-100 ANOS']

    count_young = df_heavy_paid[df_heavy_paid['faixa_etaria'].isin(young_age_ranges)]['qtd_condutores'].sum()
    count_seniors = df_heavy_paid[df_heavy_paid['faixa_etaria'].isin(senior_age_ranges)]['qtd_condutores'].sum()

    pct_young = (count_young / total_heavy_professionals) * 100
    pct_seniors = (count_seniors / total_heavy_professionals) * 100

    # Exibição dos Cards
    c1, c2 = st.columns(2)
    
    with c1:
        st.metric(
            label="👴 Risco de Aposentadoria (60+)", 
            value=f"{pct_seniors:.1f}%",
        )
        st.caption(f"{count_seniors:,.0f} condutores".replace(",", "."))
    
    with c2:
        st.metric(
            label="👶 Taxa de Renovação (18-30)", 
            value=f"{pct_young:.1f}%",
        )
        st.caption(f"{count_young:,.0f} condutores".replace(",", "."))       

    # --- THE DEMOGRAPHIC WALL (Stacked Bar Chart) ---
    st.subheader("Distribuição Etária")
    
    # Grouping by Range and EAR
    df_bar_chart = df_heavy_total.groupby(['faixa_etaria', 'exerce_atividade_remunerada'])['qtd_condutores'].sum().reset_index()
    
    # Apply categorical sorting
    df_bar_chart['faixa_etaria'] = pd.Categorical(
        df_bar_chart['faixa_etaria'], 
        categories=age_group_order, 
        ordered=True
    )
    df_bar_chart = df_bar_chart.sort_values('faixa_etaria')
    
    # Rename Legend to be friendly
    df_bar_chart['exerce_atividade_remunerada'] = df_bar_chart['exerce_atividade_remunerada'].map(
        {'S': 'Profissional Ativo', 'N': 'Reserva (Sem EAR)'}
    )

    fig_wall = px.bar(
        df_bar_chart,
        x='faixa_etaria',
        y='qtd_condutores',
        color='exerce_atividade_remunerada',
        title='Volume de Condutores Pesados por Idade',
        # Contrasting colors: Strong orange for Active, Soft blue for Reserve
        color_discrete_map={'Profissional Ativo': '#EF553B', 'Reserva (Sem EAR)': '#636EFA'}, 
        barmode='stack'
    )
    st.plotly_chart(fig_wall, use_container_width=True)

    # --- DEMOGRAPHIC CLIFF CHART ---
    st.divider()
    st.subheader("A Escolha dos Jovens")
    st.markdown("""
    Comparativo direto entre profissionais (EAR) de categorias **Leves (B/AB)** contra **Pesadas (C/D/E)**.
    Os jovens estão optando pela flexibilidade (e menor barreira de entrada) dos aplicativos em vez da carreira de motorista profissional tradicional?
    """)

    # 1. Prepare data (Only those with EAR)
    df_paid = df[df['exerce_atividade_remunerada'] == 'S'].copy()

    # 2. Define groups (Light vs Heavy)
    def classify_cliff(cat):
        # If it has C, D, or E, it's Heavy
        if any(x in cat for x in ['C', 'D', 'E']):
            return 'Pesadas (C, D, E)'
        # If it's A, B, or AB, it's Light (Apps/Motorcycles)
        # Note: We include A and AB as they are also part of the "Gig Economy" (Motoboys/Uber)
        elif cat in ['B', 'AB', 'A']: 
            return 'Leves (A, B, AB)'
        return 'Outros'

    df_paid['grupo_comparativo'] = df_paid['categoria_cnh'].apply(classify_cliff)

    # Filter out "Others" and group
    df_cliff = df_paid[df_paid['grupo_comparativo'] != 'Outros']
    df_cliff_chart = df_cliff.groupby(['faixa_etaria', 'grupo_comparativo'])['qtd_condutores'].sum().reset_index()

    # 3. Sorting (Crucial: Use the age_group_order list defined earlier)
    df_cliff_chart['faixa_etaria'] = pd.Categorical(
        df_cliff_chart['faixa_etaria'],
        categories=age_group_order,
        ordered=True
    )
    df_cliff_chart = df_cliff_chart.sort_values('faixa_etaria')

    # 4. The Chart (Side-by-Side)
    fig_cliff = px.bar(
        df_cliff_chart,
        x='faixa_etaria',
        y='qtd_condutores',
        color='grupo_comparativo',
        barmode='group', # Important: Places bars side by side, not stacked
        title='Apps vs Tradicional',
        labels={'qtd_condutores': 'Qtd. Motoristas Profissionais', 'faixa_etaria': 'Idade'},
        # Colors: Green (Tech/Apps) vs Orange/Red (Traditional/Alert)
        color_discrete_map={
            'Leves (A, B, AB)': '#00CC96', 
            'Pesadas (C, D, E)': '#EF553B'
        }
    )
    
    # Fine layout adjustments
    fig_cliff.update_layout(xaxis_tickangle=-45) # Tilts X-axis text if it gets cramped
    
    st.plotly_chart(fig_cliff, use_container_width=True)
    
    # Automatic analysis (Dynamic text)
    # We take the peak of each group to comment
    peak_light = df_cliff_chart[df_cliff_chart['grupo_comparativo'] == 'Leves (A, B, AB)'].sort_values('qtd_condutores', ascending=False).iloc[0]['faixa_etaria']
    peak_heavy = df_cliff_chart[df_cliff_chart['grupo_comparativo'] == 'Pesadas (C, D, E)'].sort_values('qtd_condutores', ascending=False).iloc[0]['faixa_etaria']

    # ==============================================================================
    # SECTION: Logistics Demographic Risk (Filtered Scatter Map)
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

    # 1. RIGOROUS FILTERING (The "Secret Sauce")
    # First, we isolate only the Heavy Logistics universe
    # This ensures we are not counting young people on motorcycles/cars in the statistics
    heavy_license_filter = df['categoria_cnh'].str.contains('C|D|E', regex=True)
    df_map_target = df[heavy_license_filter].copy()

    # 2. DATA PREPARATION

    # Risk Ranges (60+)
    ranges_60_plus = [
        '61-70 ANOS', '71-80 ANOS', '81-90 ANOS', 
        '91-100 ANOS', 'MAIOR DE 100 ANOS' # Adjust according to your unique()
    ]

    # Base Grouping: Total HEAVY Drivers by city
    df_city_total = df_map_target.groupby(['descricao_municipio', 'lat', 'lon'])['qtd_condutores'].sum().reset_index()
    df_city_total.rename(columns={'qtd_condutores': 'total_pesados'}, inplace=True)

    # Risk Grouping: Total HEAVY Drivers 60+ by city
    df_seniors = df_map_target[df_map_target['faixa_etaria'].isin(ranges_60_plus)].groupby('descricao_municipio')['qtd_condutores'].sum().reset_index()
    df_seniors.rename(columns={'qtd_condutores': 'total_60_plus'}, inplace=True)

    # Merge (Left Join to ensure cities without seniors don't disappear, stay with 0)
    df_scatter = pd.merge(df_city_total, df_seniors, on='descricao_municipio', how='left')
    df_scatter['total_60_plus'] = df_scatter['total_60_plus'].fillna(0)

    # Risk Percentage Calculation
    # (Total Heavy Seniors / Total Heavy in City)
    df_scatter['pct_risco'] = (df_scatter['total_60_plus'] / df_scatter['total_pesados']) * 100

    # 3. MAP CONFIGURATION

    risk_map = folium.Map(
        location=[-22.5, -48.5], 
        zoom_start=7,
        tiles="cartodbdark_matter" # Dark background to highlight red/green
    )

    # Color Scale: Green (0%) -> Yellow (15%) -> Red (30%)
    # Increased the ruler to 30% because the transport sector is naturally older.
    colormap = cm.LinearColormap(
        colors=['#00FF00', '#FFFF00', '#FF0000'], 
        index=[0, 15, 30], 
        vmin=0, 
        vmax=30,
        caption='% de Caminhoneiros/Motoristas 60+'
    )
    risk_map.add_child(colormap)

    # 4. CIRCLE PLOTTING

    for _, row in df_scatter.iterrows():
        # Visual filter: Shows only cities with minimal relevance (e.g., > 50 heavy drivers)
        if row['total_pesados'] > 50:
            
            # Size: Log to control visual scale
            radius = np.log1p(row['total_pesados']) * 1.8
            
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=radius,
                color=None,
                fill=True,
                fill_color=colormap(row['pct_risco']), # The color now reflects the aging OF THE SECTOR
                fill_opacity=0.8,
                popup=folium.Popup(f"""
                    <b>{row['descricao_municipio']}</b><br>
                    Frota Pesada: {int(row['total_pesados']):,}<br>
                    Idosos (60+): {row['pct_risco']:.1f}%
                """, max_width=200),
                tooltip=f"{row['descricao_municipio']}: {row['pct_risco']:.1f}% em risco"
            ).add_to(risk_map)

    st_folium(risk_map, width=None, height=500, use_container_width=True)


if __name__ == "__main__":
    main()