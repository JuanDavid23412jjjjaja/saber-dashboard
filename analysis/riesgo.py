"""Análisis de riesgo."""
import numpy as np
import pandas as pd
from analysis.descriptivos import z_scores


def perfil_estudiante(df_est, nombre, areas):
    row = df_est[df_est["Nombre"] == nombre]
    if row.empty:
        return None
    row = row.iloc[0]
    return {a: row[a] for a in areas}


def ranking(df_est, area):
    return df_est.sort_values(area, ascending=False)[["Nombre", "Grupo", area]].reset_index(drop=True)


def estudiantes_bajo_umbral(df_est, areas, umbral):
    mask = (df_est[areas] < umbral).any(axis=1)
    return df_est[mask].copy()
