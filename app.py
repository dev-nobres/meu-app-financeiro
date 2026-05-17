# =========================================
# IMPORTAÇÃO DAS BIBLIOTECAS
# =========================================

# Streamlit -> Interface visual
import streamlit as st

# Pandas -> Manipulação de tabelas
import pandas as pd

# Date -> Trabalhar com datas
from datetime import date

# Supabase -> Banco de dados online
from supabase import create_client, Client

# APIError -> Captura erros do Postgres/Supabase
from postgrest import APIError


# =========================================
# CONFIGURAÇÕES DA PÁGINA
# =========================================

# Configura título da aba do navegador
# e largura da página
st.set_page_config(
    page_title="NN | Controle Financeiro",
    layout="wide"
)


# =========================================
# LEITURA DAS SECRETS
# =========================================

# Busca credenciais do arquivo:
# .streamlit/secrets.toml
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


# =========================================
# CLIENTE PRINCIPAL SUPABASE
# =========================================

# Esse cliente é "anônimo".
# Ele serve para:
# - login
# - cadastro
# - auth
#
# MAS NÃO SERVE para RLS autenticado.
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================================
# SESSION STATE
# =========================================

# Session State funciona como memória.
# Mantém dados vivos enquanto o usuário
# usa o app.

# Usuário logado
if "usuario" not in st.session_state:
    st.session_state.usuario = None

# Sessão JWT
if "session" not in st.session_state:
    st.session_state.session = None

# Access Token JWT
if "access_token" not in st.session_state:
    st.session_state.access_token = None

# Controle login
if "logado" not in st.session_state:
    st.session_state.logado = False


# =========================================
# CLIENTE AUTENTICADO JWT
# =========================================

# ESSA É A PARTE MAIS IMPORTANTE
#
# Essa função cria um cliente Supabase
# usando o JWT do usuário autenticado.
#
# Isso faz o PostgreSQL reconhecer:
#
# auth.uid()
#
# E então o RLS funciona corretamente.

def get_authenticated_client():

    # Busca token salvo na sessão
    access_token = st.session_state.get(
        "access_token"
    )

    # Se não houver token
    if not access_token:
        return None

    # Cria novo cliente
    client = create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )

    # Injeta JWT no PostgREST
    #
    # Isso envia:
    #
    # Authorization: Bearer TOKEN
    #
    # para o Supabase.
    client.postgrest.auth(access_token)

    return client


# =========================================
# LOGIN E CADASTRO
# =========================================

def login():

    st.title("🏦 NN | Controle Financeiro")

    # Cria abas
    aba1, aba2 = st.tabs([
        "Entrar",
        "Criar Conta"
    ])


    # =====================================
    # ABA LOGIN
    # =====================================

    with aba1:

        # Campo email
        email = st.text_input("E-mail")

        # Campo senha
        senha = st.text_input(
            "Senha",
            type="password"
        )

        # Botão login
        if st.button("Entrar"):

            try:

                # Faz login no Supabase
                resposta = supabase.auth.sign_in_with_password({

                    "email": email,
                    "password": senha

                })

                # =================================
                # SALVANDO USUÁRIO
                # =================================

                # Dados do usuário
                st.session_state.usuario = resposta.user

                # Sessão completa
                st.session_state.session = resposta.session

                # JWT ACCESS TOKEN
                #
                # ESSENCIAL para RLS
                st.session_state.access_token = (
                    resposta.session.access_token
                )

                # Marca como logado
                st.session_state.logado = True

                st.success("Login realizado!")

                st.rerun()

            except Exception as e:

                st.error(f"Erro login: {e}")


    # =====================================
    # ABA CADASTRO
    # =====================================

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

                # Cria usuário no Supabase
                supabase.auth.sign_up({

                    "email": novo_email,
                    "password": nova_senha

                })

                st.success(
                    "Conta criada! Verifique o e-mail."
                )

            except Exception as e:

                st.error(f"Erro cadastro: {e}")


# =========================================
# CARREGAR CATEGORIAS
# =========================================

def carregar_categorias(
    client,
    tabela,
    user_id
):

    try:

        # Busca categorias do usuário
        resposta = client.table(tabela) \
            .select("*") \
            .eq("user_id", user_id) \
            .execute()

        return resposta.data

    except Exception as e:

        st.error(f"Erro categorias: {e}")

        return []


# =========================================
# CARREGAR TRANSAÇÕES
# =========================================

def carregar_transacoes(
    client,
    user_id
):

    try:

        resposta = client.table("transacoes") \
            .select("*") \
            .eq("user_id", user_id) \
            .execute()

        dados = resposta.data

        # Se vazio
        if not dados:
            return pd.DataFrame()

        # Converte em tabela
        df = pd.DataFrame(dados)

        return df

    except Exception as e:

        st.error(f"Erro transações: {e}")

        return pd.DataFrame()


# =========================================
# DASHBOARD PRINCIPAL
# =========================================

