# =========================================================
# IMPORTAÇÃO DAS BIBLIOTECAS
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from datetime import date

from supabase import create_client, Client


# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(

    page_title="NN | Controle Financeiro",
    layout="wide"

)


# =========================================================
# CONEXÃO SUPABASE
# =========================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]

SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


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
# CLIENTE AUTENTICADO COM JWT
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

def tela_login():

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
            "Novo E-mail"
        )

        nova_senha = st.text_input(

            "Nova Senha",
            type="password"

        )

        if st.button("Criar Conta"):

            try:

                supabase.auth.sign_up({

                    "email": novo_email,
                    "password": nova_senha

                })

                st.success(
                    "Conta criada com sucesso!"
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

        df = pd.DataFrame(dados)

        # =================================================
        # GARANTE COLUNAS
        # =================================================

        colunas_necessarias = [

            "id",
            "data",
            "categoria",
            "valor",
            "tipo",
            "status",
            "banco",
            "banco_destino",
            "user_id"

        ]

        for coluna in colunas_necessarias:

            if coluna not in df.columns:
                df[coluna] = None

        # =================================================
        # CONVERSÕES
        # =================================================

        df["data"] = pd.to_datetime(
            df["data"]
        )

        df["mes_ano"] = df["data"].dt.strftime(
            "%m/%Y"
        )

        return df

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
# EXCLUIR CATEGORIA
# =========================================================

def excluir_categoria(
    client,
    tabela,
    id_categoria
):

    try:

        client.table(
            tabela
        ).delete().eq(
            "id",
            id_categoria
        ).execute()

        st.success(
            "Categoria excluída!"
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"Erro excluir categoria: {e}"
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
    # RECEITA / DESPESA
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
    # SALVAR
    # =====================================================

    if st.button("Salvar"):

        try:

            # =================================================
            # RECEITA
            # =================================================

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

            # =================================================
            # DESPESA
            # =================================================

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

            # =================================================
            # TRANSFERÊNCIA
            # =================================================

            else:

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
                    key=f"rec_{item['id']}"

                ):

                    excluir_categoria(

                        supabase_auth,
                        "categorias_receita",
                        item["id"]

                    )

        nova = st.text_input(
            "Nova Receita"
        )

        if st.button("➕ Receita"):

            supabase_auth.table(
                "categorias_receita"
            ).insert({

                "nome": nova,
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
                    key=f"desp_{item['id']}"

                ):

                    excluir_categoria(

                        supabase_auth,
                        "categorias_despesa",
                        item["id"]

                    )

        nova_d = st.text_input(
            "Nova Despesa"
        )

        if st.button("➕ Despesa"):

            supabase_auth.table(
                "categorias_despesa"
            ).insert({

                "nome": nova_d,
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

        if st.button("💸 Nova Transação"):

            popup_nova_transacao()

        if st.button("🗂️ Categorias"):

            popup_categorias()

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
    # FILTRO MÊS
    # =====================================================

    st.title(
        "📊 Dashboard Financeiro"
    )

    meses = sorted(

        df["mes_ano"].unique(),

        reverse=True

    ) if not df.empty else []

    mes_selecionado = st.selectbox(

        "📅 Filtrar por mês",

        meses if meses else ["Sem dados"]

    )

    if not df.empty:

        df = df[
            df["mes_ano"] == mes_selecionado
        ]

    # =====================================================
    # BOTÃO NOVA TRANSAÇÃO
    # =====================================================

    if st.button(
        "➕ Nova Transação"
    ):

        popup_nova_transacao()

    # =====================================================
    # SALDOS
    # =====================================================

    saldo_itau = 0
    saldo_neon = 0
    saldo_bradesco = 0

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
    # GRÁFICO DESPESAS
    # =====================================================

    st.divider()

    st.subheader(
        "📉 Despesas por Categoria"
    )

    if (

        not df.empty
        and "tipo" in df.columns
        and "categoria" in df.columns

    ):

        df_despesas = df[
            df["tipo"] == "Despesa"
        ]

        if not df_despesas.empty:

            grafico_despesas = (

                df_despesas
                .groupby("categoria")["valor"]
                .sum()
                .reset_index()

            )

            grafico_despesas["valor"] = (
                grafico_despesas["valor"].abs()
            )

            fig = px.pie(

                grafico_despesas,

                names="categoria",
                values="valor",

                title="Distribuição de Despesas"

            )

            st.plotly_chart(

                fig,
                use_container_width=True

            )

        else:

            st.info(
                "Sem despesas cadastradas."
            )

    else:

        st.info(
            "Sem dados suficientes."
        )

    # =====================================================
    # RECEITAS VS DESPESAS
    # =====================================================

    st.divider()

    st.subheader(
        "📊 Receitas vs Despesas"
    )

    if not df.empty and "tipo" in df.columns:

        receitas_total = df[
            df["tipo"] == "Receita"
        ]["valor"].sum()

        despesas_total = abs(

            df[
                df["tipo"] == "Despesa"
            ]["valor"].sum()

        )

        grafico_resumo = pd.DataFrame({

            "Tipo": [

                "Receitas",
                "Despesas"

            ],

            "Valor": [

                receitas_total,
                despesas_total

            ]

        })

        fig2 = px.bar(

            grafico_resumo,

            x="Tipo",
            y="Valor",

            title="Comparativo Financeiro"

        )

        st.plotly_chart(

            fig2,
            use_container_width=True

        )

    else:

        st.info(
            "Sem dados financeiros."
        )

    # =====================================================
    # EVOLUÇÃO FINANCEIRA
    # =====================================================

    st.divider()

    st.subheader(
        "📈 Evolução Financeira"
    )

    if (

        not df.empty
        and "data" in df.columns
        and "valor" in df.columns

    ):

        evolucao = (

            df.groupby("data")["valor"]
            .sum()
            .reset_index()

        )

        fig3 = px.line(

            evolucao,

            x="data",
            y="valor",

            markers=True,

            title="Saldo Diário"

        )

        st.plotly_chart(

            fig3,
            use_container_width=True

        )

    else:

        st.info(
            "Sem dados para evolução."
        )

    # =====================================================
    # TRANSAÇÕES
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
    # DESPESAS
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

                    if st.button(

                        "🗑️ Excluir",
                        key=f"desp_{row['id']}"

                    ):

                        excluir_transacao(

                            supabase_auth,
                            row["id"]

                        )

    # =====================================================
    # RECEITAS
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

                    if st.button(

                        "🗑️ Excluir",
                        key=f"rec_{row['id']}"

                    ):

                        excluir_transacao(

                            supabase_auth,
                            row["id"]

                        )

    # =====================================================
    # TRANSFERÊNCIAS
    # =====================================================

    with aba3:

        transf = df[
            df["tipo"] == "Transferência"
        ] if not df.empty else pd.DataFrame()

        if not transf.empty:

            for _, row in transf.iterrows():

                with st.expander(

                    f"{row['banco']} → "
                    f"{row['banco_destino']}"

                ):

                    st.write(
                        f"Valor: R$ {abs(row['valor']):,.2f}"
                    )

                    st.write(
                        f"Data: {row['data']}"
                    )

                    if st.button(

                        "🗑️ Excluir",
                        key=f"transf_{row['id']}"

                    ):

                        excluir_transacao(

                            supabase_auth,
                            row["id"]

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

            columns=[
                "user_id",
                "mes_ano"
            ],

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

    tela_login()

else:

    dashboard()