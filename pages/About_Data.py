import streamlit as st
import utils
import pandas as pd

st.set_page_config(layout="centered", page_title="Sobre os Dados")

def main():
    st.title('Sobre os Dados')

    # 1. Context and Source
    st.markdown("""
    ### Fonte e Metodologia
    
    Este projeto utiliza dados públicos disponibilizados pelo **Detran SP**. 
    O conjunto de dados original refere-se aos **Condutores Habilitados Ativos** (referência: **dezembro de 2025**) e está disponível no portal de [Dados Abertos](https://www.detran.sp.gov.br/detransp/pb/informacoes/transparencia/dados_abertos?id=dados_abertos).
    
    **O que foi feito neste projeto:**
    1. **Coleta:** Os dados foram extraídos do portal de dados abertos.
    2. **Enriquecimento:** Adicionamos as coordenadas geográficas (Latitude e Longitude) de cada município para permitir a visualização em mapas de calor.
    3. **Agregação:** Os dados representam contagens (não dados individuais sensíveis), agrupados por:
        - Município
        - Categoria da CNH
        - Faixa Etária
        - Indicador de Atividade Remunerada (EAR)
    """)

    # Load data using your existing utility
    df = utils.load_data()

    st.divider()

    # 2. Data Dictionary
    st.subheader("Dicionário de Dados")
    st.markdown("""
    Entenda as colunas disponíveis no dataset para download:
    """)
    
    # Creating a manual dictionary for clarity
    data_dict = pd.DataFrame([
        {"Coluna": "descricao_municipio", "Descrição": "Nome da cidade do estado de São Paulo"},
        {"Coluna": "categoria_cnh", "Descrição": "Categoria da habilitação (A, B, C, D, E e combinações)"},
        {"Coluna": "faixa_etaria", "Descrição": "Grupo de idade do condutor"},
        {"Coluna": "exerce_atividade_remunerada", "Descrição": "'S' para Sim, 'N' para Não (EAR)"},
        {"Coluna": "qtd_condutores", "Descrição": "Quantidade total de condutores naquele grupo"},
        {"Coluna": "lat / lon", "Descrição": "Coordenadas geográficas do centróide da cidade"},
    ])
    st.table(data_dict)

    st.divider()

    # 3. Preview and Download
    st.subheader("Acesso aos Dados")
    
    st.write("Visualização das primeiras 50 linhas do dataset processado:")
    st.dataframe(df.head(50), use_container_width=True)

    # Convert DF to CSV for download
    csv = df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Baixar Dataset Completo (CSV)",
        data=csv,
        file_name='detran_sp_condutores_enrich.csv',
        mime='text/csv',
        help="Clique para baixar o arquivo CSV com todos os dados utilizados neste dashboard."
    )

if __name__ == '__main__':
    main()