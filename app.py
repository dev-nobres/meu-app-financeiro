# =========================================================
# IMPORTAÇÃO DAS BIBLIOTECAS
# =========================================================

# Streamlit -> Interface visual
import streamlit as st

# Pandas -> Manipulação de tabelas
import pandas as pd

# Date -> Trabalhar com datas
from datetime import date

# Supabase -> Banco de dados
from supabase import create_client, Client

# APIError -> Captura erros do Supabase/Postgres
from postgrest import APIError


# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(

    page_title="NN | Controle Financeiro",
    layout="wide"

)


# =========================================================
# LEITURA DAS SECRETS
# =========================================================

# Dados vindos do:
#
# .streamlit/secrets.toml
#
# ou
#
# Streamlit Cloud > Settings > Secrets

SUPABASE_URL = st.secrets["SUPABASE_URL"]

SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


# =========================================================
# CLIENTE PRINCIPAL SUPABASE
# =========================================================

# Cliente principal usado para:
#
# - Login
# - Cadastro
# - Auth
#
# NÃO usamos ele para inserts protegidos por RLS.

supabase: Client = create_client(

    SUPABASE_URL,
    SUPABASE_KEY

)


# =========================================================
# LISTA DE BANCOS
# =========================================================

# Aqui ficam os bancos disponíveis.
#
# Futuramente você pode transformar
# isso em tabela no Supabase.

BANCOS = [

    "Itaú",
    "Neon",
    "Bradesco"

]


# =========================================================
# SESSION STATE
# =========================================================

# Session State funciona como memória
# temporária do Streamlit.

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "session" not in st.session_state:
    st.session_state.session = None

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "logado" not in st.session_state:
    st.session_state.logado = False


# =========================================================
# CLIENTE JWT AUTENTICADO
# =========================================================

# Essa função é o coração do RLS.
#
# Ela cria um cliente autenticado
# usando o JWT do usuário.

def get_authenticated_client():

    access_token = st.session_state.get(
        "access_token"
    )

    # Se não houver token
    if not access_token:

        return None

    # Cria cliente
    client = create_client(

        SUPABASE_URL,
        SUPABASE_KEY

    )

    # Injeta JWT
    #
    # Isso faz o Supabase reconhecer:
    #
    # auth.uid()

    client.postgrest.auth(
        access_token
    )

    return client


# =========================================================
# FUNÇÃO LOGIN
# =========================================================

def login():

    st.title("🏦 NN | Controle Financeiro")

    aba1, aba2 = st.tabs([
        "Entrar",
        "Criar Conta"
    ])


    # =====================================================
    # LOGIN
    # =====================================================

    with aba1:

        email = st.text_input(
            "E-mail"
        )

        senha = st.text_input(

            "Senha",
            type="password"

        )

        if st.button("Entrar"):

            try:

                resposta = supabase.auth.sign_in_with_password({

                    "email": email,
                    "password": senha

                })

                # Salva usuário
                st.session_state.usuario = resposta.user

                # Salva sessão
                st.session_state.session = resposta.session

                # JWT ACCESS TOKEN
                st.session_state.access_token = (
                    resposta.session.access_token
                )

                st.session_state.logado = True

                st.success(
                    "Login realizado!"
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Erro login: {e}"
                )


    # =====================================================
    # CADASTRO
    # =====================================================

    with aba2:

        novo_email = st.text_input(

            "Novo E-mail",
            key="novo_email"

        )

        nova_senha = st.text_input(

            "Nova Senha",
            type="password",
            key="nova_senha"

        )

        if st.button("Criar Conta"):

            try:

                supabase.auth.sign_up({

                    "email": novo_email,
                    "password": nova_senha

                })

                st.success(
                    "Conta criada!"
                )

            except Exception as e:

                st.error(
                    f"Erro cadastro: {e}"
                )


# =========================================================
# CARREGAR TRANSAÇÕES
# =========================================================

def carregar_transacoes(
    client,
    user_id
):

    try:

        resposta = client.table(
            "transacoes"
        ).select("*").eq(
            "user_id",
            user_id
        ).execute()

        dados = resposta.data

        if not dados:

            return pd.DataFrame()

        df = pd.DataFrame(dados)

        return df

    except Exception as e:

        st.error(
            f"Erro transações: {e}"
        )

        return pd.DataFrame()


# =========================================================
# CARREGAR CATEGORIAS
# =========================================================

def carregar_categorias(
    client,
    tabela,
    user_id
):

    try:

        resposta = client.table(
            tabela
        ).select("*").eq(
            "user_id",
            user_id
        ).execute()

        return resposta.data

    except Exception as e:

        st.error(
            f"Erro categorias: {e}"
        )

        return []


