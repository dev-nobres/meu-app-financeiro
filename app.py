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

if "nome_painel" not in st.session_state:
    st.session_state.nome_painel = "Meu Controle Financeiro"


# =========================================================
# CLIENTE AUTENTICADO JWT
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

        df = pd.DataFrame(dados)

        colunas = [

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

        for coluna in colunas:

            if coluna not in df.columns:
                df[coluna] = None

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

        st.toast(
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

        st.toast(
            "Categoria excluída!"
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"Erro excluir categoria: {e}"
        )


# =========================================================
# MODAL EDITAR TRANSAÇÃO
# =========================================================

@st.dialog("✏️ Editar Transação")

def popup_editar_transacao(transacao):

    supabase_auth = get_authenticated_client()

    st.subheader(
        "Editar lançamento"
    )

    nova_categoria = st.text_input(

        "Categoria",

        value=transacao["categoria"]

    )

    novo_valor = st.number_input(

        "Valor",

        value=float(abs(transacao["valor"]))

    )

    novo_status = st.selectbox(

        "Status",

        ["Pago", "Pendente"],

        index=0 if transacao["status"] == "Pago" else 1

    )

    novo_banco = st.selectbox(

        "Banco",

        BANCOS,

        index=BANCOS.index(
            transacao["banco"]
        ) if transacao["banco"] in BANCOS else 0

    )

    if st.button("💾 Salvar Alterações"):

        valor_final = novo_valor

        if transacao["tipo"] == "Despesa":
            valor_final = -novo_valor

        supabase_auth.table(
            "transacoes"
        ).update({

            "categoria": nova_categoria,
            "valor": valor_final,
            "status": novo_status,
            "banco": novo_banco

        }).eq(

            "id",
            transacao["id"]

        ).execute()

        st.success(
            "Transação atualizada!"
        )

        st.rerun()


# =========================================================
# MODAL NOVA CATEGORIA
# =========================================================

@st.dialog("➕ Nova Categoria")

def popup_nova_categoria():

    usuario = st.session_state.usuario

    user_id = usuario.id

    supabase_auth = get_authenticated_client()

    tipo = st.selectbox(

        "Tipo da categoria",

        [
            "Receita",
            "Despesa"
        ]

    )

    nome = st.text_input(
        "Nome da categoria"
    )

    if st.button(

        "💾 Salvar Categoria",

        use_container_width=True

    ):

        tabela = (

            "categorias_receita"
            if tipo == "Receita"
            else "categorias_despesa"

        )

        supabase_auth.table(
            tabela
        ).insert({

            "nome": nome,
            "user_id": user_id

        }).execute()

        st.success(
            "Categoria criada!"
        )

        st.rerun()


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
                st.write(item["nome"])

            with c2:

                if st.button(

                    "🗑️",

                    key=f"del_rec_{item['id']}"

                ):

                    excluir_categoria(

                        supabase_auth,
                        "categorias_receita",
                        item["id"]

                    )

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
                st.write(item["nome"])

            with c2:

                if st.button(

                    "🗑️",

                    key=f"del_desp_{item['id']}"

                ):

                    excluir_categoria(

                        supabase_auth,
                        "categorias_despesa",
                        item["id"]

                    )

    st.divider()

    if st.button(

        "➕ Nova Categoria",

        use_container_width=True

    ):

        popup_nova_categoria()


# =========================================================
# MODAL NOVA TRANSAÇÃO
# =========================================================

@st.dialog("💸 Nova Transação")

def popup_nova_transacao():

    usuario = st.session_state.usuario

    user_id = usuario.id

    supabase_auth = get_authenticated_client()

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

        banco_destino = None

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

    if st.button("Salvar"):

        valor_final = valor

        if tipo == "Despesa":
            valor_final = -valor

        supabase_auth.table(
            "transacoes"
        ).insert({

            "data": str(data),
            "categoria": categoria,
            "valor": valor_final,
            "tipo": tipo,
            "status": status,
            "banco": banco,
            "banco_destino": banco_destino,
            "user_id": user_id

        }).execute()

        st.success(
            "Transação salva!"
        )

        st.rerun()


# =========================================================
# DASHBOARD
# =========================================================

def dashboard():

    usuario = st.session_state.usuario

    user_id = usuario.id

    supabase_auth = get_authenticated_client()

    # =====================================================
    # MENU LATERAL
    # =====================================================

    with st.sidebar:

        st.title("⚙️ Menu")

        st.write(
            f"👤 {usuario.email}"
        )

        if st.button("🗂️ Categorias"):

            popup_categorias()

        st.divider()

        nome_painel = st.text_input(

            "Nome do Painel",

            value=st.session_state.get(
                "nome_painel",
                "Meu Controle Financeiro"
            )

        )

        st.session_state.nome_painel = nome_painel

        st.divider()

        if st.button("🚪 Sair"):

            st.session_state.usuario = None

            st.session_state.session = None

            st.session_state.access_token = None

            st.session_state.logado = False

            st.rerun()

    # =====================================================
    # CARREGA DADOS
    # =====================================================

    df_total = carregar_transacoes(

        supabase_auth,
        user_id

    )

    meses = [

        "01/2026",
        "02/2026",
        "03/2026",
        "04/2026",
        "05/2026",
        "06/2026",
        "07/2026",
        "08/2026",
        "09/2026",
        "10/2026",
        "11/2026",
        "12/2026"

    ]

    mes_selecionado = st.selectbox(

        "📅 Filtrar por mês",

        meses,

        index=4

    )

    if not df_total.empty:

        df = df_total[
            df_total["mes_ano"] == mes_selecionado
        ]

    else:

        df = pd.DataFrame()

    # =====================================================
    # TÍTULO
    # =====================================================

    titulo_dashboard = st.session_state.get(

        "nome_painel",

        "Meu Controle Financeiro"

    )

    st.title(
        f"📊 {titulo_dashboard}"
    )

    # =====================================================
    # NOVA TRANSAÇÃO
    # =====================================================

    if st.button(

        "➕ Nova Transação",

        use_container_width=True

    ):

        popup_nova_transacao()

    # =====================================================
    # SALDOS
    # =====================================================

    saldo_itau = 0
    saldo_neon = 0
    saldo_bradesco = 0

    saldo_mes = 0
    saldo_anterior = 0

    if not df.empty:

        saldo_mes = df["valor"].sum()

        df_anterior = df_total[
            df_total["mes_ano"] != mes_selecionado
        ]

        saldo_anterior = df_anterior["valor"].sum()

        saldo_itau = df_total[
            df_total["banco"] == "Itaú"
        ]["valor"].sum()

        saldo_neon = df_total[
            df_total["banco"] == "Neon"
        ]["valor"].sum()

        saldo_bradesco = df_total[
            df_total["banco"] == "Bradesco"
        ]["valor"].sum()

    saldo_total = saldo_anterior + saldo_mes

    # =====================================================
    # PENDÊNCIAS
    # =====================================================

    pendente_itau = 0

    if not df.empty:

        pendente_itau = abs(

            df[
                (df["banco"] == "Itaú") &
                (df["status"] == "Pendente") &
                (df["tipo"] == "Despesa")
            ]["valor"].sum()

        )

    # =====================================================
    # CARDS
    # =====================================================

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        st.metric(

            "💰 Saldo Total",

            f"R$ {saldo_total:,.2f}"

        )

    with col2:

        st.metric(

            "📅 Saldo do Mês",

            f"R$ {saldo_mes:,.2f}"

        )

    with col3:

        st.metric(

            "🏦 Itaú",

            f"R$ {saldo_itau:,.2f}"

        )

        st.caption(
            f"Pendente: R$ {pendente_itau:,.2f}"
        )

    with col4:

        st.metric(

            "🏦 Neon",

            f"R$ {saldo_neon:,.2f}"

        )

    with col5:

        st.metric(

            "🏦 Bradesco",

            f"R$ {saldo_bradesco:,.2f}"

        )

    # =====================================================
    # GRÁFICOS
    # =====================================================

    st.divider()

    if not df.empty:

        despesas = df[
            df["tipo"] == "Despesa"
        ]

        if not despesas.empty:

            grafico = despesas.groupby(
                "categoria"
            )["valor"].sum().reset_index()

            grafico["valor"] = grafico["valor"].abs()

            fig = px.pie(

                grafico,

                names="categoria",
                values="valor",

                title="📉 Despesas por Categoria"

            )

            st.plotly_chart(

                fig,
                use_container_width=True

            )

    # =====================================================
    # ABAS
    # =====================================================

    st.divider()

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

                c1, c2, c3, c4, c5 = st.columns(
                    [2, 2, 2, 1, 1]
                )

                with c1:
                    st.write(row["categoria"])

                with c2:
                    st.write(
                        f"R$ {abs(row['valor']):,.2f}"
                    )

                with c3:
                    st.write(row["banco"])

                with c4:

                    if st.button(
                        "✏️",
                        key=f"edit_desp_{row['id']}"
                    ):

                        popup_editar_transacao(row)

                with c5:

                    if st.button(
                        "🗑️",
                        key=f"del_desp_{row['id']}"
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

                c1, c2, c3, c4, c5 = st.columns(
                    [2, 2, 2, 1, 1]
                )

                with c1:
                    st.write(row["categoria"])

                with c2:
                    st.write(
                        f"R$ {row['valor']:,.2f}"
                    )

                with c3:
                    st.write(row["banco"])

                with c4:

                    if st.button(
                        "✏️",
                        key=f"edit_rec_{row['id']}"
                    ):

                        popup_editar_transacao(row)

                with c5:

                    if st.button(
                        "🗑️",
                        key=f"del_rec_{row['id']}"
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

                c1, c2, c3, c4, c5 = st.columns(
                    [2, 2, 2, 1, 1]
                )

                with c1:
                    st.write(row["banco"])

                with c2:
                    st.write(
                        row["banco_destino"]
                        if row["banco_destino"]
                        else "-"
                    )

                with c3:
                    st.write(
                        f"R$ {abs(row['valor']):,.2f}"
                    )

                with c4:

                    if st.button(
                        "✏️",
                        key=f"edit_transf_{row['id']}"
                    ):

                        popup_editar_transacao(row)

                with c5:

                    if st.button(
                        "🗑️",
                        key=f"del_transf_{row['id']}"
                    ):

                        excluir_transacao(
                            supabase_auth,
                            row["id"]
                        )

    # =====================================================
    # HISTÓRICO
    # =====================================================

    st.divider()

    st.subheader(
        "📜 Histórico Completo"
    )

    if not df.empty:

        df_exibir = df.drop(

            columns=[
                "user_id",
                "mes_ano",
                "conta"
            ],

            errors="ignore"

        )

        df_exibir = df_exibir.fillna("-")

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