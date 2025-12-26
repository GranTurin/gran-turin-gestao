import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÃO ---
URL = "https://vfbzvzajgbllbbnfrqbh.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZmYnp2emFqZ2JsbGJibmZycWJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY2OTk2MjIsImV4cCI6MjA4MjI3NTYyMn0.b3Nk15L9Ez0i50kMpaOkBQEfOSY8GIhNYNmk9rycA9c"

supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Gran Turin - Gestão", layout="centered")

def carregar_dados():
    try:
        res = supabase.table("estoque").select("*").execute()
        if res.data:
            df_res = pd.DataFrame(res.data)
            df_res.columns = [c.lower() for c in df_res.columns] # Normaliza colunas
            return df_res
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return pd.DataFrame()

st.title("🍊 Gran Turin - Gestão")

df = carregar_dados()

# --- VERIFICAÇÃO DE SEGURANÇA ---
# Se o banco estiver vazio ou as colunas não existirem, o código não trava
colunas_necessarias = ['categoria', 'produto', 'quantidade_atual', 'estoque_minimo']
banco_pronto = all(col in df.columns for col in colunas_necessarias) if not df.empty else False

if not banco_pronto:
    st.warning("⚠️ O sistema ainda não possui produtos cadastrados ou a tabela 'estoque' precisa ser configurada.")
    st.info("Use o formulário abaixo para adicionar o primeiro item e ativar o sistema.")
    
    with st.form("primeiro_cadastro"):
        st.subheader("Cadastrar Primeiro Produto")
        c = st.text_input("Categoria (ex: Bebidas)")
        p = st.text_input("Produto (ex: Coca-Cola)")
        m = st.number_input("Estoque Mínimo", value=5)
        if st.form_submit_button("Salvar e Iniciar"):
            if c and p:
                supabase.table("estoque").insert({
                    "categoria": c, 
                    "produto": p, 
                    "quantidade_atual": 0, 
                    "estoque_minimo": m
                }).execute()
                st.success("Primeiro item salvo! Recarregando...")
                st.rerun()
            else:
                st.error("Preencha todos os campos.")
else:
    # --- SE O BANCO TIVER DADOS, MOSTRA AS ABAS ---
    tab1, tab2, tab3 = st.tabs(["📦 Estoque", "🛒 Compras", "⚙️ Gerenciar"])

    with tab1:
        # Pega as categorias únicas com segurança
        categorias = df['categoria'].unique()
        for cat in categorias:
            with st.expander(f"📁 {cat}", expanded=True):
                itens = df[df['categoria'] == cat]
                for _, row in itens.iterrows():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    col1.write(f"**{row['produto']}**")
                    
                    n_at = col2.number_input("Tem", value=int(row['quantidade_atual']), key=f"at_{row['id']}")
                    n_min = col3.number_input("Mín", value=int(row['estoque_minimo']), key=f"min_{row['id']}")
                    
                    if col4.button("💾", key=f"btn_{row['id']}"):
                        supabase.table("estoque").update({
                            "quantidade_atual": n_at, 
                            "estoque_minimo": n_min
                        }).eq("id", row['id']).execute()
                        st.success(f"{row['produto']} salvo!")
                        st.rerun()

    with tab2:
        faltantes = df[df['quantidade_atual'] < df['estoque_minimo']]
        if faltantes.empty:
            st.success("✅ Tudo em dia!")
        else:
            txt_whats = f"*Lista Gran Turin - {datetime.now().strftime('%d/%m')}*\n\n"
            for _, r in faltantes.iterrows():
                dif = r['estoque_minimo'] - r['quantidade_atual']
                msg = f"• {r['produto']} (Faltam {dif})"
                st.error(msg)
                txt_whats += msg + "\n"
            
            st.link_button("🚀 Enviar WhatsApp", f"https://wa.me/?text={urllib.parse.quote(txt_whats)}")

    with tab3:
        st.subheader("Adicionar Novo")
        with st.form("add_more"):
            new_c = st.text_input("Categoria")
            new_p = st.text_input("Produto")
            new_m = st.number_input("Mínimo", value=5)
            if st.form_submit_button("Cadastrar"):
                supabase.table("estoque").insert({"categoria": new_c, "produto": new_p, "quantidade_atual": 0, "estoque_minimo": new_m}).execute()
                st.rerun()
        
        st.divider()
        st.subheader("Excluir")
        for _, row in df.iterrows():
            c1, c2 = st.columns([4, 1])
            c1.write(f"{row['categoria']} | {row['produto']}")
            if c2.button("🗑️", key=f"del_{row['id']}"):
                supabase.table("estoque").delete().eq("id", row['id']).execute()
                st.rerun()
