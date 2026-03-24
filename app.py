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

map_state = None
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

        folium.Marker(
            location=[lat, lon],
            popup=f"{nome} - Rota: {rota_do_colab if rota_do_colab else 'Nenhuma'}",
            icon=folium.Icon(color="green" if rota_do_colab else "blue")
        ).add_to(cluster)

    map_state = st_folium(m, width=1200, height=700)

# -----------------------------
# Captura de clique no mapa
# -----------------------------
if map_state and map_state.get("last_clicked"):
    lat = map_state["last_clicked"]["lat"]
    lon = map_state["last_clicked"]["lng"]

    # Encontrar colaborador mais próximo do clique
    for _, row in st.session_state["colaboradores"].iterrows():
        if abs(row["LAT"] - lat) < 0.0005 and abs(row["LONG"] - lon) < 0.0005:
            nome = row["COLABORADORES"]
            rota_atual = st.session_state["rota_atual"]
            if rota_atual:
                if nome not in st.session_state["rotas"][rota_atual]:
                    st.session_state["rotas"][rota_atual].append(nome)
                    st.success(f"Colaborador {nome} adicionado à rota {rota_atual}")
                else:
                    st.session_state["rotas"][rota_atual].remove(nome)
                    st.warning(f"Colaborador {nome} removido da rota {rota_atual}")

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
