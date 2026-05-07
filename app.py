import streamlit as st
import pandas as pd
import requests
import time
import base64

def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img = get_base64("fundo.PNG")

st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)),
                    url("data:image/png;base64,{img}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<style>

.block-container {
    background: rgba(0, 0, 0, 0.45);
    backdrop-filter: blur(10px);

    padding: 2rem;
    border-radius: 20px;

    /* CENTRALIZA */
    max-width: 700px;
    margin: auto;

    /* SOMBRA */
    box-shadow: 0 10px 35px rgba(0,0,0,0.35);
}

</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>

/* FUNDO DA BARRA */
div.stProgress > div > div {
    background-color: rgba(255,255,255,0.15);
    border-radius: 10px;
}

/* BARRA DE PROGRESSO */
div.stProgress > div > div > div {
    background: linear-gradient(90deg, #2962ff → #448aff);
    border-radius: 10px;
    height: 12px;
}

/* ANIMAÇÃO */
div.stProgress > div > div > div {
    transition: width 0.4s ease-in-out;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* DIMINUI A ÁREA DE UPLOAD */
[data-testid="stFileUploader"] {
    max-width: 450px;
    margin: auto;
}

/* DEIXA A CAIXA MAIS CLEAN */
[data-testid="stFileUploader"] section {
    padding: 1rem;
    border-radius: 12px;
    background: rgba(255,255,255,0.06);
    
    /* SOMBRA */
    box-shadow: 0 0 15px rgba(0,0,0,0.25);
}

/* CENTRALIZA TEXTO */
[data-testid="stFileUploader"] label {
    text-align: center;
    width: 100%;
}

</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Consulta CNPJ", layout="centered")

st.title("🔎 Consulta de clientes inaptos")

st.divider()

# Upload da planilha
uploaded_file = st.file_uploader("📂 Envie sua planilha Excel", type=["xlsx"])

st.divider()

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
        inicio = time.time()

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

                porcentagem = int(progresso * 100)

                tempo_decorrido = time.time() - inicio
                tempo_medio = tempo_decorrido / contador
                tempo_restante = int((total - contador) * tempo_medio)

                progress_bar.progress(progresso)
                status_text.text(f"🔎 {porcentagem}% concluído | ⏳ ~{tempo_restante}s restantes")

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
        st.divider()

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
