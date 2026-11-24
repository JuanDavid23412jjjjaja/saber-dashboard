"""Carga de datos desde el Google Sheet del Simulacro SABER AR1."""
import json
import os
import requests
import gspread
import pandas as pd
import streamlit as st
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SHEET_ID = "100iQLezFA10KTbd2nHpLQTfCduUnkPq5C00G4q_Sto8"
TOKEN_PATH = os.path.expanduser("~/.config/google-workspace-mcp/tokens.json")
CLIENT_ID = "812463761660-dmr9nk7e5adtrmabhq44bfk3bnu0g36v.apps.googleusercontent.com"
CLIENT_SECRET = None  # se resuelve desde secrets/env o token.json (local)

def _get_secret(key, default=None):
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


def _resolve_client_secret():
    s = _get_secret("GOOGLE_CLIENT_SECRET")
    if s:
        return s
    # fallback local: leer del token.json
    try:
        with open(TOKEN_PATH) as f:
            tok = json.load(f)
        return tok.get("client_secret", CLIENT_SECRET)
    except Exception:
        return CLIENT_SECRET

AREAS = ["Biología", "Química", "Física", "CTS"]
AREA_KEY = {"Biología": "biologia", "Química": "quimica", "Física": "fisica", "CTS": "cts"}


def _creds():
    # 1) Intentar secrets/env (Streamlit Cloud)
    rt = _get_secret("GOOGLE_REFRESH_TOKEN")
    cid = _get_secret("GOOGLE_CLIENT_ID", CLIENT_ID)
    csec = _resolve_client_secret()
    if rt:
        data = {"client_id": cid, "client_secret": csec, "refresh_token": rt, "grant_type": "refresh_token"}
        r = requests.post("https://oauth2.googleapis.com/token", data=data)
        r.raise_for_status()
        new = r.json()
        return Credentials(token=new["access_token"])
    # 2) Fallback archivo local
    with open(TOKEN_PATH) as f:
        tok = json.load(f)
    data = {
        "client_id": CLIENT_ID,
        "client_secret": _resolve_client_secret(),
        "refresh_token": tok["refresh_token"],
        "grant_type": "refresh_token",
    }
    r = requests.post("https://oauth2.googleapis.com/token", data=data)
    r.raise_for_status()
    new = r.json()
    tok["access_token"] = new["access_token"]
    tok["expires_in"] = new.get("expires_in", 3600)
    try:
        with open(TOKEN_PATH, "w") as f:
            json.dump(tok, f, indent=2)
    except Exception:
        pass
    return Credentials(token=new["access_token"])


@st.cache_data(ttl=300, show_spinner="Cargando datos del Sheet...")
def load_all():
    creds = _creds()
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)

    def tab(name):
        ws = sh.worksheet(name)
        data = ws.get_all_values()
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])

    df_est = tab("RAW_ESTUDIANTES")
    df_items = tab("RAW_ITEMS")
    df_comp = tab("COMPETENCIAS")
    df_compo = tab("COMPONENTES")
    df_riesgo = tab("RIESGO")
    df_plan = tab("PLAN_MEJORAMIENTO")

    # Tipos
    for c in ["Biología", "Química", "Física", "CTS"]:
        if c in df_est.columns:
            df_est[c] = pd.to_numeric(df_est[c], errors="coerce")
    df_est["Grupo"] = df_est["Grupo"].astype(str)
    for c in ["%Nac", "%Plan"]:
        if c in df_items.columns:
            df_items[c] = pd.to_numeric(df_items[c], errors="coerce")
    for c in ["Nac Prom", "Plantel Prom", "Nac Desv", "Plantel Desv"]:
        if c in df_comp.columns:
            df_comp[c] = pd.to_numeric(df_comp[c], errors="coerce")
        if c in df_compo.columns:
            df_compo[c] = pd.to_numeric(df_compo[c], errors="coerce")
    if "Brecha (Plantel-Nac)" in df_comp.columns:
        df_comp["Brecha"] = pd.to_numeric(df_comp["Brecha (Plantel-Nac)"], errors="coerce")
    if "Brecha (Plantel-Nac)" in df_compo.columns:
        df_compo["Brecha"] = pd.to_numeric(df_compo["Brecha (Plantel-Nac)"], errors="coerce")

    df_est["Prom4"] = df_est[AREAS].mean(axis=1)
    df_est["Riesgo"] = (
        (df_est[AREAS] < 50).sum(axis=1) >= 2
    ) | (df_est["Física"] < 40) | (df_est["Biología"] < 50)

    return {
        "est": df_est,
        "items": df_items,
        "comp": df_comp,
        "compo": df_compo,
        "riesgo": df_riesgo,
        "plan": df_plan,
    }


def load_local_fallback():
    """Carga desde CSVs locales si no hay conexión."""
    base = os.path.expanduser("~/saber-dashboard/data/cache")
    est = pd.read_csv(os.path.join(base, "estudiantes.csv"))
    items = pd.read_csv(os.path.join(base, "items.csv"))
    for c in AREAS:
        est[c] = pd.to_numeric(est[c], errors="coerce")
    items["%Nac"] = pd.to_numeric(items["%Nac"], errors="coerce")
    items["%Plan"] = pd.to_numeric(items["%Plan"], errors="coerce")
    est["Prom4"] = est[AREAS].mean(axis=1)
    est["Riesgo"] = ((est[AREAS] < 50).sum(axis=1) >= 2) | (est["Física"] < 40) | (est["Biología"] < 50)
    return {"est": est, "items": items, "comp": None, "compo": None, "riesgo": None, "plan": None}