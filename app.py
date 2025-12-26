import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÃO DE ACESSO ---
URL = "https://vfbzvzajgbllbbnfrqbh.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZmYnp2emFqZ2JsbGJibmZycWJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY2OTk2MjIsImV4cCI6MjA4MjI3NTYyMn0.b3Nk15L9Ez0i50kMpaOkBQEfOSY8GIhNYNmk9rycA9c"

# Inicialização do Cliente Supabase
try:
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error(f"Erro de Conexão: {e}")

st.set_page_config(page_title="Gran Turin - Gestão", layout="centered", page_icon="🍊")

# --- FUNÇÕES DE APOIO ---
def carregar_dados():
    try:
        res = supabase.table("estoque").select("*").execute()
        if res.data:
            df_res = pd.DataFrame(res.data)
            # Normaliza nomes de colunas para evitar KeyError
            df_res.columns = [c.lower() for c in df_res.columns]
            return df_res
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def atualizar_item(id_item, atual, minimo):
    supabase.table("estoque").update({
        "quantidade_atual": atual, 
        "estoque_minimo": minimo
    }).eq("id", id_item).execute()
    st.success("Sincronizado!")
    st.rerun()

# --- ESTILIZAÇÃO E TÍTULO ---
st.title("🍊 Gran Turin - Gestão Total")
st.caption(f"Conectado ao Banco de Dados | {datetime.now().strftime('%d/%m/%Y %H:%M')}")

df = carregar_dados()

# Criar estrutura básica caso o DF venha vazio para não quebrar a lógica das abas
if df.empty:
    colunas_padrao = ['id', 'categoria', 'produto', 'quantidade_atual', 'estoque_minimo']
    df = pd.DataFrame(columns=colunas_padrao)

tab1, tab2, tab3 = st.tabs(["📦 ESTOQUE", "🛒 COMPRAS", "⚙️ GERENCIAR"])

# --- ABA 1: CONFERÊNCIA DIÁRIA ---
with tab1:
    if df.empty or len(df) == 0:
        st.info("Nenhum produto cadastrado ainda. Vá na aba Gerenciar.")
    else:
        categorias = sorted(df['categoria'].unique())
        for cat in categorias:
            with st.expander(f"📁 {cat.upper()}", expanded=True):
                itens = df[df['categoria'] == cat]
                for _, row in itens.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                    
                    c1.write(f"**{row['produto']}**")
                    
                    # Inputs numéricos
                    n_at = c2.number_input("Tem", value=int(row['quantidade_atual']), key=f"at_{row['id']}")
                    n_min = c3.number_input("Mín", value=int(row['estoque_minimo']), key=f"min_{row['id']}")
                    
                    # Botão Salvar com lógica de confirmação para o Mínimo
                    if c4.button("💾", key=f"btn_{row['id']}"):
                        if n_min != int(row['estoque_minimo']):
                            st.warning(f"Alterar mínimo de {row['produto']}?")
                            if st.button("CONFIRMAR MUDANÇA", key=f"conf_{row['id']}"):
                                atualizar_item(row['id'], n_at, n_min)
                        else:
                            atualizar_item(row['id'], n_at, n_min)
                    st.divider()

# --- ABA 2: LISTA DE COMPRAS ---
with tab2:
    # Filtra produtos abaixo do mínimo
    df_compras = df[df['quantidade_atual'] < df['estoque_minimo']]
    
    if df_compras.empty:
        st.success("✅ Tudo em dia! Estoque abastecido.")
    else:
        st.subheader("Itens Necessários")
        texto_whats = f"*Lista Gran Turin ({datetime.now().strftime('%d/%m')})*\n\n"
        
        for _, r in df_compras.iterrows():
            necessario = int(r['estoque_minimo']) - int(r['quantidade_atual'])
            msg = f"• {r['produto']} (Faltam {necessario} un.)"
            st.error(msg)
            texto_whats += msg + "\n"
        
        st.divider()
        link_wa = f"https://wa.me/?text={urllib.parse.quote(texto_whats)}"
        st.link_button("🚀 ENVIAR LISTA VIA WHATSAPP", link_wa, use_container_width=True)

# --- ABA 3: GERENCIAR (CRUD) ---
with tab3:
    st.subheader("Cadastrar Novo Item")
    with st.form("novo_item_form", clear_on_submit=True):
        col_cat, col_prod, col_min = st.columns([2, 2, 1])
        new_cat = col_cat.text_input("Categoria")
        new_prod = col_prod.text_input("Produto")
        new_min = col_min.number_input("Mínimo", value=5, min_value=1)
        
        if st.form_submit_button("ADICIONAR"):
            if new_cat and new_prod:
                try:
                    supabase.table("estoque").insert({
                        "categoria": new_cat,
                        "produto": new_prod,
                        "quantidade_atual": 0,
                        "estoque_minimo": new_min
                    }).execute()
                    st.success("Adicionado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha os nomes da categoria e do produto.")

    st.divider()
    if not df.empty and len(df) > 0:
        st.subheader("Excluir Itens do Sistema")
        for _, row in df.iterrows():
            ca, cb = st.columns([4, 1])
            ca.write(f"{row['categoria']} | {row['produto']}")
            if cb.button("🗑️", key=f"del_{row['id']}"):
                supabase.table("estoque").delete().eq("id", row['id']).execute()
                st.rerun()
