import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from data.loader import load_all, AREAS
from analysis.descriptivos import resumen_por_area, resumen_por_grupo, clasificar_riesgo, z_scores
from analysis.tests import normalidad, levene, comparar_dos, anova_un_factor, correlacion, chi_cuadrado_independencia
from analysis.riesgo import ranking, estudiantes_bajo_umbral
from viz.charts import (boxplot_area, violin_grupo, scatter_corr, heatmap_matrix,
                        tendencia_items, barras_brecha, hist_kde, radar_estudiante)

st.set_page_config(page_title="SABER AR1 - Megadashboard", layout="wide", page_icon="📊")

# ---------- carga ----------
try:
    data = load_all()
except Exception as e:
    st.error(f"No se pudo cargar el Sheet: {e}")
    st.stop()

df_est = data["est"]
df_items = data["items"]
df_comp = data["comp"]
df_compo = data["compo"]
df_riesgo = data["riesgo"]
df_plan = data["plan"]

# ---------- sidebar ----------
st.sidebar.title("Filtros")
areas_sel = st.sidebar.multiselect("Áreas", AREAS, default=AREAS)
grupos_sel = st.sidebar.multiselect("Grupos", ["1", "2"], default=["1", "2"])
umbral = st.sidebar.slider("Umbral de riesgo", 30, 70, 50)
dif_sel = st.sidebar.multiselect("Dificultad de ítems",
    ["Bajo", "Básico", "Alto", "Superior"], default=["Bajo", "Básico", "Alto", "Superior"])
solo_criticos = st.sidebar.toggle("Solo ítems críticos (<50%)", value=False)
mostrar_tests = st.sidebar.toggle("Mostrar pruebas estadísticas", value=True)
comp_sel = st.sidebar.selectbox("Competencia (heatmap)", ["Todas"] + sorted(df_comp["Competencia"].unique().tolist()))
compo_sel = st.sidebar.selectbox("Componente", ["Todos"] + sorted(df_compo["Componente"].unique().tolist()))

# filtrar estudiantes
mask_est = df_est["Grupo"].isin(grupos_sel)
df_est_f = df_est[mask_est].copy()
# filtrar items
mask_it = df_items["Área"].isin(areas_sel) & df_items["Dificultad"].isin(dif_sel)
if solo_criticos:
    mask_it = mask_it & (df_items["%Plan"] < 50)
df_items_f = df_items[mask_it].copy()

st.title("📊 Megadashboard — Simulacro SABER AR1 (Grado 10°)")
st.caption("Foco: Biología, Química, Física, CTS · Plantel: Colegio San Bonifacio De Las Lanzas · Fecha 24/11/2026")

# ---------- tabs ----------
tabs = st.tabs(["Resumen", "Por área", "Competencias/Componentes", "Ítems", "Estudiantes",
                "Riesgo", "Grupos", "Pruebas estadísticas", "Plan de mejoramiento"])

# ===== Resumen =====
with tabs[0]:
    st.subheader("KPIs por área")
    cols = st.columns(len(areas_sel) if areas_sel else 1)
    for i, a in enumerate(areas_sel):
        sub = df_est_f[a].dropna()
        r = resumen_por_area(df_est_f, [a]).iloc[0]
        with cols[i]:
            st.metric(a, f"{r['media']:.1f}", delta=f"sd {r['sd']:.1f}")
            st.caption(f"n={r['n']} · min {r['min']:.0f} · max {r['max']:.0f} · med {r['mediana']:.1f}")
    st.plotly_chart(boxplot_area(df_est_f, areas_sel), width="stretch", key="chart_0")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top 5 por área seleccionada")
        if areas_sel:
            a0 = areas_sel[0]
            st.dataframe(ranking(df_est_f, a0).head(5), width="stretch")
    with c2:
        st.subheader("Bottom 5")
        if areas_sel:
            a0 = areas_sel[0]
            st.dataframe(ranking(df_est_f, a0).tail(5), width="stretch")

