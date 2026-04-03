import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="Consulta CNPJ", layout="centered")

st.title("🔎 Consulta de CNPJs em Massa")

# Upload da planilha
uploaded_file = st.file_uploader("📂 Envie sua planilha Excel", type=["xlsx"])

# Função de consulta
def consultar_cnpj(cnpj):
    tentativas = 3

    for tentativa in range(tentativas):
        try:
            url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
            r = requests.get(url, timeout=10)

            if r.status_code == 200:
                data = r.json()
                status = data.get("descricao_situacao_cadastral")

                if not status:
                    return "ERRO"

                status_validos = ["ATIVA", "INAPTA", "BAIXADA", "SUSPENSA"]

                if status.upper() not in status_validos:
                    return "SUSPEITO"

                return status

            elif r.status_code == 404:
                return "INVALIDO"

        except:
            pass

        time.sleep(2 + tentativa)

    return "ERRO"


# Quando arquivo for enviado
if uploaded_file:

    df = pd.read_excel(uploaded_file)

    # Limpar CNPJ
    df["CNPJ"] = df["CNPJ"].astype(str)
    df["CNPJ"] = df["CNPJ"].str.replace(r"\D", "", regex=True)
    df["CNPJ"] = df["CNPJ"].str.zfill(14)

    # Botão para iniciar
    if st.button("🚀 Iniciar Consulta"):

        resultado = []
        cache = {}

        cnpjs_unicos = df["CNPJ"].unique()
        total = len(cnpjs_unicos)

        progress_bar = st.progress(0)
        status_text = st.empty()

        contador = 0

        for _, row in df.iterrows():
            cnpj = row["CNPJ"]
            remessa = row["REMESSA"]

            # Consulta única por CNPJ
            if cnpj not in cache:

                if len(cnpj) != 14:
                    cache[cnpj] = "INVALIDO"
                else:
                    cache[cnpj] = consultar_cnpj(cnpj)

                contador += 1
                progresso = contador / total

                progress_bar.progress(progresso)
                status_text.text(f"Consultando {contador} de {total} CNPJs...")

            status = cache[cnpj]

            resultado.append({
                "CNPJ": cnpj,
                "REMESSA": remessa,
                "STATUS": status
            })

        # Criar DataFrame
        df_resultado = pd.DataFrame(resultado)

        # Normalizar
        df_resultado["STATUS"] = df_resultado["STATUS"].str.upper()

        # Regra final
        df_resultado["STATUS_FINAL"] = df_resultado["STATUS"].apply(
            lambda x: "ATIVA" if x == "ATIVA"
            else "INAPTO" if x in ["INAPTA", "BAIXADA", "SUSPENSA"]
            else "VERIFICAR"
        )

        # Separar resultados
        aptos = df_resultado[df_resultado["STATUS_FINAL"] == "ATIVA"]
        inaptos = df_resultado[df_resultado["STATUS_FINAL"] == "INAPTO"]
        verificar = df_resultado[df_resultado["STATUS_FINAL"] == "VERIFICAR"]

        st.success("✅ Consulta finalizada!")

        # Exibir resultados
        st.subheader("🟢 CNPJs Aptos")
        st.dataframe(aptos[["CNPJ", "REMESSA"]])

        st.subheader("🔴 CNPJs Inaptos")
        st.dataframe(inaptos[["CNPJ", "REMESSA"]])

        st.subheader("⚠️ Necessário Verificar")
        st.dataframe(verificar[["CNPJ", "REMESSA"]])