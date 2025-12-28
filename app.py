import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÃO (Mantenha sua URL e KEY aqui) ---
URL = "https://vfbzvzajgbllbbnfrqbh.supabase.co"
KEY = "SUA_KEY_AQUI" 

try:
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error(f"Erro de Conexão: {e}")

st.set_page_config(page_title="Gestão de Estoque Gran Turin", layout="centered", page_icon="🍊")

def carregar_dados():
    try:
        res = supabase.table("estoque").select("*").execute()
        if res.data:
            df_res = pd.DataFrame(res.data)
            df_res.columns = [c.lower() for c in df_res.columns]
            return df_res.sort_values(['categoria', 'produto'])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- INTERFACE ---
st.title("🍊 Gestão de Estoque Gran Turin")
df = carregar_dados()

tab1, tab2, tab3 = st.tabs(["📦 ESTOQUE", "🛒 COMPRAS", "⚙️ GERENCIAR"])

# ... (Abas 1 e 2 permanecem iguais) ...
with tab1:
    if df.empty: st.info("Cadastre produtos na aba Gerenciar.")
    else:
        for cat in sorted(df['categoria'].unique()):
            with st.expander(f"📁 {cat.upper()}", expanded=True):
                itens = df[df['categoria'] == cat]
                for _, row in itens.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                    c1.markdown(f"**{row['produto']}**")
                    n_at = c2.number_input("Tem", value=int(row['quantidade_atual']), key=f"at_{row['id']}")
                    n_min = c3.number_input("Mín", value=int(row['estoque_minimo']), key=f"min_{row['id']}")
                    if c4.button("💾", key=f"btn_{row['id']}"):
                        supabase.table("estoque").update({"quantidade_atual": n_at, "estoque_minimo": n_min}).eq("id", row['id']).execute()
                        st.rerun()
                    st.divider()

with tab2:
    if not df.empty:
        df_compras = df[df['quantidade_atual'].astype(int) < df['estoque_minimo'].astype(int)]
        if not df_compras.empty:
            texto_whats = f"*Lista Gran Turin ({datetime.now().strftime('%d/%m')})*\n\n"
            for _, r in df_compras.iterrows():
                msg = f"• {r['produto']} (Faltam {int(r['estoque_minimo']) - int(r['quantidade_atual'])} un.)"
                st.warning(msg)
                texto_whats += msg + "\n"
            st.link_button("🚀 ENVIAR WHATSAPP", f"https://wa.me/?text={urllib.parse.quote(texto_whats)}", use_container_width=True)
        else:
            st.success("Estoque em dia!")

# --- ABA 3: GERENCIAR (CORRIGIDA) ---
with tab3:
    st.subheader("Cadastrar Novo Item")
    
    # 1. Pegamos as categorias fora do form para o selectbox ser responsivo
    categorias_existentes = sorted(df['categoria'].unique().tolist()) if not df.empty else []
    opcoes_cat = ["-- Selecione --", "+ Nova Categoria"] + categorias_existentes
    
    # Selectbox FORA do form para atualizar a tela na hora
    escolha = st.selectbox("Selecione a Categoria", options=opcoes_cat)
    
    categoria_final = ""
    
    # Se escolher nova, o campo aparece instantaneamente
    if escolha == "+ Nova Categoria":
        categoria_final = st.text_input("Nome da Nova Categoria:").strip().upper()
    else:
        categoria_final = escolha

    # 2. Form apenas para os dados do produto
    with st.form("cadastro_produto", clear_on_submit=True):
        col_p, col_m = st.columns([3, 1])
        nome_prod = col_p.text_input("Nome do Produto")
        min_est = col_m.number_input("Mínimo", value=5, min_value=0)
        
        btn_salvar = st.form_submit_button("CADASTRAR PRODUTO", use_container_width=True)
        
        if btn_salvar:
            if categoria_final and categoria_final != "-- Selecione --" and nome_prod:
                try:
                    supabase.table("estoque").insert({
                        "categoria": categoria_final,
                        "produto": nome_prod.strip(),
                        "quantidade_atual": 0,
                        "estoque_minimo": min_est
                    }).execute()
                    st.success(f"Sucesso: {nome_prod} adicionado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha todos os campos antes de salvar.")

    st.divider()
    # Lista de exclusão simplificada
    if not df.empty:
        with st.expander("🗑️ Remover Produtos"):
            for _, row in df.iterrows():
                ca, cb = st.columns([4, 1])
                ca.write(f"**{row['categoria']}** | {row['produto']}")
                if cb.button("Excluir", key=f"del_{row['id']}"):
                    supabase.table("estoque").delete().eq("id", row['id']).execute()
                    st.rerun()
