import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÃO SUPABASE ---
SUPABASE_URL = "https://vfbzvzajgbllbbnfrqbh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZmYnp2emFqZ2JsbGJibmZycWJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY2OTk2MjIsImV4cCI6MjA4MjI3NTYyMn0.b3Nk15L9Ez0i50kMpaOkBQEfOSY8GIhNYNmk9rycA9c"

# Inicialização segura do cliente
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Erro ao conectar ao Supabase: {e}")

st.set_page_config(page_title="Gran Turin - Gestão", layout="centered", page_icon="🍊")

# --- FUNÇÕES DE DADOS ---
def carregar_dados():
    try:
        response = supabase.table("estoque").select("*").execute()
        if response.data:
            temp_df = pd.DataFrame(response.data)
            # RESOLVE O CASE SENSITIVE: Força nomes de colunas para minúsculo
            temp_df.columns = [c.lower() for c in temp_df.columns]
            return temp_df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler banco de dados: {e}")
        return pd.DataFrame()

def salvar_dados(id_item, atual, minimo):
    try:
        # Importante: Os nomes aqui devem bater com o que está no Supabase
        supabase.table("estoque").update({
            "quantidade_atual": atual, 
            "estoque_minimo": minimo
        }).eq("id", id_item).execute()
        st.success("Alteração salva com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# --- INTERFACE ---
st.title("🍊 Gran Turin - Gestão Total")

# Carregamento inicial
df = carregar_dados()

# Proteção contra DataFrame vazio (evita o KeyError inicial)
if df.empty:
    st.info("👋 Bem-vindo! Vá na aba '⚙️ GERENCIAR' para cadastrar seu primeiro item.")
    # Estrutura padrão para não quebrar o código
    df = pd.DataFrame(columns=['id', 'categoria', 'produto', 'quantidade_atual', 'estoque_minimo'])

tab1, tab2, tab3 = st.tabs(["📦 ESTOQUE", "🛒 COMPRAS", "⚙️ GERENCIAR"])

# --- ABA 1: CONFERÊNCIA ---
with tab1:
    if not df.empty and 'categoria' in df.columns:
        categorias = sorted(df['categoria'].unique())
        for cat in categorias:
            with st.expander(f"📂 {cat.upper()}", expanded=True):
                itens = df[df['categoria'] == cat]
                for _, row in itens.iterrows():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    col1.write(f"**{row['produto']}**")
                    
                    # Garantia de valores numéricos para evitar erros de cálculo
                    val_atual = int(row['quantidade_atual']) if pd.notnull(row['quantidade_atual']) else 0
                    val_minimo = int(row['estoque_minimo']) if pd.notnull(row['estoque_minimo']) else 0
                    
                    n_at = col2.number_input("Tem", value=val_atual, key=f"at_{row['id']}")
                    n_min = col3.number_input("Mín", value=val_minimo, key=f"min_{row['id']}")
                    
                    # Botão Salvar com Confirmação para Estoque Mínimo
                    if col4.button("💾", key=f"btn_{row['id']}"):
                        if n_min != val_minimo:
                            st.warning(f"Alterar mínimo de {row['produto']} para {n_min}?")
                            if st.button("CONFIRMAR MUDANÇA", key=f"conf_{row['id']}"):
                                salvar_dados(row['id'], n_at, n_min)
                        else:
                            salvar_dados(row['id'], n_at, n_min)
                    st.divider()

# --- ABA 2: LISTA DE COMPRAS ---
with tab2:
    if not df.empty:
        # Filtra quem está abaixo do mínimo
        comprar = df[df['quantidade_atual'] < df['estoque_minimo']]
        
        if comprar.empty:
            st.success("✅ Estoque completo! Nada para comprar.")
        else:
            msg_wpp = f"*Lista de Compras Gran Turin - {datetime.now().strftime('%d/%m')}*\n\n"
            for _, row in comprar.iterrows():
                falta = int(row['estoque_minimo']) - int(row['quantidade_atual'])
                linha = f"• {row['produto']} (Faltam {falta} un.)"
                st.error(linha)
                msg_wpp += linha + "\n"
            
            st.divider()
            link = f"https://wa.me/?text={urllib.parse.quote(msg_wpp)}"
            st.link_button("📲 ENVIAR PARA WHATSAPP", link, use_container_width=True)

# --- ABA 3: GERENCIAMENTO ---
with tab3:
    st.subheader("Cadastrar Novo Produto")
    with st.form("novo_produto", clear_on_submit=True):
        f_cat = st.text_input("Categoria (ex: Grãos, Carnes)")
        f_prod = st.text_input("Nome do Produto")
        f_min = st.number_input("Estoque Mínimo", value=5, min_value=1)
        
        if st.form_submit_button("ADICIONAR AO SISTEMA"):
            if f_cat and f_prod:
                supabase.table("estoque").insert({
                    "categoria": f_cat,
                    "produto": f_prod,
                    "quantidade_atual": 0,
                    "estoque_minimo": f_min
                }).execute()
                st.success("Produto cadastrado!")
                st.rerun()
            else:
                st.error("Preencha Categoria e Produto!")

    st.divider()
    if not df.empty:
        st.subheader("Excluir Produtos")
        for _, row in df.iterrows():
            c_a, c_b = st.columns([4, 1])
            c_a.write(f"{row['categoria']} | {row['produto']}")
            if c_b.button("🗑️", key=f"del_{row['id']}"):
                supabase.table("estoque").delete().eq("id", row['id']).execute()
                st.success("Removido!")
                st.rerun()