# ===== Por área =====
with tabs[1]:
    area_sel = st.selectbox("Área", areas_sel if areas_sel else AREAS)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(hist_kde(df_est_f, area_sel), width="stretch", key="chart_1")
    with col2:
        st.plotly_chart(violin_grupo(df_est_f, area_sel), width="stretch", key="chart_2")
    st.plotly_chart(tendencia_items(df_items, area_sel), width="stretch", key="chart_3")
    st.subheader("Estadísticos descriptivos")
    r = resumen_por_area(df_est_f, [area_sel]).iloc[0].to_dict()
    st.json({k: (round(v, 3) if isinstance(v, (int, float, np.floating)) else v) for k, v in r.items()})

# ===== Competencias/Componentes =====
with tabs[2]:
    st.subheader("Competencias: Plantel vs Nacional")
    dfc = df_comp[df_comp["Área"].isin(areas_sel)].copy()
    if comp_sel != "Todas":
        dfc = dfc[dfc["Competencia"] == comp_sel]
    st.plotly_chart(barras_brecha(dfc), width="stretch", key="chart_4")
    st.dataframe(dfc[["Área", "Competencia", "Nac Prom", "Plantel Prom", "Brecha", "Nac Desv", "Plantel Desv"]],
                 width="stretch")
    st.subheader("Heatmap competencias (Plantel)")
    try:
        fig = px.imshow(dfc.pivot(index="Competencia", columns="Área", values="Plantel Prom"),
                        text_auto=".1f", aspect="auto", color_continuous_scale="RdYlGn", zmin=20, zmax=95)
        st.plotly_chart(fig, width="stretch", key="chart_5")
    except Exception:
        st.info("No hay suficientes datos para el heatmap.")
    st.subheader("Componentes")
    dfco = df_compo[df_compo["Área"].isin(areas_sel)].copy()
    if compo_sel != "Todos":
        dfco = dfco[dfco["Componente"] == compo_sel]
    st.dataframe(dfco[["Área", "Componente", "Nac Prom", "Plantel Prom", "Brecha", "Plantel Desv"]],
                 width="stretch")

# ===== Ítems =====
with tabs[3]:
    st.subheader(f"Ítems filtrados: {len(df_items_f)}")
    st.dataframe(df_items_f[["Área", "Nro", "Competencia", "Componente", "Dificultad",
                             "%Nac", "%Plan", "Oportunidad Mejora", "Tarea"]],
                 width="stretch")
    if len(df_items_f) > 0:
        fig = px.scatter(df_items_f, x="%Nac", y="%Plan", color="Área", size="%Plan",
                         hover_data=["Nro", "Dificultad", "Tarea"], title="Ítems: %Nac vs %Plan")
        fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(dash="dash", color="gray"))
        st.plotly_chart(fig, width="stretch", key="chart_6")

# ===== Estudiantes =====
with tabs[4]:
    st.subheader("Tabla de estudiantes")
    cols_show = ["Nombre", "Grupo", "Código"] + areas_sel + ["Prom4", "Riesgo"]
    cols_show = [c for c in cols_show if c in df_est_f.columns]
    st.dataframe(df_est_f[cols_show].sort_values("Prom4", ascending=False), width="stretch")
    st.subheader("Perfil individual")
    nombre_sel = st.selectbox("Estudiante", df_est_f["Nombre"].tolist())
    vals = [df_est_f[df_est_f["Nombre"] == nombre_sel][a].values[0] for a in AREAS]
    st.plotly_chart(radar_estudiante(vals, AREAS, nombre_sel), width="stretch", key="chart_7")
    if mostrar_tests:
        st.subheader("Z-scores del estudiante seleccionado")
        zdf = z_scores(df_est_f, AREAS)
        row = zdf[zdf["Nombre"] == nombre_sel]
        st.dataframe(row[[f"z_{a}" for a in AREAS]], width="stretch")

