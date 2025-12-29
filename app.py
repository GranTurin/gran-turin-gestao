import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÃO DE ACESSO ---
# ⚠️ IMPORTANTE: Substitua a KEY pela nova chave 'anon' do seu painel Supabase
URL = "https://vfbzvzajgbllbbnfrqbh.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZmYnp2emFqZ2JsbGJibmZycWJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY2OTk2MjIsImV4cCI6MjA4MjI3NTYyMn0.b3Nk15L9Ez0i50kMpaOkBQEfOSY8GIhNYNmk9rycA9c"

try:
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error(f"Erro de Conexão: {e}")

# Alteração de nome solicitada
st.set_page_config(page_title="Gestão de Estoque Gran Turin", layout="centered", page_icon="🍊")

def carregar_dados():
    try:
        res = supabase.table("estoque").select("*").execute()
        if res.data:
            df_res = pd.DataFrame(res.data)
            df_res.columns = [c.lower() for c in df_res.columns]
            return df_res.sort_values(['categoria', 'produto'])
        return pd.DataFrame()
    except Exception as e:
        # Silenciamos o erro aqui para não quebrar a UI, mas avisamos se for 401
        if "401" in str(e):
            st.error("Chave API Inválida. Por favor, atualize a KEY no código.")
        return pd.DataFrame()

def atualizar_item(id_item, atual, minimo):
    supabase.table("estoque").update({
        "quantidade_atual": atual, 
        "estoque_minimo": minimo
    }).eq("id", id_item).execute()
    st.toast("Sincronizado!", icon="✅")
    st.rerun()

# --- TÍTULO ---
st.title("🍊 Gestão de Estoque Gran Turin")

df = carregar_dados()

tab1, tab2, tab3 = st.tabs(["📦 ESTOQUE", "🛒 COMPRAS", "⚙️ GERENCIAR"])

# --- ABA 1: CONFERÊNCIA ---
with tab1:
    if df.empty:
        st.info("Nenhum produto cadastrado.")
    else:
        for cat in sorted(df['categoria'].unique()):
            with st.expander(f"📁 {cat.upper()}", expanded=False):
                itens = df[df['categoria'] == cat]
                for _, row in itens.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                    c1.markdown(f"**{row['produto']}**")
                    n_at = c2.number_input("Tem", value=int(row['quantidade_atual']), key=f"at_{row['id']}")
                    n_min = c3.number_input("Mín", value=int(row['estoque_minimo']), key=f"min_{row['id']}")
                    if c4.button("💾", key=f"btn_{row['id']}"):
                        atualizar_item(row['id'], n_at, n_min)
                    st.divider()

# --- ABA 2: LISTA DE COMPRAS ---
with tab2:
    if not df.empty:
        df_compras = df[df['quantidade_atual'].astype(int) < df['estoque_minimo'].astype(int)]
        if df_compras.empty:
            st.success("✅ Estoque em dia!")
        else:
            st.subheader("Itens para Comprar")
            texto_whats = f"*Lista Gran Turin ({datetime.now().strftime('%d/%m')})*\n\n"
            for _, r in df_compras.iterrows():
                necessario = int(r['estoque_minimo']) - int(r['quantidade_atual'])
                msg = f"• {r['produto']} (Faltam {necessario} un.)"
                st.warning(msg)
                texto_whats += msg + "\n"
            st.divider()
            link_wa = f"https://wa.me/?text={urllib.parse.quote(texto_whats)}"
            st.link_button("🚀 ENVIAR WHATSAPP", link_wa, use_container_width=True)

# --- ABA 3: GERENCIAR (Cadastro com Categorias Salvas) ---
with tab3:
    st.subheader("Cadastrar Novo Item")
    
    # Lógica de Categorias Dinâmicas
    categorias_existentes = []
    if not df.empty:
        categorias_existentes = sorted(df['categoria'].unique().tolist())
    
    opcoes_cat = ["-- Selecione --", "+ Nova Categoria"] + categorias_existentes
    
    with st.form("novo_item_form", clear_on_submit=True):
        cat_selecionada = st.selectbox("Escolha a Categoria", options=opcoes_cat)
        
        # Campo que aparece apenas se precisar de categoria nova
        nova_cat_input = st.text_input("Se for nova categoria, digite o nome aqui:")
        
        col_prod, col_min = st.columns([3, 1])
        new_prod = col_prod.text_input("Nome do Produto")
        new_min = col_min.number_input("Estoque Mínimo", value=5, min_value=0)
        
        if st.form_submit_button("ADICIONAR PRODUTO", use_container_width=True):
            # Lógica para decidir qual categoria usar
            if cat_selecionada == "+ Nova Categoria":
                categoria_final = nova_cat_input.strip().upper()
            else:
                categoria_final = cat_selecionada
            
            if categoria_final and categoria_final != "-- Selecione --" and new_prod:
                supabase.table("estoque").insert({
                    "categoria": categoria_final,
                    "produto": new_prod.strip(),
                    "quantidade_atual": 0,
                    "estoque_minimo": new_min
                }).execute()
                st.success(f"Produto {new_prod} cadastrado!")
                st.rerun()
            else:
                st.error("Preencha a categoria e o nome do produto.")

    st.divider()
    if not df.empty:
        with st.expander("Excluir Produtos"):
            for _, row in df.iterrows():
                ca, cb = st.columns([4, 1])
                ca.write(f"**{row['categoria']}** | {row['produto']}")
                if cb.button("🗑️", key=f"del_{row['id']}"):
                    supabase.table("estoque").delete().eq("id", row['id']).execute()
                    st.rerun()
