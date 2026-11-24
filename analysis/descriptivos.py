"""Análisis descriptivo."""
import numpy as np
import pandas as pd


def resumen_area(series):
    s = pd.Series(series).dropna()
    return {
        "n": len(s),
        "media": s.mean(),
        "mediana": s.median(),
        "sd": s.std(ddof=0),
        "min": s.min(),
        "max": s.max(),
        "q1": s.quantile(0.25),
        "q3": s.quantile(0.75),
        "iqr": s.quantile(0.75) - s.quantile(0.25),
        "cv": s.std(ddof=0) / s.mean() * 100 if s.mean() != 0 else np.nan,
        "skew": s.skew(),
        "kurt": s.kurtosis(),
    }


def resumen_por_area(df_est, areas):
    rows = []
    for a in areas:
        r = resumen_area(df_est[a])
        r["area"] = a
        rows.append(r)
    return pd.DataFrame(rows).set_index("area")


def resumen_por_grupo(df_est, areas):
    rows = []
    for g in sorted(df_est["Grupo"].unique()):
        sub = df_est[df_est["Grupo"] == g]
        for a in areas:
            r = resumen_area(sub[a])
            r["grupo"] = g
            r["area"] = a
            rows.append(r)
    return pd.DataFrame(rows)


def clasificar_riesgo(df_est, areas, umbral=50):
    df = df_est.copy()
    weak = []
    for _, row in df.iterrows():
        ws = [a for a in areas if row[a] < 60]
        weak.append(", ".join(ws) if ws else "-")
    df["areas_debiles"] = weak
    df["riesgo"] = (
        (df[areas] < umbral).sum(axis=1) >= 2
    ) | (df["Física"] < 40) | (df["Biología"] < 50)
    motivos = []
    for _, row in df.iterrows():
        m = []
        if row["Física"] < 40:
            m.append("Física<40")
        if row["Biología"] < 50:
            m.append("Biología<50")
        if (row[areas] < umbral).sum() >= 2:
            m.append(f">=2 áreas<{umbral}")
        if row["CTS"] < 60:
            m.append("CTS<60")
        motivos.append("; ".join(m) if m else "-")
    df["motivo"] = motivos
    return df


def z_scores(df_est, areas):
    df = df_est.copy()
    for a in areas:
        mu = df[a].mean()
        sd = df[a].std(ddof=0)
        df[f"z_{a}"] = (df[a] - mu) / sd
    return df