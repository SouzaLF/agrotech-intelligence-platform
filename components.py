# components.py
import streamlit as st

def metric_card(title: str, value: str, delta: str = None, help_text: str = None) -> None:
    """Cria um card de métrica estilizado com efeitos visuais avançados.
    
    Args:
        title (str): Título exibido no topo do card (ex: "Taxa de Crescimento")
        value (str): Valor principal formatado (ex: "R$ 1.200,00")
        delta (str, optional): Variação com sinal (ex: "+2.5%"). Defaults to None.
        help_text (str, optional): Texto de ajuda flutuante. Defaults to None.
    
    Example:
        >>> metric_card(
        >>>     title="Preço Soja", 
        >>>     value="R$ 138,32", 
        >>>     delta="-1.2% (vs ontem)",
        >>>     help_text="Fonte: CEPEA/ESALQ"
        >>> )
    """
    with st.container():
        st.markdown(f"""
        <div class="data-card">
            <p style="opacity:0.8;margin-bottom:0.5rem;font-size:0.9rem">{title}</p>
            <h3 style="margin-top:0;margin-bottom:0.5rem">{value}</h3>
            {f'<p style="margin:0;font-size:0.8rem;color:#3a7bd5">{delta}</p>' if delta else ''}
        </div>
        """, unsafe_allow_html=True)
        if help_text:
            st.markdown(f"<div style='font-size:0.7rem;opacity:0.6'>{help_text}</div>", unsafe_allow_html=True)