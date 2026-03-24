import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import io

st.set_page_config(layout="wide", page_title="Gestão Manual de Rotas")

# -----------------------------
# Estado inicial
# -----------------------------
if "colaboradores" not in st.session_state:
    st.session_state["colaboradores"] = pd.DataFrame()

if "rotas" not in st.session_state:
    st.session_state["rotas"] = {}  # {nome_rota: [lista de colaboradores]}

if "rota_atual" not in st.session_state:
    st.session_state["rota_atual"] = None

# -----------------------------
# Upload
# -----------------------------
st.sidebar.header("📂 Upload")
xlsx = st.sidebar.file_uploader("Colaboradores", type=["xlsx"])

if xlsx:
    st.session_state["colaboradores"] = pd.read_excel(xlsx)

# -----------------------------
# Criar nova rota
# -----------------------------
st.sidebar.header("🛣️ Rotas")
nova_rota = st.sidebar.text_input("Nome da nova rota")
if st.sidebar.button("Criar rota"):
    if nova_rota and nova_rota not in st.session_state["rotas"]:
        st.session_state["rotas"][nova_rota] = []
        st.session_state["rota_atual"] = nova_rota
        st.success(f"Rota '{nova_rota}' criada e selecionada.")

rota_selecionada = st.sidebar.selectbox("Selecionar rota para edição", list(st.session_state["rotas"].keys()))
if rota_selecionada:
    st.session_state["rota_atual"] = rota_selecionada

# -----------------------------
# Mapa
# -----------------------------
st.title("🗺️ Gestão Manual de Rotas")

if not st.session_state["colaboradores"].empty:
    m = folium.Map(location=[-3.119, -60.021], zoom_start=12)
    cluster = MarkerCluster().add_to(m)

    for _, row in st.session_state["colaboradores"].iterrows():
        nome = row["COLABORADORES"]
        lat, lon = row["LAT"], row["LONG"]

        # Verifica se colaborador já está em alguma rota
        rota_do_colab = None
        for rota, membros in st.session_state["rotas"].items():
            if nome in membros:
                rota_do_colab = rota
                break

        popup_html = f"""
        <b>{nome}</b><br>
        Rota: {rota_do_colab if rota_do_colab else "Nenhuma"}<br>
        <a href="javascript:window.parent.postMessage({{'add_colab':'{nome}'}}, '*')">Adicionar à rota atual</a><br>
        <a href="javascript:window.parent.postMessage({{'remove_colab':'{nome}'}}, '*')">Remover da rota</a>
        """

        folium.Marker(
            location=[lat, lon],
            popup=popup_html,
            icon=folium.Icon(color="blue" if not rota_do_colab else "green")
        ).add_to(cluster)

    st_folium(m, width=1200, height=700)

# -----------------------------
# Captura de eventos JS
# -----------------------------
msg = st.experimental_get_query_params()
# OBS: no Streamlit Cloud, o postMessage pode precisar de workaround com st_folium events.
# Aqui é apenas protótipo da lógica.

# -----------------------------
# Exportar XLSX
# -----------------------------
if st.sidebar.button("📤 Exportar rotas"):
    dados = []
    for rota, membros in st.session_state["rotas"].items():
        for m in membros:
            dados.append({"COLABORADOR": m, "ROTA": rota})
    df_export = pd.DataFrame(dados)
    buffer = io.BytesIO()
    df_export.to_excel(buffer, index=False)
    st.download_button("Baixar XLSX", buffer.getvalue(), file_name="rotas.xlsx")
