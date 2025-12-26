import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÃO SUPABASE ---
# Pegue esses dados no painel do Supabase (Project Settings > API)
SUPABASE_URL = "https://vfbzvzajgbllbbnfrqbh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZmYnp2emFqZ2JsbGJibmZycWJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY2OTk2MjIsImV4cCI6MjA4MjI3NTYyMn0.b3Nk15L9Ez0i50kMpaOkBQEfOSY8GIhNYNmk9rycA9c"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Gran Turin - Gestão", layout="centered")

# --- FUNÇÕES DE BANCO DE DATA ---
def carregar_dados():
    response = supabase.table("estoque").select("*").execute()
    return pd.DataFrame(response.data)

def atualizar_banco(id_item, atual, minimo):
    supabase.table("estoque").update({"quantidade_atual": atual, "estoque_minimo": minimo}).eq("id", id_item).execute()

def excluir_item(id_item):
    supabase.table("estoque").delete().eq("id", id_item).execute()

def adicionar_item(categoria, produto, minimo):
    supabase.table("estoque").insert({
        "categoria": categoria,
        "produto": produto,
        "quantidade_atual": 0,
        "estoque_minimo": minimo
    }).execute()

# --- INTERFACE ---
st.title("🍊 Gran Turin - Gestão Total")
st.caption(f"Controle de Estoque Profissional - {datetime.now().strftime('%d/%m/%Y')}")

tab1, tab2, tab3 = st.tabs(["📦 Estoque", "🛒 Compras", "⚙️ Gerenciar"])

df = carregar_dados()

# --- ABA 1: ESTOQUE ---
with tab1:
    st.subheader("Conferência Diária")
    categorias = df['categoria'].unique()
    for cat in categorias:
        with st.expander(cat):
            itens = df[df['categoria'] == cat]
            for _, row in itens.iterrows():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                col1.write(f"**{row['produto']}**")
                novo_at = col2.number_input("Tem", value=int(row['quantidade_atual']), key=f"at_{row['id']}")
                novo_min = col3.number_input("Mín", value=int(row['estoque_minimo']), key=f"min_{row['id']}")
                
                if col4.button("💾", key=f"btn_{row['id']}"):
                    # Lógica de confirmação nativa do Streamlit
                    if novo_min != row['estoque_minimo']:
                        st.warning(f"Alterar mínimo de {row['produto']}?")
                        if st.button("Confirmar Alteração", key=f"conf_{row['id']}"):
                            atualizar_banco(row['id'], novo_at, novo_min)
                            st.success("Salvo!")
                            st.rerun()
                    else:
                        atualizar_banco(row['id'], novo_at, novo_min)
                        st.success("Salvo!")
                        st.rerun()

# --- ABA 2: COMPRAS ---
with tab2:
    st.subheader("Lista de Reposição")
    faltantes = df[df['quantidade_atual'] < df['estoque_minimo']]
    
    if faltantes.empty:
        st.success("✅ Tudo em dia!")
    else:
        msg_whatsapp = "*Lista Gran Turin*\n\n"
        for _, row in faltantes.iterrows():
            falta = row['estoque_minimo'] - row['quantidade_atual']
            item_str = f"• {row['produto']} (Faltam {falta} un.)"
            st.error(item_str)
            msg_whatsapp += item_str + "\n"
        
        link_wa = f"https://wa.me/?text={urllib.parse.quote(msg_whatsapp)}"
        st.link_button("Enviar para WhatsApp", link_wa, type="primary")

# --- ABA 3: GERENCIAR ---
with tab3:
    st.subheader("Novo Produto")
    with st.form("add_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        n_cat = c1.text_input("Categoria")
        n_prod = c2.text_input("Produto")
        n_min = c3.number_input("Mínimo", value=5)
        if st.form_submit_button("Cadastrar"):
            adicionar_item(n_cat, n_prod, n_min)
            st.success("Cadastrado!")
            st.rerun()
    
    st.divider()
    st.subheader("Remover Itens")
    for _, row in df.iterrows():
        c1, c2 = st.columns([4, 1])
        c1.write(f"{row['categoria']} > {row['produto']}")
        if c2.button("🗑️", key=f"del_{row['id']}"):
            excluir_item(row['id'])
            st.rerun()
