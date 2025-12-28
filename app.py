import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÃO ---
URL = "https://vfbzvzajgbllbbnfrqbh.supabase.co"
KEY = "SUA_CHAVE_AQUI" 

try:
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error(f"Erro de Conexão: {e}")

# 1. NOVO NOME CONFORME SOLICITADO
st.set_page_config(page_title="Gestão de Estoque Gran Turin", layout="centered", page_icon="🍊")

# --- FUNÇÕES ---
def carregar_dados():
    try:
        res = supabase.table("estoque").select("*").execute()
        if res.data:
            df_res = pd.DataFrame(res.data)
            # Normaliza TODAS as colunas para minúsculo para evitar KeyError
            df_res.columns = [c.lower() for c in df_res.columns]
            return df_res.sort_values(['categoria', 'produto'])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def atualizar_item(id_item, atual, minimo):
    try:
        supabase.table("estoque").update({
            "quantidade_atual": atual, 
            "estoque_minimo": minimo
        }).eq("id", id_item).execute()
        st.toast("Estoque Atualizado!", icon="✅")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# --- TÍTULO ---
st.title("🍊 Gestão de Estoque Gran Turin")

df = carregar_dados()

# Garantir que as colunas mínimas existam no DF mesmo que vazio para evitar erros
colunas_necessarias = ['id', 'categoria', 'produto', 'quantidade_atual', 'estoque_minimo']
if df.empty:
    df = pd.DataFrame(columns=colunas_necessarias)

tab1, tab2, tab3 = st.tabs(["📦 ESTOQUE", "🛒 COMPRAS", "⚙️ GERENCIAR"])

# --- ABA 1: CONFERÊNCIA ---
with tab1:
    if df.empty or len(df) == 0:
        st.info("Nenhum produto encontrado. Cadastre na aba Gerenciar.")
    else:
        for cat in sorted(df['categoria'].unique()):
            with st.expander(f"📁 {cat.upper()}", expanded=True):
                itens = df[df['categoria'] == cat]
                for _, row in itens.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                    c1.markdown(f"**{row['produto']}**")
                    
                    # Uso de int() para garantir que não haja erro de tipo
                    n_at = c2.number_input("Tem", value=int(row['quantidade_atual']), key=f"at_{row['id']}")
                    n_min = c3.number_input("Mín", value=int(row['estoque_minimo']), key=f"min_{row['id']}")
                    
                    if c4.button("💾", key=f"btn_{row['id']}"):
                        atualizar_item(row['id'], n_at, n_min)
                    st.divider()

# --- ABA 2: LISTA DE COMPRAS ---
with tab2:
    # Lógica de compras
    df_compras = df[df['quantidade_atual'].astype(int) < df['estoque_minimo'].astype(int)]
    
    if df_compras.empty:
        st.success("✅ Estoque abastecido!")
    else:
        st.subheader("Itens Faltantes")
        texto_whats = f"*Lista Gran Turin ({datetime.now().strftime('%d/%m')})*\n\n"
        for _, r in df_compras.iterrows():
            necessario = int(r['estoque_minimo']) - int(r['quantidade_atual'])
            msg = f"• {r['produto']} (Faltam {necessario} un.)"
            st.warning(msg)
            texto_whats += msg + "\n"
        
        st.divider()
        link_wa = f"https://wa.me/?text={urllib.parse.quote(texto_whats)}"
        st.link_button("🚀 ENVIAR LISTA WHATSAPP", link_wa, use_container_width=True)

# --- ABA 3: GERENCIAR (Categorias Dinâmicas) ---
with tab3:
    st.subheader("Cadastrar Novo Item")
    
    # Busca categorias existentes para o Selectbox
    categorias_existentes = []
    if not df.empty and 'categoria' in df.columns:
        categorias_existentes = sorted(df['categoria'].unique().tolist())
    
    opcoes = ["-- Selecione --", "+ Nova Categoria"] + categorias_existentes
    
    with st.form("form_cadastro", clear_on_submit=True):
        escolha = st.selectbox("Categoria", options=opcoes)
        
        # Campo extra se for categoria nova
        nova_cat = ""
        if escolha == "+ Nova Categoria":
            nova_cat = st.text_input("Nome da Nova Categoria").upper()
            
        prod = st.text_input("Nome do Produto")
        min_est = st.number_input("Estoque Mínimo", value=5, min_value=0)
        
        btn_cadastrar = st.form_submit_button("CADASTRAR PRODUTO", use_container_width=True)
        
        if btn_cadastrar:
            cat_final = nova_cat if escolha == "+ Nova Categoria" else escolha
            
            if cat_final and cat_final != "-- Selecione --" and prod:
                supabase.table("estoque").insert({
                    "categoria": cat_final.strip().upper(),
                    "produto": prod.strip(),
                    "quantidade_atual": 0,
                    "estoque_minimo": min_est
                }).execute()
                st.success("Produto cadastrado!")
                st.rerun()
            else:
                st.error("Preencha todos os campos corretamente.")

    st.divider()
    # Lista de exclusão
    if not df.empty:
        with st.expander("🗑️ Excluir Produtos"):
            for _, row in df.iterrows():
                col_a, col_b = st.columns([4, 1])
                col_a.write(f"{row['categoria']} | {row['produto']}")
                if col_b.button("Excluir", key=f"del_{row['id']}"):
                    supabase.table("estoque").delete().eq("id", row['id']).execute()
                    st.rerun()
