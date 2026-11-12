
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

D = Path(__file__).parent
st.set_page_config(page_title="Alerta temprana de inflación – Lima", layout="wide")
p = json.loads((D / "pronostico_operativo.json").read_text(encoding="utf-8"))
hist = pd.read_csv(D / "serie_historica_ipc.csv", parse_dates=["fecha"])
oos = pd.read_csv(D / "predicciones_fuera_de_muestra.csv")
reg = pd.read_csv(D / "registro_predicciones.csv")
imp = pd.read_csv(D / "importancia_variables.csv")
COL = {"Baja": "#2e9e5b", "Media": "#f0a30a", "Alta": "#d64545"}

st.title("Sistema de alerta temprana – inflación mensual de Lima Metropolitana")
st.caption("Prototipo académico. No sustituye las estadísticas ni evaluaciones oficiales del BCRP o del INEI.")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Mes pronosticado", p["periodo_objetivo"])
c2.metric("Inflación estimada", f"{p['prediccion']:.2f} %", f"IC90 [{p['p05']:.2f}; {p['p95']:.2f}]", delta_color="off")
c3.markdown(f"### Alerta: <span style='color:{COL[p['alerta']]}'>{p['alerta'].upper()}</span>", unsafe_allow_html=True)
c4.metric("MAE (prueba)", f"{p['mae_prueba']:.3f} pp")

anios = st.slider("Años de historia", 2, 20, 10)
h = hist[hist["fecha"] >= hist["fecha"].max() - pd.DateOffset(years=anios)]
cols = [c for c in oos.columns if c.startswith("pred_")]
sel = st.multiselect("Predicciones fuera de muestra", cols, default=[f"pred_{p['modelo']}", "pred_Persistencia"])
fig = go.Figure(go.Scatter(x=h["fecha"], y=h["ipc"], name="IPC observado"))
x = pd.to_datetime(oos["periodo_objetivo"])
for c in sel:
    fig.add_trace(go.Scatter(x=x, y=oos[c], name=c.replace("pred_", ""), mode="lines+markers"))
fig.add_trace(go.Scatter(x=[pd.to_datetime(p["periodo_objetivo"])], y=[p["prediccion"]], mode="markers", name="Pronóstico",
                         marker=dict(size=14, color=COL[p["alerta"]], symbol="diamond")))
fig.add_hline(y=p["P33"], line_dash="dash", line_color="green"); fig.add_hline(y=p["P67"], line_dash="dash", line_color="red")
st.plotly_chart(fig, use_container_width=True)

a, b = st.columns(2)
a.subheader("Probabilidad por nivel")
a.bar_chart(pd.Series({"Baja": p["prob_baja"], "Media": p["prob_media"], "Alta": p["prob_alta"]}))
b.subheader("Variables más influyentes")
b.bar_chart(imp.head(10).set_index("variable")["importancia (ΔMAE)"])
st.subheader("Registro de predicciones emitidas vs. observado")
st.dataframe(reg.tail(24), use_container_width=True)