# ===== Riesgo =====
with tabs[5]:
    df_risk = clasificar_riesgo(df_est_f, areas_sel if areas_sel else AREAS, umbral)
    df_risk = df_risk[df_risk["riesgo"] == True]
    st.subheader(f"Estudiantes en riesgo: {len(df_risk)}")
    st.dataframe(df_risk[["Nombre", "Grupo", "Biología", "Química", "Física", "CTS", "Prom4",
                          "areas_debiles", "motivo"]], width="stretch")
    csv = df_risk.to_csv(index=False).encode("utf-8")
    st.download_button("Descargar CSV de riesgo", csv, "riesgo.csv", "text/csv")

# ===== Grupos =====
with tabs[6]:
    st.subheader("Comparación Grupo 1 vs Grupo 2")
    if len(grupos_sel) == 2:
        area_g = st.selectbox("Área para comparar", areas_sel if areas_sel else AREAS, key="area_grupo")
        g1 = df_est[df_est["Grupo"] == "1"][area_g].dropna()
        g2 = df_est[df_est["Grupo"] == "2"][area_g].dropna()
        st.plotly_chart(violin_grupo(df_est, area_g), width="stretch", key="chart_8")
        res = comparar_dos(g1, g2)
        st.json({k: (round(v, 4) if isinstance(v, (int, float, np.floating)) else v) for k, v in res.items()})
        if mostrar_tests:
            st.subheader("Normalidad por grupo")
            st.write("Grupo 1:", normalidad(g1))
            st.write("Grupo 2:", normalidad(g2))
            st.write("Levene:", levene(g1, g2))
    else:
        st.info("Selecciona ambos grupos en el sidebar para comparar.")

# ===== Pruebas estadísticas =====
with tabs[7]:
    if mostrar_tests:
        st.subheader("Correlaciones entre áreas")
        corr_df = correlacion(df_est_f, areas_sel if areas_sel else AREAS, method="pearson")
        st.dataframe(corr_df.round(3), width="stretch")
        fig = px.imshow(corr_df, text_auto=".2f", color_continuous_scale="RdBu", zmin=-1, zmax=1,
                        title="Matriz de correlación (Pearson)")
        st.plotly_chart(fig, width="stretch", key="chart_9")

        st.subheader("ANOVA / Kruskal-Wallis entre áreas")
        df_long = df_est_f.melt(id_vars=["Nombre", "Grupo"], value_vars=areas_sel if areas_sel else AREAS,
                                var_name="Área", value_name="Puntaje")
        anova_res = anova_un_factor(df_long, "Puntaje", "Área")
        st.json({k: (round(v, 4) if isinstance(v, (int, float, np.floating)) else v) for k, v in anova_res.items()})

        st.subheader("Normalidad por área (Shapiro-Wilk)")
        for a in (areas_sel if areas_sel else AREAS):
            st.write(a, normalidad(df_est_f[a]))

        st.subheader("Homogeneidad de varianzas (Levene) entre áreas")
        groups = [df_est_f[a].dropna().values for a in (areas_sel if areas_sel else AREAS)]
        st.write(levene(*groups))

        st.subheader("Chi-cuadrado: Dificultad × Oportunidad de mejora")
        if len(df_items_f) > 0:
            tabla = pd.crosstab(df_items_f["Dificultad"], df_items_f["Oportunidad Mejora"])
            st.dataframe(tabla, width="stretch")
            try:
                chi = chi_cuadrado_independencia(tabla)
                st.json({k: (round(v, 4) if isinstance(v, (int, float, np.floating)) else v) for k, v in chi.items()})
            except Exception as e:
                st.warning(str(e))
    else:
        st.info("Activa 'Mostrar pruebas estadísticas' en el sidebar.")

# ===== Plan de mejoramiento =====
with tabs[8]:
    st.subheader("Plan de mejoramiento priorizado")
    st.dataframe(df_plan, width="stretch")

st.sidebar.markdown("---")
st.sidebar.caption("Datos: Google Sheet SABER AR1 · Cache 5 min")
