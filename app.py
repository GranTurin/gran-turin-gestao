import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÃO SUPABASE ---
SUPABASE_URL = "https://vfbzvzajgbllbbnfrqbh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZmYnp2emFqZ2JsbGJibmZycWJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY2OTk2MjIsImV4cCI6MjA4MjI3NTYyMn0.b3Nk15L9Ez0i50kMpaOkBQEfOSY8GIhNYNmk9rycA9c"

# Inicialização do Cliente
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Gran Turin - Gestão", layout="centered", page_icon="🍊")

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_dados():
    try:
        response = supabase.table("estoque").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        return pd.DataFrame()

def salvar_no_banco(id_item, atual, minimo):
    supabase.table("estoque").update({
        "quantidade_atual": atual, 
        "estoque_minimo": minimo
    }).eq("id", id_item).execute()
    st.success("Dados atualizados!")
    st.rerun()

# --- INTERFACE PRINCIPAL ---
st.title("🍊 Gran Turin - Gestão")
st.write(f"Sincronizado com Supabase | {datetime.now().strftime('%d/%m/%Y')}")

df = carregar_dados()

# Verifica se há dados para evitar o KeyError
if df.empty:
    st.info("O banco de dados está vazio. Cadastre o primeiro item na aba 'GERENCIAR'.")
    df = pd.DataFrame(columns=['id', 'categoria', 'produto', 'quantidade_atual', 'estoque_minimo'])

tab1, tab2, tab3 = st.tabs(["📦 CONFERIR ESTOQUE", "🛒 LISTA DE COMPRAS", "⚙️ GERENCIAR"])

# --- ABA 1: ESTOQUE (COM CONFIRMAÇÃO) ---
with tab1:
    if not df.empty:
        categorias = df['categoria'].unique()
        for cat in categorias:
            with st.expander(f"📁 Categoria: {cat}", expanded=True):
                itens = df[df['categoria'] == cat]
                for _, row in itens.iterrows():
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                        
                        col1.write(f"**{row['produto']}**")
                        novo_at = col2.number_input("Tem", value=int(row['quantidade_atual']), key=f"at_{row['id']}")
                        novo_min = col3.number_input("Mín", value=int(row['estoque_minimo']), key=f"min_{row['id']}")
                        
                        # Lógica de Confirmação
                        if col4.button("💾", key=f"btn_{row['id']}"):
                            # Se o estoque mínimo mudou, pede confirmação
                            if novo_min != row['estoque_minimo']:
                                st.warning(f"Confirmar novo mínimo de {novo_min} para {row['produto']}?")
                                if st.button("SIM, ALTERAR", key=f"confirm_{row['id']}"):
                                    salvar_no_banco(row['id'], novo_at, novo_min)
                            else:
                                # Se mudou apenas a quantidade atual, salva direto
                                salvar_no_banco(row['id'], novo_at, novo_min)
                    st.divider()

# --- ABA 2: COMPRAS + WHATSAPP ---
with tab2:
    faltantes = df[df['quantidade_atual'] < df['estoque_minimo']]
    if faltantes.empty:
        st.success("✅ Tudo em ordem no Gran Turin!")
    else:
        st.subheader("Itens abaixo do mínimo")
        texto_whats = f"*Lista de Compras Gran Turin - {datetime.now().strftime('%d/%m')}*\n\n"
        
        for _, row in faltantes.iterrows():
            qtd_necessaria = row['estoque_minimo'] - row['quantidade_atual']
            item_msg = f"• {row['produto']} (Faltam {qtd_necessaria} un.)"
            st.error(item_msg)
            texto_whats += item_msg + "\n"
        
        st.divider()
        link_wa = f"https://wa.me/?text={urllib.parse.quote(texto_whats)}"
        st.link_button("🚀 ENVIAR PARA WHATSAPP", link_wa, use_container_width=True)

# --- ABA 3: GERENCIAR (ADICIONAR/EXCLUIR) ---
with tab3:
    st.subheader("Novo Produto")
    with st.form("form_add", clear_on_submit=True):
        c1 = st.text_input("Nome da Categoria (ex: Grãos)")
        p1 = st.text_input("Nome do Produto (ex: Arroz)")
        m1 = st.number_input("Estoque Mínimo Inicial", min_value=1, value=5)
        if st.form_submit_button("CADASTRAR PRODUTO"):
            if c1 and p1:
                supabase.table("estoque").insert({
                    "categoria": c1, "produto": p1, 
                    "quantidade_atual": 0, "estoque_minimo": m1
                }).execute()
                st.success("Cadastrado com sucesso!")
                st.rerun()
    
    st.divider()
    st.subheader("Remover Itens")
    if not df.empty:
        for _, row in df.iterrows():
            col_a, col_b = st.columns([4, 1])
            col_a.write(f"{row['categoria']} | {row['produto']}")
            if col_b.button("🗑️", key=f"del_{row['id']}"):
                supabase.table("estoque").delete().eq("id", row['id']).execute()
                st.rerun()
