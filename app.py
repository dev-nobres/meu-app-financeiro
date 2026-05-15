# =========================================
# IMPORTAÇÃO DAS BIBLIOTECAS
# =========================================

# Streamlit -> cria a interface visual do app
import streamlit as st

# Pandas -> manipulação de tabelas/dados
import pandas as pd

# Date -> trabalhar com datas
from datetime import date

# Supabase -> conexão com banco online
from supabase import create_client, Client


# =========================================
# CONFIGURAÇÕES DA PÁGINA
# =========================================

# Define título da aba do navegador
# e layout da aplicação
st.set_page_config(
    page_title="NN | Controle Financeiro",
    layout="wide"
)


# =========================================
# CONEXÃO COM SUPABASE
# =========================================

# Lê dados secretos do arquivo:
# .streamlit/secrets.toml
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# Cria conexão com o Supabase
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================================
# SESSION STATE
# =========================================

# Session State funciona como memória temporária.
# Ele mantém informações enquanto o usuário
# navega dentro do app.

# Verifica se existe "usuario"
if "usuario" not in st.session_state:
    st.session_state.usuario = None

# Verifica se existe "logado"
if "logado" not in st.session_state:
    st.session_state.logado = False


# =========================================
# FUNÇÃO DE LOGIN E CADASTRO
# =========================================

def login():

    # Título da tela
    st.title("🏦 NN | Controle Financeiro")

    # Cria duas abas:
    # Entrar | Criar Conta
    aba1, aba2 = st.tabs([
        "Entrar",
        "Criar Conta"
    ])


    # =====================================
    # ABA LOGIN
    # =====================================

    with aba1:

        # Campo de email
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

                # Guarda usuário na sessão
                st.session_state.usuario = resposta.user

                # Marca como logado
                st.session_state.logado = True

                # Mensagem sucesso
                st.success("Login realizado!")

                # Atualiza tela
                st.rerun()

            except Exception as e:

                # Mostra erro caso login falhe
                st.error(f"Erro no login: {e}")


    # =====================================
    # ABA CADASTRO
    # =====================================

    with aba2:

        # Novo email
        novo_email = st.text_input(
            "Novo e-mail",
            key="novo_email"
        )

        # Nova senha
        nova_senha = st.text_input(
            "Nova senha",
            type="password",
            key="nova_senha"
        )

        # Botão criar conta
        if st.button("Criar Conta"):

            try:

                # Cria usuário no Supabase
                supabase.auth.sign_up({
                    "email": novo_email,
                    "password": nova_senha
                })

                st.success(
                    "Conta criada! Verifique seu e-mail."
                )

            except Exception as e:

                st.error(f"Erro: {e}")


# =========================================
# FUNÇÃO CARREGAR TRANSAÇÕES
# =========================================

def carregar_transacoes(user_id):

    try:

        # Busca transações do usuário
        resposta = supabase.table("transacoes") \
            .select("*") \
            .eq("user_id", user_id) \
            .execute()

        # Dados retornados
        dados = resposta.data

        # Se não houver dados
        if not dados:
            return pd.DataFrame()

        # Converte para DataFrame
        df = pd.DataFrame(dados)

        return df

    except Exception as e:

        st.error(f"Erro ao carregar dados: {e}")

        return pd.DataFrame()


# =========================================
# FUNÇÃO CARREGAR CATEGORIAS
# =========================================

def carregar_categorias(tabela, user_id):

    try:

        # Busca categorias do usuário
        resposta = supabase.table(tabela) \
            .select("*") \
            .eq("user_id", user_id) \
            .execute()

        return resposta.data

    except Exception as e:

        st.error(f"Erro categorias: {e}")

        return []


# =========================================
# DASHBOARD PRINCIPAL
# =========================================

