import streamlit as st

st.set_page_config(
    page_title="SP Logistics | Home",
    page_icon="🚚",
    layout="centered"
)

def main():
    # --- Hero Section ---
    st.title("🚚 Observatório do Trabalho Logístico")
    st.subheader("Monitoramento estratégico da força de trabalho de condutores em São Paulo")
    
    st.markdown("""
    Bem-vindo ao painel de inteligência de dados sobre o mercado de motoristas profissionais (Categorias C, D e E).
    Esta ferramenta foi desenvolvida para apoiar gestores públicos e privados na compreensão do **"Apagão Logístico"**.
    """)

    st.divider()

    # --- Value Proposition (Why use this app?) ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("📊 **Diagnóstico Preciso**")
        st.markdown("Cruzamos dados de **faixa etária**, **categoria de CNH** e **atividade remunerada (EAR)** para revelar a real disponibilidade de mão de obra.")
    
    with col2:
        st.warning("🚨 **Alerta de Risco**")
        st.markdown("Identificamos municípios onde a **aposentadoria massiva** de veteranos não está sendo compensada pela entrada de jovens.")

    st.divider()

    # --- Navigation Cards ---
    st.markdown("### 🧭 Por onde começar?")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("#### 1. Panorama")
        st.caption("O Censo da Categoria")
        st.markdown("Visão geral do volume de condutores, distribuição geográfica e perfil demográfico básico.")
        st.page_link("pages/Overview.py", label="Ir para Panorama", icon="🌎")

    with c2:
        st.markdown("#### 2. O Apagão")
        st.caption("A Análise Crítica")
        st.markdown("Entenda o déficit de reposição, o abismo geracional e o mapa de risco por município.")
        st.page_link("pages/LogisticsBlackout.py", label="Ver Análise de Risco", icon="🚨")

    with c3:
        st.markdown("#### 3. Dados")
        st.caption("Transparência")
        st.markdown("Acesse a metodologia detalhada, dicionário de dados e faça o download da base completa.")
        st.page_link("pages/About_Data.py", label="Acessar Dados", icon="💾")

    st.divider()
    
    # --- Footer / Context ---
    st.markdown("""
    <div style='text-align: center; color: grey; font-size: 0.8em;'>
        Dados baseados no portal de transparência do Detran SP (Dez/2025).<br>
        Desenvolvido para análise de impacto econômico e social.
    </div>
    """, unsafe_allow_html=True)

if __name__ == '__main__':
    main()