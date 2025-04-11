import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from io import BytesIO
import requests
import json
import geopandas as gpd
import zipfile
import folium
from streamlit_folium import st_folium
from branca.colormap import LinearColormap

# Configuração da página
st.set_page_config(
    page_title="AgroTech Intelligence Platform",
    layout="wide",
    page_icon="🚜",
    initial_sidebar_state="collapsed"
)

# --- Dados Geoespaciais Enriquecidos ---
@st.cache_data
def load_geodata():
    """Carrega dados geoespaciais com tratamento de erros robusto"""
    try:
        # GeoJSON alternativo (com propriedades garantidas)
        geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
        estados_geo = requests.get(geojson_url).json()
        
        # Dados de exemplo (substitua pelos seus)
        produtividade = {
            "AC": 50.0, "AL": 48.0, "AP": 52.0, "AM": 55.0,
            "BA": 48.9, "CE": 47.0, "DF": 60.0, "ES": 53.0,
            "GO": 59.1, "MA": 46.0, "MT": 60.5, "MS": 61.2,
            "MG": 52.3, "PA": 49.0, "PB": 47.5, "PR": 58.2,
            "PE": 48.0, "PI": 47.0, "RJ": 54.0, "RN": 47.0,
            "RS": 55.8, "RO": 53.0, "RR": 51.0, "SC": 57.0,
            "SP": 56.7, "SE": 48.5, "TO": 50.0
        }

        # Padroniza propriedades
        for feature in estados_geo['features']:
            estado_id = feature['properties']['sigla']  # Agora usando 'sigla'
            feature['properties'].update({
                'produtividade': produtividade.get(estado_id, 0),
                'nome': feature['properties'].get('name', '')
            })

        return estados_geo

    except Exception as e:
        st.error(f"Erro ao carregar dados geográficos: {str(e)}")
        # Retorna um GeoJSON vazio em caso de falha
        return {
            "type": "FeatureCollection",
            "features": []
        }

estados_geo = load_geodata()

