import pandas as pd
import streamlit as st


def classify_profile(row):
    """Classifies a driver's profile based on their EAR status and CNH category.

    Args:
        row (pd.Series): A row from a pandas DataFrame containing 'exerce_atividade_remunerada'
                         and 'categoria_cnh' columns.

    Returns:
        str: The classified profile type ('Amador', 'Logística Pesada/Tradicional',
             'Gig Economy/Apps', or 'Outros').
    """
    ear = row['exerce_atividade_remunerada']
    cat = row['categoria_cnh']

    if ear == 'N':
        return 'Amador'

    # Checks if C, D, or E exists in the category string (e.g., 'AC', 'AE')
    if any(pesada in cat for pesada in ['C', 'D', 'E']):
        return 'Logística Pesada/Tradicional'

    # If it has EAR and is not heavy, we assume light
    if any(leve in cat for leve in ['A', 'B']):  # Covers A, B, and AB
        return 'Gig Economy/Apps'

    return 'Outros'


@st.cache_data
def load_data():
    df = pd.read_csv('condutores_habilitados_ativos_incrementado.csv', sep=',')

    # Remove drivers over 100 years old (statistically unlikely to be professionally active)
    df = df[~df['faixa_etaria'].isin(['101-120 ANOS', '+120 ANOS'])]

    df['tipo_atuacao'] = df.apply(classify_profile, axis=1)

    return df