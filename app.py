# =========================================================
# IMPORTAÇÃO DAS BIBLIOTECAS
# =========================================================

import streamlit as st
import pandas as pd

from datetime import date

from supabase import create_client, Client

from postgrest import APIError


# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(

    page_title="NN | Controle Financeiro",
    layout="wide"

)


# =========================================================
# SUPABASE SECRETS
# =========================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]

SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


# =========================================================
# CLIENTE PRINCIPAL
# =========================================================

supabase: Client = create_client(

    SUPABASE_URL,
    SUPABASE_KEY

)


# =========================================================
# LISTA DE BANCOS
# =========================================================

BANCOS = [

    "Itaú",
    "Neon",
    "Bradesco"

]


# =========================================================
# SESSION STATE
# =========================================================

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "session" not in st.session_state:
    st.session_state.session = None

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "logado" not in st.session_state:
    st.session_state.logado = False

if "tela" not in st.session_state:
    st.session_state.tela = "dashboard"


# =========================================================
# CLIENTE JWT AUTENTICADO
# =========================================================

def get_authenticated_client():

    access_token = st.session_state.get(
        "access_token"
    )

    if not access_token:
        return None

    client = create_client(

        SUPABASE_URL,
        SUPABASE_KEY

    )

    client.postgrest.auth(
        access_token
    )

    return client


