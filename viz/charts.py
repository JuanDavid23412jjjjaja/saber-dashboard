"""Visualizaciones Plotly."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

AREAS = ["Biología", "Química", "Física", "CTS"]
COLORS = {"Biología": "#2ecc71", "Química": "#3498db", "Física": "#e74c3c", "CTS": "#9b59b6"}


def boxplot_area(df_est, areas=None):
    areas = areas or AREAS
    df = df_est.melt(id_vars=["Nombre", "Grupo"], value_vars=areas, var_name="Área", value_name="Puntaje")
    fig = px.box(df, x="Área", y="Puntaje", color="Área", points="all",
                 color_discrete_map=COLORS, title="Distribución por área (boxplot)")
    fig.update_layout(showlegend=False)
    return fig


def violin_grupo(df_est, area):
    fig = px.violin(df_est, x="Grupo", y=area, color="Grupo", box=True, points="all",
                    title=f"{area}: Grupo 1 vs Grupo 2")
    return fig


def scatter_corr(df_est, x, y):
    fig = px.scatter(df_est, x=x, y=y, color="Grupo", trendline="ols",
                     title=f"{x} vs {y}", color_discrete_sequence=["#e74c3c", "#3498db"])
    return fig


def heatmap_matrix(df, index_col, value_col, title):
    pivot = df.pivot(index=index_col, columns="Área", values=value_col) if "Área" in df.columns else None
    if pivot is None:
        return go.Figure()
    fig = px.imshow(pivot, text_auto=".1f", aspect="auto", color_continuous_scale="RdYlGn",
                    title=title, zmin=20, zmax=95)
    return fig


def tendencia_items(df_items, area):
    sub = df_items[df_items["Área"] == area].reset_index(drop=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sub.index, y=sub["%Plan"], mode="lines+markers", name="%Plan",
                             line=dict(color=COLORS[area], width=2)))
    fig.add_trace(go.Scatter(x=sub.index, y=sub["%Nac"], mode="lines+markers", name="%Nac",
                             line=dict(color=COLORS[area], width=1, dash="dash")))
    fig.update_layout(title=f"Tendencia por ítem — {area}", xaxis_title="Ítem (orden)", yaxis_title="%")
    return fig


def barras_brecha(df_comp):
    df = df_comp.copy()
    df["brecha"] = df["Plantel Prom"] - df["Nac Prom"]
    fig = px.bar(df, x="Competencia", y="brecha", color="Área", title="Brecha (Plantel - Nacional) por competencia",
                 color_discrete_map=COLORS)
    fig.update_layout(xaxis_tickangle=-30)
    return fig


def hist_kde(df_est, area):
    fig = px.histogram(df_est, x=area, nbins=10, marginal="box", title=f"Distribución — {area}")
    return fig


def radar_estudiante(valores, areas, nombre):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=valores + [valores[0]], theta=areas + [areas[0]], fill="toself", name=nombre))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title=f"Perfil: {nombre}")
    return fig
