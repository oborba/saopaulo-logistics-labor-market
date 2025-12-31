import streamlit as st

# Page configuration (must be the first thing in Streamlit)
st.set_page_config(page_title='Logistica Pesada SP', page_icon='🚗', layout='wide')

pg = st.navigation([
    st.Page("pages/Home.py", title="Home", icon="🏠"),
    st.Page("pages/LogisticsBlackout.py", title="Apagão Logístico", icon="📉")
])
pg.run()
