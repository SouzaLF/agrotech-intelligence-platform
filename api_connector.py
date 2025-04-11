import requests
import pandas as pd
from datetime import datetime
import streamlit as st
from config import Config

@st.cache_data(
    ttl=3600,  # Cache de 1 hora
    show_spinner="Buscando dados da API..."
)

def fetch_commodity_data(commodity: str) -> pd.DataFrame:
    api_key = Config.ALPHA_VANTAGE_KEY
    """Obtém dados de commodities com tratamento robusto de erros.
    
    Features:
    - Cache automático
    - Fallback para dados mock
    - Timeout para evitar travamentos
    """
    try:
        url = f"https://www.alphavantage.co/query?function={commodity}&interval=monthly&apikey={api_key}"
        
        # Adicione timeout (10 segundos conexão, 30 segundos leitura)
        response = requests.get(url, timeout=(10, 30)).json()
        
        if not response.get("data"):
            st.warning("⚠️ Dados não encontrados na API. Usando dados simulados...")
            return generate_mock_data()
            
        # Processamento seguro
        df = pd.DataFrame(response["data"])
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['value'] = pd.to_numeric(df['value'], errors='coerce').ffill()
        
        return df.dropna().sort_values('date')
        
    except requests.exceptions.RequestException as e:
        st.error(f"⛔ Falha na conexão: {str(e)}")
        return generate_mock_data()
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        return generate_mock_data()

def generate_mock_data():
    """Gera dados fictícios para manter o funcionamento do dashboard"""
    dates = pd.date_range(end=datetime.today(), periods=12, freq='M')
    values = [100 + i*5 + (i%3)*10 for i in range(12)]
    return pd.DataFrame({'date': dates, 'value': values})