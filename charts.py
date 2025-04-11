import plotly.graph_objects as go
import pandas as pd

def create_interactive_table(df: pd.DataFrame):
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(df.columns),
            fill_color='#1a2a6c',
            font=dict(color='white', size=12),
            align='center',
            height=40
        ),
        cells=dict(
            values=[df[col] for col in df.columns],
            fill_color='rgba(58, 123, 213, 0.1)',
            align=['left', 'center', 'right'],  # Ajuste por tipo de dado
            font=dict(color='white', size=11),
            height=35
        )
    )])
    fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))
    return fig