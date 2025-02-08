import streamlit as st
import sqlite3
import pandas as pd
import io
from PIL import Image
from datetime import datetime
import matplotlib.pyplot as plt

# Função para criar a tabela de login no banco de dados
def criar_tabela_login():
    conn = sqlite3.connect('estoque.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY,
                        username TEXT NOT NULL,
                        senha TEXT NOT NULL)''')
    conn.commit()
    conn.close()


# Função para criar a tabela de produtos no banco de dados
def criar_tabela_produtos():
    conn = sqlite3.connect('estoque.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY,
                    nome TEXT,
                    descricao TEXT,
                    preco REAL,
                    categoria TEXT,
                    qtd_estoque INTEGER,
                    fornecedor TEXT,
                    data_entrada TEXT,
                    numero_serie TEXT,
                    imagem BLOB
                )''')
    conn.commit()
    conn.close()


# Função para criar a tabela de vendas
def criar_tabela_vendas():
    conn = sqlite3.connect('estoque.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER,
                    nome_produto TEXT,
                    quantidade INTEGER,
                    preco_total REAL,
                    data_venda TEXT,
                    FOREIGN KEY (produto_id) REFERENCES produtos (id)
                )''')
    conn.commit()
    conn.close()


# Função para converter imagem para binário
def converter_imagem_para_binario(imagem):
    if imagem is not None:
        return imagem.read()
    return None

# Função para cadastrar um novo produto
def cadastrar_produto():
    st.subheader("Cadastrar Produto")

    with st.form("form_cadastro"):
        nome = st.text_input("Nome do Produto")
        descricao = st.text_input("Descrição")
        preco = st.number_input("Preço", min_value=0.0, format="%.2f")
        categoria = st.text_input("Categoria")
        qtd_estoque = st.number_input("Quantidade em estoque", min_value=0)
        fornecedor = st.text_input("Fornecedor (opcional)")
        data_entrada = st.date_input("Data de entrada (opcional)")
        numero_serie = st.text_input("Número de série (opcional)")
        imagem_file = st.file_uploader("Upload de Imagem", type=["jpg", "jpeg", "png"])

        submit = st.form_submit_button("Cadastrar")

    if submit:
        imagem_binario = converter_imagem_para_binario(imagem_file)

        conn = sqlite3.connect('estoque.db')
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO produtos
                        (nome, descricao, preco, categoria, qtd_estoque, fornecedor, data_entrada, numero_serie, imagem)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (nome, descricao, preco, categoria, qtd_estoque, fornecedor, data_entrada, numero_serie, imagem_binario))
        conn.commit()
        conn.close()
        st.success("Produto cadastrado com sucesso!")

# Função para exibir imagem a partir de binário
def exibir_imagem(binario):
    if binario:
        imagem = Image.open(io.BytesIO(binario))
        st.image(imagem, width=100)
    else:
        st.text("Sem imagem")

# Função para exibir produtos cadastrados
def exibir_produtos():
    conn = sqlite3.connect('estoque.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome, descricao, preco, categoria, qtd_estoque, fornecedor, data_entrada, numero_serie, imagem FROM produtos')
    produtos = cursor.fetchall()
    conn.close()

    if produtos:
        for produto in produtos:
            id_, nome, descricao, preco, categoria, qtd_estoque, fornecedor, data_entrada, numero_serie, imagem_binario = produto
            
            col1, col2 = st.columns([1, 3])

            # Exibir imagem na coluna 1
            with col1:
                exibir_imagem(imagem_binario)

            # Exibir informações do produto na coluna 2
            with col2:
                st.write(f"**ID:** {id_}")
                st.write(f"**Nome:** {nome}")
                st.write(f"**Descrição:** {descricao}")
                st.write(f"**Preço:** R$ {preco:.2f}")
                st.write(f"**Categoria:** {categoria}")
                st.write(f"**Quantidade em Estoque:** {qtd_estoque}")
                st.write(f"**Fornecedor:** {fornecedor}")
                st.write(f"**Data de Entrada:** {data_entrada}")
                st.write(f"**Número de Série:** {numero_serie}")
                st.write("---")
    else:
        st.info("Nenhum produto cadastrado.")

# Função para registrar uma venda
def registrar_venda():
    st.subheader("Registrar Venda")

    conn = sqlite3.connect('estoque.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome, preco, qtd_estoque FROM produtos')
    produtos = cursor.fetchall()

    if produtos:
        produto_escolhido = st.selectbox("Escolha o Produto", [(p[0], p[1], p[2], p[3]) for p in produtos], format_func=lambda x: f"{x[1]} (Estoque: {x[3]})")
        quantidade_vendida = st.number_input("Quantidade a Vender", min_value=1, max_value=produto_escolhido[3], step=1)
        
        if st.button("Registrar Venda"):
            preco_total = produto_escolhido[2] * quantidade_vendida
            data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Inserir a venda na tabela de vendas
            cursor.execute('''INSERT INTO vendas (produto_id, nome_produto, quantidade, preco_total, data_venda)
                            VALUES (?, ?, ?, ?, ?)''', (produto_escolhido[0], produto_escolhido[1], quantidade_vendida, preco_total, data_venda))

            # Atualizar a quantidade em estoque
            nova_quantidade = produto_escolhido[3] - quantidade_vendida
            cursor.execute('UPDATE produtos SET qtd_estoque = ? WHERE id = ?', (nova_quantidade, produto_escolhido[0]))

            conn.commit()
            conn.close()
            st.success(f"Venda registrada com sucesso! Total: R$ {preco_total:.2f}")
    else:
        st.warning("Nenhum produto disponível para venda.")


# Função para gerar o dashboard de vendas
def dashboard_vendas():
    st.subheader("Dashboard de Vendas")

    conn = sqlite3.connect('estoque.db')
    # Produtos mais vendidos
    vendas_df = pd.read_sql_query('SELECT nome_produto, SUM(quantidade) as total_vendido FROM vendas GROUP BY nome_produto ORDER BY total_vendido DESC', conn)

    # Produtos com estoque baixo
    estoque_df = pd.read_sql_query('SELECT nome, qtd_estoque, estoque_inicial FROM produtos WHERE qtd_estoque < 0.1 * estoque_inicial', conn)
    
    conn.close()

    # Gráfico de produtos mais vendidos
    if not vendas_df.empty:
        st.write("### Produtos Mais Vendidos")
        fig1, ax1 = plt.subplots()
        ax1.bar(vendas_df['nome_produto'], vendas_df['total_vendido'], color='green')
        ax1.set_xlabel("Produtos")
        ax1.set_ylabel("Quantidade Vendida")
        ax1.set_title("Top Produtos Mais Vendidos")
        st.pyplot(fig1)
    else:
        st.info("Nenhuma venda registrada ainda.")

    # Gráfico de produtos com estoque baixo
    if not estoque_df.empty:
        st.write("### Produtos com Estoque Baixo")
        fig2, ax2 = plt.subplots()
        ax2.bar(estoque_df['nome'], estoque_df['qtd_estoque'], color='red')
        ax2.set_xlabel("Produtos")
        ax2.set_ylabel("Estoque Atual")
        ax2.set_title("Produtos com Menos de 10% do Estoque Inicial")
        st.pyplot(fig2)
    else:
        st.info("Todos os produtos estão dentro dos níveis de estoque.")


# Função principal para o menu
def main():
    st.title("Sistema de Estoque - Super Mercado Willian")

    criar_tabela_login()
    criar_tabela_produtos()
    criar_tabela_vendas()

    # Estado de login
    if "login" not in st.session_state:
        st.session_state.login = False

    # Simulação de login simples
    if not st.session_state.login:
        st.subheader("Login")
        username = st.text_input("Nome de Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if username == "admin" and senha == "9805":
                st.success(f"Bem-vindo, {username}!")
                st.session_state.login = True
            else:
                st.error("Nome de usuário ou senha inválidos.")
    else:
        # Layout com menu e conteúdo
        col1, col2 = st.columns([1, 3])

        with col1:
            st.sidebar.markdown("## Menu")
            menu = ["Cadastrar Produto", "Visualizar Produtos", "Registrar Venda", "Dashboard de Vendas", "Logout"]
            escolha = st.sidebar.radio("Escolha uma opção", menu)

            if escolha == "Logout":
                st.session_state.login = False
                st.success("Você saiu com sucesso.")
                return

        with col2:
            if escolha == "Cadastrar Produto":
                cadastrar_produto()
            elif escolha == "Visualizar Produtos":
                exibir_produtos()
            elif escolha == "Registrar Venda":
                registrar_venda()
            elif escolha == "Dashboard de Vendas":
                dashboard_vendas()

if __name__ == "__main__":
    main()