def dashboard():

    # =====================================
    # DADOS USUÁRIO
    # =====================================

    usuario = st.session_state.usuario

    user_id = usuario.id


    # =====================================
    # CLIENTE JWT AUTENTICADO
    # =====================================

    # AQUI está o segredo do RLS.
    #
    # Agora TODAS queries terão JWT.
    supabase_auth = get_authenticated_client()


    # Segurança extra
    if not supabase_auth:

        st.error("Sessão inválida.")

        st.stop()


    # =====================================
    # SIDEBAR
    # =====================================

    with st.sidebar:

        st.write(f"👤 {usuario.email}")

        # DEBUG JWT
        #
        # Pode remover depois
        with st.expander("JWT Debug"):

            st.write(
                st.session_state.access_token
            )

        # Logout
        if st.button("🚪 Sair"):

            st.session_state.usuario = None
            st.session_state.session = None
            st.session_state.access_token = None
            st.session_state.logado = False

            st.rerun()


    # =====================================
    # TÍTULO
    # =====================================

    st.title("📊 Dashboard Financeiro")


    # =====================================
    # GERENCIAR CATEGORIAS
    # =====================================

    with st.expander("⚙️ Gerenciar Categorias"):

        col1, col2 = st.columns(2)


        # =================================
        # RECEITAS
        # =================================

        with col1:

            st.subheader("🟢 Receitas")

            categorias_receita = carregar_categorias(
                supabase_auth,
                "categorias_receita",
                user_id
            )

            # Lista categorias
            for cat in categorias_receita:

                st.write(f"• {cat['nome']}")

            # Nova categoria
            nova_categoria = st.text_input(
                "Nova categoria receita"
            )

            # Botão adicionar
            if st.button("Adicionar Receita"):

                try:

                    # INSERT COM JWT
                    #
                    # Agora o auth.uid()
                    # funciona corretamente.
                    supabase_auth.table(
                        "categorias_receita"
                    ).insert({

                        "nome": nova_categoria,
                        "user_id": user_id

                    }).execute()

                    st.success(
                        "Categoria criada!"
                    )

                    st.rerun()

                except APIError as e:

                    st.error(f"Erro API: {e}")

                except Exception as e:

                    st.error(f"Erro geral: {e}")


        # =================================
        # DESPESAS
        # =================================

        with col2:

            st.subheader("🔴 Despesas")

            categorias_despesa = carregar_categorias(
                supabase_auth,
                "categorias_despesa",
                user_id
            )

            for cat in categorias_despesa:

                st.write(f"• {cat['nome']}")

            nova_despesa = st.text_input(
                "Nova categoria despesa"
            )

            if st.button("Adicionar Despesa"):

                try:

                    supabase_auth.table(
                        "categorias_despesa"
                    ).insert({

                        "nome": nova_despesa,
                        "user_id": user_id

                    }).execute()

                    st.success(
                        "Categoria criada!"
                    )

                    st.rerun()

                except APIError as e:

                    st.error(f"Erro API: {e}")

                except Exception as e:

                    st.error(f"Erro geral: {e}")


    # =====================================
    # NOVA TRANSAÇÃO
    # =====================================

    st.divider()

    st.subheader("➕ Novo Lançamento")


    # Tipo transação
    tipo = st.selectbox(
        "Tipo",
        ["Receita", "Despesa"]
    )


    # Escolhe tabela categorias
    tabela = (
        "categorias_receita"
        if tipo == "Receita"
        else "categorias_despesa"
    )


    # Carrega categorias
    categorias = carregar_categorias(
        supabase_auth,
        tabela,
        user_id
    )


    # Extrai nomes
    opcoes = [c["nome"] for c in categorias]


    # Campos formulário
    data = st.date_input("Data")

    categoria = st.selectbox(
        "Categoria",
        opcoes if opcoes else ["Sem categoria"]
    )

    valor = st.number_input(
        "Valor",
        min_value=0.0
    )

    conta = st.text_input(
        "Conta",
        value="Carteira"
    )

    status = st.selectbox(
        "Status",
        ["Pago", "Pendente"]
    )


    # =====================================
    # SALVAR TRANSAÇÃO
    # =====================================

    if st.button("Salvar Transação"):

        try:

            # Despesa = negativo
            valor_final = valor

            if tipo == "Despesa":

                valor_final = -valor


            # INSERT COM JWT
            supabase_auth.table(
                "transacoes"
            ).insert({

                "data": str(data),
                "categoria": categoria,
                "valor": valor_final,
                "conta": conta,
                "tipo": tipo,
                "status": status,
                "user_id": user_id

            }).execute()

            st.success(
                "Transação salva!"
            )

            st.rerun()

        except APIError as e:

            st.error(f"Erro API: {e}")

        except Exception as e:

            st.error(f"Erro geral: {e}")


    # =====================================
    # TABELA DE TRANSAÇÕES
    # =====================================

    st.divider()

    st.subheader("📋 Transações")


    # Carrega tabela
    df = carregar_transacoes(
        supabase_auth,
        user_id
    )


    # Se houver dados
    if not df.empty:

        # Mostra tabela
        st.dataframe(
            df,
            use_container_width=True
        )

        # Soma valores
        total = df["valor"].sum()

        # Métrica saldo
        st.metric(
            "Saldo Atual",
            f"R$ {total:,.2f}"
        )

    else:

        st.info(
            "Nenhuma transação encontrada."
        )


# =========================================
# CONTROLE PRINCIPAL APP
# =========================================

# Se NÃO estiver logado
if not st.session_state.logado:

    login()

# Se estiver logado
else:

    dashboard()