# =========================================================
# DASHBOARD PRINCIPAL
# =========================================================

def dashboard():

    usuario = st.session_state.usuario

    user_id = usuario.id

    # Cliente JWT autenticado
    supabase_auth = get_authenticated_client()

    if not supabase_auth:

        st.error(
            "Sessão inválida."
        )

        st.stop()


    # =====================================================
    # MENU LATERAL
    # =====================================================

    with st.sidebar:

        st.title("⚙️ Menu")

        st.write(
            f"👤 {usuario.email}"
        )

        menu = st.radio(

            "Navegação",

            [
                "Dashboard",
                "Categorias",
                "Configurações"
            ]

        )

        # Logout
        if st.button("🚪 Sair"):

            st.session_state.usuario = None

            st.session_state.session = None

            st.session_state.access_token = None

            st.session_state.logado = False

            st.rerun()


    # =====================================================
    # TELA DASHBOARD
    # =====================================================

    if menu == "Dashboard":

        st.title(
            "📊 Dashboard Financeiro"
        )

        # ================================================
        # CARREGA TRANSAÇÕES
        # ================================================

        df = carregar_transacoes(
            supabase_auth,
            user_id
        )


        # ================================================
        # SALDOS BANCÁRIOS
        # ================================================

        st.subheader(
            "💰 Saldos Bancários"
        )

        if not df.empty:

            saldo_itau = df[
                df["banco"] == "Itaú"
            ]["valor"].sum()

            saldo_neon = df[
                df["banco"] == "Neon"
            ]["valor"].sum()

            saldo_bradesco = df[
                df["banco"] == "Bradesco"
            ]["valor"].sum()

        else:

            saldo_itau = 0
            saldo_neon = 0
            saldo_bradesco = 0


        # ================================================
        # CARDS DOS BANCOS
        # ================================================

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(

                "🏦 Itaú",
                f"R$ {saldo_itau:,.2f}"

            )

        with col2:

            st.metric(

                "🏦 Neon",
                f"R$ {saldo_neon:,.2f}"

            )

        with col3:

            st.metric(

                "🏦 Bradesco",
                f"R$ {saldo_bradesco:,.2f}"

            )


        # ================================================
        # SALDO TOTAL
        # ================================================

        st.divider()

        saldo_total = (

            saldo_itau +
            saldo_neon +
            saldo_bradesco

        )

        st.metric(

            "💵 Saldo Total",
            f"R$ {saldo_total:,.2f}"

        )


        # ================================================
        # NOVA TRANSAÇÃO
        # ================================================

        st.divider()

        st.subheader(
            "➕ Novo Lançamento"
        )

        tipo = st.selectbox(

            "Tipo Transação",

            [
                "Receita",
                "Despesa",
                "Transferência"
            ]

        )


        # ================================================
        # CAMPOS PADRÃO
        # ================================================

        data = st.date_input(
            "Data"
        )

        valor = st.number_input(

            "Valor",
            min_value=0.0

        )


        # ================================================
        # RECEITA E DESPESA
        # ================================================

        if tipo != "Transferência":

            tabela = (
                "categorias_receita"
                if tipo == "Receita"
                else "categorias_despesa"
            )

            categorias = carregar_categorias(

                supabase_auth,
                tabela,
                user_id

            )

            opcoes = [
                c["nome"]
                for c in categorias
            ]

            categoria = st.selectbox(

                "Categoria",

                opcoes if opcoes else [
                    "Sem categoria"
                ]

            )

            banco = st.selectbox(

                "Banco",

                BANCOS

            )


        # ================================================
        # TRANSFERÊNCIA
        # ================================================

        else:

            categoria = "Transferência"

            banco = st.selectbox(

                "Banco Origem",

                BANCOS

            )

            banco_destino = st.selectbox(

                "Banco Destino",

                BANCOS

            )


        status = st.selectbox(

            "Status",

            [
                "Pago",
                "Pendente"
            ]

        )


        # ================================================
        # BOTÃO SALVAR
        # ================================================

        if st.button("Salvar Transação"):

            try:

                # ========================================
                # RECEITA
                # ========================================

                if tipo == "Receita":

                    supabase_auth.table(
                        "transacoes"
                    ).insert({

                        "data": str(data),
                        "categoria": categoria,
                        "valor": valor,
                        "tipo": tipo,
                        "status": status,
                        "banco": banco,
                        "user_id": user_id

                    }).execute()


                # ========================================
                # DESPESA
                # ========================================

                elif tipo == "Despesa":

                    supabase_auth.table(
                        "transacoes"
                    ).insert({

                        "data": str(data),
                        "categoria": categoria,
                        "valor": -valor,
                        "tipo": tipo,
                        "status": status,
                        "banco": banco,
                        "user_id": user_id

                    }).execute()


                # ========================================
                # TRANSFERÊNCIA
                # ========================================

                elif tipo == "Transferência":

                    # SAÍDA
                    supabase_auth.table(
                        "transacoes"
                    ).insert({

                        "data": str(data),
                        "categoria": "Transferência",
                        "valor": -valor,
                        "tipo": tipo,
                        "status": status,
                        "banco": banco,
                        "banco_destino": banco_destino,
                        "user_id": user_id

                    }).execute()


                    # ENTRADA
                    supabase_auth.table(
                        "transacoes"
                    ).insert({

                        "data": str(data),
                        "categoria": "Transferência",
                        "valor": valor,
                        "tipo": tipo,
                        "status": status,
                        "banco": banco_destino,
                        "banco_destino": banco,
                        "user_id": user_id

                    }).execute()


                st.success(
                    "Transação salva!"
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Erro salvar: {e}"
                )


        # ================================================
        # LISTAGEM TRANSAÇÕES
        # ================================================

        st.divider()

        st.subheader(
            "📋 Transações"
        )

        if not df.empty:

            # Remove user_id da visualização
            df_exibir = df.drop(

                columns=["user_id"],
                errors="ignore"

            )

            st.dataframe(

                df_exibir,
                use_container_width=True

            )


            # ============================================
            # EXCLUIR TRANSAÇÃO
            # ============================================

            st.divider()

            st.subheader(
                "🗑️ Excluir Transação"
            )

            ids = df["id"].tolist()

            id_excluir = st.selectbox(

                "Selecione ID",

                ids

            )

            if st.button(
                "Excluir Transação"
            ):

                supabase_auth.table(
                    "transacoes"
                ).delete().eq(

                    "id",
                    id_excluir

                ).execute()

                st.success(
                    "Transação excluída!"
                )

                st.rerun()


    # =====================================================
    # MENU CATEGORIAS
    # =====================================================

    elif menu == "Categorias":

        st.title(
            "🗂️ Categorias"
        )

        col1, col2 = st.columns(2)


        # =================================================
        # RECEITAS
        # =================================================

        with col1:

            st.subheader(
                "🟢 Receitas"
            )

            receitas = carregar_categorias(

                supabase_auth,
                "categorias_receita",
                user_id

            )

            for item in receitas:

                c1, c2 = st.columns([4, 1])

                with c1:

                    st.write(
                        item["nome"]
                    )

                with c2:

                    if st.button(

                        "❌",
                        key=f"del_rec_{item['id']}"

                    ):

                        supabase_auth.table(
                            "categorias_receita"
                        ).delete().eq(

                            "id",
                            item["id"]

                        ).execute()

                        st.rerun()


            nova_receita = st.text_input(
                "Nova Receita"
            )

            if st.button(
                "Adicionar Receita"
            ):

                supabase_auth.table(
                    "categorias_receita"
                ).insert({

                    "nome": nova_receita,
                    "user_id": user_id

                }).execute()

                st.rerun()


        # =================================================
        # DESPESAS
        # =================================================

        with col2:

            st.subheader(
                "🔴 Despesas"
            )

            despesas = carregar_categorias(

                supabase_auth,
                "categorias_despesa",
                user_id

            )

            for item in despesas:

                c1, c2 = st.columns([4, 1])

                with c1:

                    st.write(
                        item["nome"]
                    )

                with c2:

                    if st.button(

                        "❌",
                        key=f"del_desp_{item['id']}"

                    ):

                        supabase_auth.table(
                            "categorias_despesa"
                        ).delete().eq(

                            "id",
                            item["id"]

                        ).execute()

                        st.rerun()


            nova_despesa = st.text_input(
                "Nova Despesa"
            )

            if st.button(
                "Adicionar Despesa"
            ):

                supabase_auth.table(
                    "categorias_despesa"
                ).insert({

                    "nome": nova_despesa,
                    "user_id": user_id

                }).execute()

                st.rerun()


    # =====================================================
    # MENU CONFIGURAÇÕES
    # =====================================================

    elif menu == "Configurações":

        st.title(
            "⚙️ Configurações"
        )

        st.info(
            "Área reservada para futuras configurações."
        )


# =========================================================
# CONTROLE PRINCIPAL
# =========================================================

if not st.session_state.logado:

    login()

else:

    dashboard()