def dashboard():

    # Usuário atual
    usuario = st.session_state.usuario

    # ID do usuário
    user_id = usuario.id


    # =====================================
    # SIDEBAR
    # =====================================

    with st.sidebar:

        # Exibe email
        st.write(f"👤 {usuario.email}")

        # Botão sair
        if st.button("🚪 Sair"):

            # Limpa sessão
            st.session_state.usuario = None
            st.session_state.logado = False

            st.rerun()


    # =====================================
    # TÍTULO
    # =====================================

    st.title("📊 Dashboard Financeiro")


    # =====================================
    # GERENCIAMENTO DE CATEGORIAS
    # =====================================

    # Expander -> bloco expansível
    with st.expander("⚙️ Gerenciar Categorias"):

        # Divide tela em 2 colunas
        col1, col2 = st.columns(2)


        # =================================
        # RECEITAS
        # =================================

        with col1:

            st.subheader("🟢 Receitas")

            # Carrega categorias receita
            categorias = carregar_categorias(
                "categorias_receita",
                user_id
            )

            # Mostra categorias
            for cat in categorias:
                st.write(f"• {cat['nome']}")

            # Campo nova categoria
            nova_categoria = st.text_input(
                "Nova categoria receita"
            )

            # Botão adicionar
            if st.button("Adicionar Receita"):

                # Validação
                if nova_categoria != "":

                    try:

                        # Insere no banco
                        supabase.table(
                            "categorias_receita"
                        ).insert({

                            "nome": nova_categoria,
                            "user_id": user_id

                        }).execute()

                        st.success("Categoria criada!")

                        st.rerun()

                    except Exception as e:

                        st.error(f"Erro: {e}")


        # =================================
        # DESPESAS
        # =================================

        with col2:

            st.subheader("🔴 Despesas")

            categorias = carregar_categorias(
                "categorias_despesa",
                user_id
            )

            for cat in categorias:
                st.write(f"• {cat['nome']}")

            nova_categoria_desp = st.text_input(
                "Nova categoria despesa"
            )

            if st.button("Adicionar Despesa"):

                if nova_categoria_desp != "":

                    try:

                        supabase.table(
                            "categorias_despesa"
                        ).insert({

                            "nome": nova_categoria_desp,
                            "user_id": user_id

                        }).execute()

                        st.success("Categoria criada!")

                        st.rerun()

                    except Exception as e:

                        st.error(f"Erro: {e}")


    # =====================================
    # NOVA TRANSAÇÃO
    # =====================================

    st.divider()

    st.subheader("➕ Novo Lançamento")


    # Tipo da transação
    tipo = st.selectbox(
        "Tipo",
        ["Receita", "Despesa"]
    )


    # Define qual tabela usar
    tabela = (
        "categorias_receita"
        if tipo == "Receita"
        else "categorias_despesa"
    )


    # Busca categorias
    categorias = carregar_categorias(
        tabela,
        user_id
    )


    # Lista somente nomes
    opcoes = [c["nome"] for c in categorias]


    # Campos formulário
    data = st.date_input("Data")

    categoria = st.selectbox(
        "Categoria",
        opcoes if opcoes else ["Sem categoria"]
    )

    valor = st.number_input(
        "Valor",
        min_value=0.0,
        step=1.0
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

            # Se for despesa:
            # transforma em valor negativo
            valor_final = valor

            if tipo == "Despesa":
                valor_final = -valor


            # Insere no banco
            supabase.table("transacoes").insert({

                "data": str(data),
                "categoria": categoria,
                "valor": valor_final,
                "conta": conta,
                "tipo": tipo,
                "status": status,
                "user_id": user_id

            }).execute()

            st.success("Transação salva!")

            st.rerun()

        except Exception as e:

            st.error(f"Erro: {e}")


    # =====================================
    # TABELA DE TRANSAÇÕES
    # =====================================

    st.divider()

    st.subheader("📋 Transações")


    # Carrega dados
    df = carregar_transacoes(user_id)


    # Se houver dados
    if not df.empty:

        # Mostra tabela
        st.dataframe(
            df,
            use_container_width=True
        )

        # Soma todos valores
        total = df["valor"].sum()

        # Exibe saldo
        st.metric(
            "Saldo Atual",
            f"R$ {total:,.2f}"
        )

    else:

        st.info("Nenhuma transação encontrada.")


# =========================================
# CONTROLE PRINCIPAL DO APP
# =========================================

# Se usuário NÃO estiver logado
if not st.session_state.logado:

    # Mostra tela login
    login()

# Se estiver logado
else:

    # Mostra dashboard
    dashboard()