# =========================================================
# LOGIN
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

                st.session_state.usuario = resposta.user

                st.session_state.session = resposta.session

                st.session_state.access_token = (
                    resposta.session.access_token
                )

                st.session_state.logado = True

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

            "Novo e-mail",
            key="novo_email"

        )

        nova_senha = st.text_input(

            "Nova senha",
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
        ).order(
            "data",
            desc=True
        ).execute()

        dados = resposta.data

        if not dados:

            return pd.DataFrame()

        return pd.DataFrame(dados)

    except Exception as e:

        st.error(
            f"Erro carregar transações: {e}"
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
# EXCLUIR TRANSAÇÃO
# =========================================================

def excluir_transacao(
    client,
    id_transacao
):

    try:

        client.table(
            "transacoes"
        ).delete().eq(
            "id",
            id_transacao
        ).execute()

        st.success(
            "Transação excluída!"
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"Erro excluir: {e}"
        )


# =========================================================
# MODAL NOVA TRANSAÇÃO
# =========================================================

@st.dialog("💸 Nova Transação")

def popup_nova_transacao():

    usuario = st.session_state.usuario

    user_id = usuario.id

    supabase_auth = get_authenticated_client()

    st.subheader(
        "Cadastrar Nova Transação"
    )

    tipo = st.selectbox(

        "Tipo",

        [
            "Receita",
            "Despesa",
            "Transferência"
        ]

    )

    data = st.date_input(
        "Data"
    )

    valor = st.number_input(

        "Valor",
        min_value=0.0

    )


    # =====================================================
    # RECEITA E DESPESA
    # =====================================================

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


    # =====================================================
    # TRANSFERÊNCIA
    # =====================================================

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


    # =====================================================
    # BOTÃO SALVAR
    # =====================================================

    if st.button("Salvar"):

        try:

            # =============================================
            # RECEITA
            # =============================================

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


            # =============================================
            # DESPESA
            # =============================================

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


            # =============================================
            # TRANSFERÊNCIA
            # =============================================

            elif tipo == "Transferência":

                # SAÍDA
                supabase_auth.table(
                    "transacoes"
                ).insert({

                    "data": str(data),
                    "categoria": categoria,
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
                    "categoria": categoria,
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


# =========================================================
# MODAL CATEGORIAS
# =========================================================

@st.dialog("🗂️ Categorias")

def popup_categorias():

    usuario = st.session_state.usuario

    user_id = usuario.id

    supabase_auth = get_authenticated_client()

    col1, col2 = st.columns(2)


    # =====================================================
    # RECEITAS
    # =====================================================

    with col1:

        st.subheader("🟢 Receitas")

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


    # =====================================================
    # DESPESAS
    # =====================================================

    with col2:

        st.subheader("🔴 Despesas")

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


# =========================================================
# DASHBOARD
# =========================================================

def dashboard():

    usuario = st.session_state.usuario

    user_id = usuario.id

    supabase_auth = get_authenticated_client()

    if not supabase_auth:

        st.error(
            "Sessão inválida"
        )

        st.stop()


    # =====================================================
    # SIDEBAR MENU
    # =====================================================

    with st.sidebar:

        st.title("⚙️ Menu")

        st.write(
            f"👤 {usuario.email}"
        )

        if st.button("🏠 Dashboard"):

            st.session_state.tela = "dashboard"


        if st.button("💸 Nova Transação"):

            popup_nova_transacao()


        if st.button("🗂️ Categorias"):

            popup_categorias()


        if st.button("⚙️ Configurações"):

            st.info(
                "Configurações futuras."
            )


        if st.button("🚪 Sair"):

            st.session_state.usuario = None

            st.session_state.session = None

            st.session_state.access_token = None

            st.session_state.logado = False

            st.rerun()


    # =====================================================
    # CARREGA DADOS
    # =====================================================

    df = carregar_transacoes(

        supabase_auth,
        user_id

    )


    # =====================================================
    # DASHBOARD PRINCIPAL
    # =====================================================

    st.title(
        "📊 Dashboard Financeiro"
    )


    # =====================================================
    # SALDOS DOS BANCOS
    # =====================================================

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


    # =====================================================
    # SALDO TOTAL
    # =====================================================

    st.divider()

    saldo_total = (

        saldo_itau +
        saldo_neon +
        saldo_bradesco

    )

    st.metric(

        "💰 Saldo Total",
        f"R$ {saldo_total:,.2f}"

    )


    # =====================================================
    # ABAS TRANSAÇÕES
    # =====================================================

    st.divider()

    st.subheader(
        "💳 Transações"
    )

    aba1, aba2, aba3 = st.tabs([

        "🔴 Despesas",
        "🟢 Receitas",
        "🔄 Transferências"

    ])


    # =====================================================
    # ABA DESPESAS
    # =====================================================

    with aba1:

        despesas = df[
            df["tipo"] == "Despesa"
        ] if not df.empty else pd.DataFrame()

        if not despesas.empty:

            for _, row in despesas.iterrows():

                with st.expander(

                    f"{row['categoria']} | "
                    f"R$ {abs(row['valor']):,.2f}"

                ):

                    st.write(
                        f"Banco: {row['banco']}"
                    )

                    st.write(
                        f"Data: {row['data']}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(

                            "🗑️ Excluir",
                            key=f"del_desp_{row['id']}"

                        ):

                            excluir_transacao(

                                supabase_auth,
                                row["id"]

                            )

                    with col2:

                        st.button(

                            "✏️ Editar",
                            key=f"edit_desp_{row['id']}"

                        )


    # =====================================================
    # ABA RECEITAS
    # =====================================================

    with aba2:

        receitas = df[
            df["tipo"] == "Receita"
        ] if not df.empty else pd.DataFrame()

        if not receitas.empty:

            for _, row in receitas.iterrows():

                with st.expander(

                    f"{row['categoria']} | "
                    f"R$ {row['valor']:,.2f}"

                ):

                    st.write(
                        f"Banco: {row['banco']}"
                    )

                    st.write(
                        f"Data: {row['data']}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(

                            "🗑️ Excluir",
                            key=f"del_rec_{row['id']}"

                        ):

                            excluir_transacao(

                                supabase_auth,
                                row["id"]

                            )

                    with col2:

                        st.button(

                            "✏️ Editar",
                            key=f"edit_rec_{row['id']}"

                        )


    # =====================================================
    # ABA TRANSFERÊNCIAS
    # =====================================================

    with aba3:

        transf = df[
            df["tipo"] == "Transferência"
        ] if not df.empty else pd.DataFrame()

        if not transf.empty:

            for _, row in transf.iterrows():

                with st.expander(

                    f"{row['banco']} → "
                    f"{row.get('banco_destino', '')}"

                ):

                    st.write(
                        f"Valor: R$ {abs(row['valor']):,.2f}"
                    )

                    st.write(
                        f"Data: {row['data']}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(

                            "🗑️ Excluir",
                            key=f"del_transf_{row['id']}"

                        ):

                            excluir_transacao(

                                supabase_auth,
                                row["id"]

                            )

                    with col2:

                        st.button(

                            "✏️ Editar",
                            key=f"edit_transf_{row['id']}"

                        )


    # =====================================================
    # HISTÓRICO COMPLETO
    # =====================================================

    st.divider()

    st.subheader(
        "📜 Histórico Completo"
    )

    if not df.empty:

        df_exibir = df.drop(

            columns=["user_id"],
            errors="ignore"

        )

        st.dataframe(

            df_exibir,
            use_container_width=True

        )

    else:

        st.info(
            "Nenhuma transação encontrada."
        )


# =========================================================
# CONTROLE PRINCIPAL
# =========================================================

if not st.session_state.logado:

    login()

else:

    dashboard()