# Mapeamento de tiles e suas atribuições
TILE_LAYERS = {
    "OpenStreetMap": {
        "tiles": "OpenStreetMap",
        "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    },
    "CartoDB DarkMatter": {
        "tiles": "CartoDB dark_matter",
        "attr": '&copy; <a href="https://www.carto.com/attributions">CARTO</a>'
    },
    "Stamen Terrain": {
        "tiles": "Stamen Terrain",
        "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.'
    }
}

# Configuração de estado (adicionar logo abaixo dos imports)
if 'filtros' not in st.session_state:
    st.session_state.filtros = {
        'commodities': ['Soja', 'Milho'],
        'periodo': [datetime(2023,1,1), datetime(2023,12,31)]
    }

# ======================================
# 1. CSS PERSONALIZADO
# ======================================
st.markdown("""
<style>
/* Estilos para tabelas nativas do Streamlit */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

[data-testid="stDataFrame"] table {
    width: 100% !important;
}

[data-testid="stDataFrame"] th {
    background: linear-gradient(45deg, #0047AB, #002366) !important;
    color: white !important;
    font-weight: bold !important;
    text-transform: uppercase;
}

[data-testid="stDataFrame"] tr:nth-child(even) {
    background-color: rgba(0, 71, 171, 0.1) !important;
}

[data-testid="stDataFrame"] tr:hover {
    background-color: rgba(0, 150, 255, 0.2) !important;
}
</style>
""", unsafe_allow_html=True)

# --- CSS Customizado (Design Futurista) ---
st.markdown("""
<style>
/* Fundo tecnológico */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at center, #0a1a2e 0%, #000000 100%);
    color: #ffffff;
}

/* Títulos holográficos */
h1, h2, h3 {
    background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
}

/* Cards futuristas */
.css-1l269bu {
    background: rgba(10, 25, 47, 0.7) !important;
    backdrop-filter: blur(16px);
    border-radius: 12px;
    border: 1px solid rgba(0, 210, 255, 0.3);
    box-shadow: 0 8px 32px rgba(0, 107, 255, 0.2);
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.css-1l269bu:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 40px rgba(0, 107, 255, 0.3);
}

/* Botões de ação */
.stButton>button {
    background: linear-gradient(45deg, #00c6ff 0%, #0072ff 100%);
    border: none;
    border-radius: 8px;
    color: white;
    font-weight: 600;
    padding: 12px 32px;
    text-transform: uppercase;
    letter-spacing: 1px;
    transition: all 0.4s;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 198, 255, 0.4);
}

/* Barras de divisão */
hr {
    border: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0, 210, 255, 0.6), transparent);
    margin: 40px 0;
}
</style>
""", unsafe_allow_html=True)

# --- Dados REAIS com apresentação aprimorada ---
@st.cache_data
def load_data():
    dates = pd.date_range(start="2023-01-01", periods=12, freq='M')
    return pd.DataFrame({
        # Soja (R$/sc 60kg) - Valores reais formatados
        "Soja": [178.50, 182.30, 185.20, 188.50, 192.00, 195.80, 
                 200.50, 205.20, 210.00, 215.50, 220.80, 225.30],
        # Milho (R$/sc 60kg) - Valores reais formatados
        "Milho": [87.30, 89.10, 91.50, 93.20, 95.40, 97.10,
                  99.50, 101.80, 104.20, 106.50, 108.90, 110.50],
        # Café (R$/sc 60kg) - Valores reais formatados
        "Café": [1200.00, 1225.50, 1252.30, 1270.75, 1295.90, 1310.20,
                 1335.00, 1360.50, 1385.75, 1410.30, 1435.90, 1460.20],
        "Data": dates
    }).set_index('Data')

df = load_data()

# Dados estaduais com formatação profissional
estados_brasil = {
    "Estado": ["MT", "PR", "RS", "GO", "MG", "SP", "BA", "MS"],
    "Produtividade (sc/ha)": [60.5, 58.2, 55.8, 59.1, 52.3, 56.7, 48.9, 61.2],
    "Área Cultivada (mi ha)": [11.4, 5.7, 6.2, 4.1, 2.9, 2.3, 1.8, 3.5],
    "Escoamento": ["Ferrovia", "Porto", "Porto", "Rodovia", "Rodovia", "Rodovia", "Ferrovia", "Ferrovia"],
    "Lat": [-12.5, -24.5, -30.0, -16.5, -18.5, -22.0, -12.0, -20.5],
    "Lon": [-55.5, -51.5, -53.0, -49.5, -44.5, -47.5, -41.5, -54.5]
}
df_mapa = pd.DataFrame(estados_brasil)

def convert_df(df, format_type):
    """Converte DataFrame para diferentes formatos"""
    if format_type == "CSV":
        return df.to_csv(index=True).encode('utf-8')
    elif format_type == "Excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=True)
        return output.getvalue()
    elif format_type == "JSON":
        return df.to_json(orient='records').encode('utf-8')

# --- Header Holográfico ---
col1, col2 = st.columns([1, 3])
with col1:
    st.image("logo.svg", width=200)  # Logo fictício
with col2:
    st.title("AGROTECH INTELLIGENCE PLATFORM")
    st.markdown("""<div style="opacity:0.8;margin-top:-15px;">ANÁLISE EM TEMPO REAL DO AGRONEGÓCIO BRASILEIRO</div>""", 
                unsafe_allow_html=True)

st.markdown("---")

# --- KPIs em Tempo Real ---
st.subheader("🌡️ DADOS EM TEMPO REAL")
col1, col2, col3, col4 = st.columns(4)
# --- KPIs com FORMATAÇÃO APRIMORADA ---
with col1:
    st.metric(
        label="💰 Preço Soja (SC 60kg)", 
        value="R$ 138,32", 
        delta="-21,90 (Dezembro/2023)",
        delta_color="normal",
        help="Cepea/Esalq - Paraná 2023/24"
    )
    
with col2:
    st.metric(
        label="🚢 Exportações Soja", 
        value="3,83 mi t", 
        delta="97,8% (Dezembro/2023)",
        help="MAPA Safra 2023/24"
    )

with col3:
    st.metric(
        label="🌱 Produtividade Média", 
        value="53,4 sc/ha",
        delta="-8,7% (vs safra anterior)",
        delta_color="normal",
        help="CONAB Safra 2023/24"
    )

with col4:
    st.metric(
        label="📈 Área Plantada", 
        value="79,82 mi ha", 
        delta="1,6% (Dezembro/2023)",
        help="CONAB Safra 2023/24"
    )

# --- Visualizações Premium ---
tab1, tab2, tab3 = st.tabs(["📈 ANÁLISE MERCADOLÓGICA", "🌎 MAPA DE PRODUTIVIDADE", "📊 DADOS DETALHADOS"])

with tab1:
    view_type = st.radio("Tipo de Visualização:",
                    ["Área Empilhada", "Heatmap", "Linhas Paralelas"],
                    horizontal=True)
    if view_type == "Área Empilhada":
        st.subheader("📊 DISTRIBUIÇÃO RELATIVA DAS COMMODITIES")

        fig = px.area(df.reset_index(), 
                    x='Data', 
                    y=df.columns,
                    height=500,
                    template='plotly_dark',
                    color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c'])
        
        fig.update_layout(
            yaxis_title="Preço (R$)",
            xaxis_title="Mês/Ano",
            hovermode="x unified",
            legend=dict(
                title="Variável",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            hoverlabel=dict(
                bgcolor="rgba(0,0,0,0.8)",
                font_size=14,
                font_family="Arial"
            )
            
        )
        
        st.plotly_chart(fig, use_container_width=True)

    elif view_type == "Heatmap":
        st.subheader("🔥 HEATMAP DE VARIAÇÃO PERCENTUAL")
        
        # Calcula variação percentual
        returns = df.pct_change().dropna() * 100
        
        fig = px.imshow(returns.T,
                    x=returns.index,
                    y=returns.columns,
                    color_continuous_scale=[
                        [0, '#3a7bd5'],  # Azul
                        [0.5, '#00d2ff'], # Ciano 
                        [1, '#00d2ff']    # Ciano
                    ],
                    aspect="auto",
                    height=500)
        
        fig.update_layout(
            xaxis_title="Data",
            yaxis_title="Commodity",
            coloraxis_colorbar=dict(
                title="Variação %",
                thickness=15
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        # Adiciona valores nos tiles
        fig.update_traces(
            text=returns.round(2).T.values,
            texttemplate="%{text}%",
            hovertemplate="<b>%{y}</b><br>Data: %{x}<br>"
        )

        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.subheader("📈 EVOLUÇÃO DE PREÇOS POR COMMODITY")
    
        # Cria subplots com eixos compartilhados
        fig = px.line(df.reset_index(), 
                    x='Data', 
                    y=df.columns,
                    facet_col='variable',
                    facet_col_wrap=2,
                    height=600,
                    template='plotly_dark')
        
        # Ajustes de layout profissional
        fig.update_layout(
            showlegend=False,
            margin=dict(l=50, r=50, t=80, b=50),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # Personaliza cada subplot
        for annotation in fig.layout.annotations:
            annotation.text = annotation.text.split("=")[1]
            annotation.font.size = 14
        
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    # --- Configuração Inicial ---
    st.subheader("🌎 MAPA DE PRODUTIVIDADE DINÂMICO")
    
    # Controles Avançados
    col1, col2 = st.columns([2, 1])
    with col1:
        variavel = st.selectbox(
            "Variável Principal",
            options=["Produtividade (sc/ha)", "Área Cultivada (mi ha)"],
            key="map_var"
        )
    with col2:
        mapa_base = st.selectbox(
            "Base Cartográfica",
            ["OpenStreetMap", "CartoDB DarkMatter", "Stamen Terrain"],
            key="map_base"
        )

    # --- Processamento de Dados ---
    df_mapa['size'] = df_mapa['Área Cultivada (mi ha)'] * 2  # Ajuste visual
    colormap = LinearColormap(
        colors=['#ff0000', '#ffff00', '#00ff00'],
        vmin=df_mapa['Produtividade (sc/ha)'].min(),
        vmax=df_mapa['Produtividade (sc/ha)'].max()
    ).to_step(n=10)

    # --- Criação do Mapa Folium ---
    tile_config = TILE_LAYERS.get(mapa_base, TILE_LAYERS["OpenStreetMap"])

    m = folium.Map(
        location=[-15, -55],
        zoom_start=4,
        tiles=tile_config["tiles"],
        attr=tile_config["attr"],  # Atribuição correta
        control_scale=True
    )

    # Camada de Polígonos Estaduais (GeoJSON)
    folium.GeoJson(
        estados_geo,
        name="Estados",
        style_function=lambda feature: {
            'fillColor': colormap(feature['properties']['produtividade']),
            'color': 'white',
            'weight': 1,
            'fillOpacity': 0.7
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['sigla', 'nome', 'produtividade'],
            aliases=['Estado:', 'Nome:', 'Produtividade:'],
            localize=True
        )
    ).add_to(m)

    # Marcadores Circulares
    for idx, row in df_mapa.iterrows():
        folium.CircleMarker(
            location=[row['Lat'], row['Lon']],
            radius=row['size'],
            color=colormap(row['Produtividade (sc/ha)']),
            fill=True,
            fill_opacity=0.7,
            popup=f"""
            <b>{row['Estado']}</b><br>
            Produtividade: {row['Produtividade (sc/ha)']} sc/ha<br>
            Área: {row['Área Cultivada (mi ha)']} mi ha
            """,
            tooltip=row['Estado']
        ).add_to(m)

    # --- Controles do Mapa ---
    colormap.caption = 'Produtividade (sc/ha)'
    colormap.add_to(m)
    folium.LayerControl().add_to(m)

    # --- Exibição ---
    with st.expander("🔍 Controles Avançados", expanded=True):
        st_folium(m, width=1000, height=500)

    # --- Sidebar Analytics ---
    with st.sidebar:
        st.subheader("📊 Análise Geográfica")
        selected_state = st.selectbox(
            "Filtrar por Estado",
            options=df_mapa['Estado'].unique()
        )
        state_data = df_mapa[df_mapa['Estado'] == selected_state].iloc[0]
        
        st.metric("Produtividade", f"{state_data['Produtividade (sc/ha)']} sc/ha")
        st.metric("Área Cultivada", f"{state_data['Área Cultivada (mi ha)']} mi ha")
        
        # Mini-gráfico de tendência
        st.vega_lite_chart({
            "mark": {"type": "area", "interpolate": "monotone"},
            "encoding": {
                "x": {"field": "Ano", "type": "ordinal"},
                "y": {"field": "Produtividade", "type": "quantitative"}
            },
            "data": {
                "values": [
                    {"Ano": "2020", "Produtividade": state_data['Produtividade (sc/ha)'] * 0.8},
                    {"Ano": "2021", "Produtividade": state_data['Produtividade (sc/ha)'] * 0.9},
                    {"Ano": "2022", "Produtividade": state_data['Produtividade (sc/ha)'] * 0.95},
                    {"Ano": "2023", "Produtividade": state_data['Produtividade (sc/ha)']}
                ]
            }, "height": 150
        })

    # --- Painel de Análise ---
    st.divider()
    st.subheader("🔍 Análise Comparativa")

    col1, col2 = st.columns(2)
    with col1:
        st.vega_lite_chart({
            "data": {"values": df_mapa.to_dict('records')},
            "mark": {"type": "bar", "cornerRadiusEnd": 4},
            "encoding": {
                "x": {"field": "Estado", "type": "nominal", "sort": "-y"},
                "y": {"field": variavel, "type": "quantitative"},
                "color": {
                    "field": "Estado",
                    "scale": {"scheme": "viridis"},
                    "legend": None
                }
            },
            "height": 430
        })

    with col2:
        st.plotly_chart(px.scatter(
            df_mapa,
            x="Área Cultivada (mi ha)",
            y="Produtividade (sc/ha)",
            size="Área Cultivada (mi ha)",
            color="Estado",
            hover_name="Estado",
            trendline="lowess",
            template="plotly_dark",
            height=430
        ), use_container_width=True)

    # --- Exportação de Dados ---
    st.divider()

    with st.expander("💾 Exportar Dados Geoespaciais", expanded=False):
        export_formats = {
            "GeoJSON": ("geojson", "application/geo+json"),
            "Shapefile": ("zip", "application/zip"),
            "CSV": ("csv", "text/csv")
        }
        
        format_type = st.radio("Formato", list(export_formats.keys()), horizontal=True)
        
        if format_type == "GeoJSON":
            data = json.dumps(estados_geo)
        elif format_type == "Shapefile":
            # Conversão para Shapefile (requer geopandas)
            gdf = gpd.GeoDataFrame.from_features(estados_geo['features'])
            with BytesIO() as buffer:
                with zipfile.ZipFile(buffer, 'w') as zipf:
                    for ext in ['shp', 'prj', 'dbf', 'shx']:
                        gdf.to_file(f"dados.{ext}", driver='ESRI Shapefile')
                        zipf.write(f"dados.{ext}")
                data = buffer.getvalue()
        else:
            data = df_mapa.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label=f"⬇️ Exportar como {format_type}",
            data=data,
            file_name=f"produtividade_agro.{export_formats[format_type][0]}",
            mime=export_formats[format_type][1]
        )

with tab3:
    st.subheader("🔍 DASHBOARD ANALÍTICO AVANÇADO")
    
    # --- Filtros Interativos ---
    col1, col2, col3 = st.columns(3)
    with col1:
        commodity_filter = st.multiselect(
            "Selecione as Commodities",
            options=df.columns,
            default=df.columns.tolist(),
            key="commodity_filter"
        )
    with col2:
        date_range = st.date_input(
            "Período",
            value=[df.index.min(), df.index.max()],
            min_value=df.index.min(),
            max_value=df.index.max(),
            key="date_range"
        )
    with col3:
        metric_view = st.radio(
            "Visualização",
            options=["Tabela Dinâmica", "Gráfico Temporal", "Análise Comparativa"],
            horizontal=True,
            key="metric_view"
        )
    
    # Filtra os dados
    filtered_df = df[commodity_filter].loc[date_range[0]:date_range[1]]
    
    # --- Visualizações Condicionais ---
    if metric_view == "Tabela Dinâmica":
        st.markdown("### 📊 TABELA INTERATIVA")
        
        # Tabela estilizada com Plotly
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['<b>Data</b>'] + [f'<b>{col}</b>' for col in filtered_df.columns],
                fill_color='#1a2a6c',
                align=['left'] + ['center']*len(filtered_df.columns),
                font=dict(color='white', size=14),
                height=40
            ),
            cells=dict(
                values=[filtered_df.index.strftime('%d/%m/%Y')] + [filtered_df[col].round(2) for col in filtered_df.columns],
                fill_color='rgba(26, 42, 108, 0.3)',
                align=['left'] + ['center']*len(filtered_df.columns),
                font=dict(color='white', size=12),
                height=35,
                format=[None] + [',.2f']*len(filtered_df.columns)
            )
        )])
        
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=min(600, 35 * (len(filtered_df) + 1)),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Funções de análise rápida
        with st.expander("🔍 ANÁLISE RÁPIDA", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="Maior Valor",
                    value=f"R$ {filtered_df.max().max():,.2f}",
                    delta=f"{filtered_df.idxmax().name} - {filtered_df.max().idxmax()}"
                )
            with col2:
                st.metric(
                    label="Menor Valor",
                    value=f"R$ {filtered_df.min().min():,.2f}",
                    delta=f"{filtered_df.idxmin().name} - {filtered_df.min().idxmin()}"
                )
            
            st.progress(value=float(filtered_df.iloc[-1].mean()/filtered_df.max().mean()), 
                        text=f"Média atual: R$ {filtered_df.iloc[-1].mean():,.2f}")
        
    elif metric_view == "Gráfico Temporal":
        st.markdown("### 📈 ANÁLISE TEMPORAL")
        
        fig = px.line(
            filtered_df.reset_index().melt(id_vars='Data'),
            x='Data',
            y='value',
            color='variable',
            height=500,
            template='plotly_dark',
            color_discrete_sequence=px.colors.qualitative.Plotly,
            labels={'value': 'Preço (R$/sc 60kg)', 'variable': 'Commodity'}
        )
        
        fig.update_layout(
            hovermode="x unified",
            legend_title_text=None,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(rangeslider=dict(visible=True))
        )
        
        # Adiciona médias móveis
        for col in commodity_filter:
            fig.add_scatter(
                x=filtered_df.index,
                y=filtered_df[col].rolling(3).mean(),
                mode='lines',
                line=dict(dash='dot', width=1),
                name=f'Média {col}',
                showlegend=False,
                hoverinfo='skip'
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.markdown("### ⚖️ ANÁLISE COMPARATIVA")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.box(
                filtered_df.melt(ignore_index=False).reset_index(),
                x='variable',
                y='value',
                color='variable',
                template='plotly_dark',
                title='Distribuição de Preços',
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            fig = px.scatter(
                filtered_df.reset_index(),
                x=commodity_filter[0],
                y=commodity_filter[1] if len(commodity_filter) > 1 else commodity_filter[0],
                trendline="ols",
                template='plotly_dark',
                title='Relação entre Commodities',
                color_discrete_sequence=['#3a7bd5']
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # --- Módulo de Exportação ---
    with st.expander("📤 EXPORTAR DADOS", expanded=False):
        export_col1, export_col2 = st.columns([3,1])
        
        with export_col1:
            export_format = st.radio(
                "Formato de Exportação",
                options=["CSV", "Excel", "JSON"],
                horizontal=True,
                key="export_format"
            )
            
        with export_col2:
            st.download_button(
                label=f"⬇️ Exportar ({export_format})",
                data=convert_df(filtered_df, export_format),
                file_name=f"agro_data_{datetime.now().strftime('%Y%m%d')}.{export_format.lower()}",
                mime=f"text/{export_format.lower()}" if export_format != "Excel" else "application/vnd.ms-excel",
                key="download_button"
            )

# --- Rodapé Tecnológico ---
st.markdown("---")
st.markdown("""
<div style="text-align:center;opacity:0.7;font-size:0.9em;margin-top:2rem;">
    <p>© 2024 AGROTECH INTELLIGENCE | <strong>DADOS ILUSTRATIVOS</strong> PARA FINS DEMONSTRATIVOS</p>
    <p style="font-size:0.8em;">SIMULAÇÃO DE INTEGRAÇÃO COM FONTES: CONAB, MAPA, IBGE E BOLSAS INTERNACIONAIS</p>
    <p style="font-size:0.75em;border-top:1px solid rgba(255,255,255,0.1);padding-top:0.5rem;">
        Os valores apresentados são exemplos hipotéticos para demonstração da plataforma
    </p>
</div>
""", unsafe_allow_html=True)
