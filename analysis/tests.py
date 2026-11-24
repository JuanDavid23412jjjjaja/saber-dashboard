"""Pruebas estadísticas."""
import numpy as np
import pandas as pd
from scipy import stats


def normalidad(series):
    s = pd.Series(series).dropna()
    if len(s) < 3 or len(s) > 5000:
        return {"test": "Shapiro-Wilk", "stat": np.nan, "p": np.nan, "normal": None}
    stat, p = stats.shapiro(s)
    return {"test": "Shapiro-Wilk", "stat": stat, "p": p, "normal": p > 0.05}


def levene(*groups):
    stat, p = stats.levene(*[np.asarray(g).ravel() for g in groups])
    return {"test": "Levene", "stat": stat, "p": p, "homogeneo": p > 0.05}


def comparar_dos(grupo1, grupo2):
    g1 = np.asarray(grupo1).ravel()
    g2 = np.asarray(grupo2).ravel()
    n1 = normalidad(g1)["normal"]
    n2 = normalidad(g2)["normal"]
    lev = levene(g1, g2)
    if n1 and n2:
        if lev["homogeneo"]:
            stat, p = stats.ttest_ind(g1, g2, equal_var=True)
            metodo = "t-test (varianzas iguales)"
        else:
            stat, p = stats.ttest_ind(g1, g2, equal_var=False)
            metodo = "t-test Welch"
    else:
        stat, p = stats.mannwhitneyu(g1, g2, alternative="two-sided")
        metodo = "Mann-Whitney U"
    # Cohen's d
    pooled = np.sqrt(((len(g1) - 1) * g1.std(ddof=1) ** 2 + (len(g2) - 1) * g2.std(ddof=1) ** 2) / (len(g1) + len(g2) - 2))
    d = (g1.mean() - g2.mean()) / pooled if pooled != 0 else np.nan
    return {
        "metodo": metodo,
        "stat": stat,
        "p": p,
        "significativo": p < 0.05,
        "cohens_d": d,
        "media1": g1.mean(),
        "media2": g2.mean(),
        "n1": len(g1),
        "n2": len(g2),
    }


def anova_un_factor(df, value_col, group_col):
    groups = [g[value_col].values for _, g in df.groupby(group_col)]
    if len(groups) < 2:
        return {"metodo": "N/A", "stat": np.nan, "p": np.nan}
    # normalidad por grupo
    normals = [normalidad(g)["normal"] for g in groups]
    if all(n for n in normals if n is not None and n):
        stat, p = stats.f_oneway(*groups)
        metodo = "ANOVA de un factor"
    else:
        stat, p = stats.kruskal(*groups)
        metodo = "Kruskal-Wallis"
    return {"metodo": metodo, "stat": stat, "p": p, "significativo": p < 0.05, "normales": normals}


def correlacion(df, cols, method="pearson"):
    return df[cols].corr(method=method)


def chi_cuadrado_independencia(tabla):
    chi2, p, dof, expected = stats.chi2_contingency(tabla)
    return {"chi2": chi2, "p": p, "dof": dof, "significativo": p < 0.05}


def tukey_posthoc(df, value_col, group_col):
    try:
        from statsmodels.stats.multicomp import pairwise_tukeyhsd
        res = pairwise_tukeyhsd(df[value_col], df[group_col], alpha=0.05)
        return res
    except Exception as e:
        return str(e)
