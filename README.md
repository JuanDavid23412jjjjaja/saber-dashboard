# Megadashboard — Simulacro SABER AR1 (Grado 10°)

Dashboard Streamlit para análisis profundo del simulacro SABER AR1, foco en Biología, Química, Física y CTS.

## Ejecutar

```bash
cd ~/saber-dashboard
pip install -r requirements.txt
streamlit run app.py
```

Abrir: http://localhost:8501 (o http://100.115.92.206:8501 en Chrome OS).

## Datos

Lee en tiempo real del Google Sheet:
https://docs.google.com/spreadsheets/d/100iQLezFA10KTbd2nHpLQTfCduUnkPq5C00G4q_Sto8/edit

Autenticación vía token OAuth en `~/.config/google-workspace-mcp/tokens.json`.

## Pestañas

Resumen · Por área · Competencias/Componentes · Ítems · Estudiantes · Riesgo · Grupos · Pruebas estadísticas · Plan de mejoramiento

## Filtros (sidebar)

Áreas, grupos, umbral de riesgo, dificultad de ítems, competencia/componente, solo críticos, mostrar pruebas.

## Pruebas estadísticas incluidas

Shapiro-Wilk (normalidad), Levene (homogeneidad), t-test/Mann-Whitney (grupos), ANOVA/Kruskal-Wallis (áreas), Pearson/Spearman (correlación), chi-cuadrado (dificultad × oportunidad), Cohen's d.
EOF