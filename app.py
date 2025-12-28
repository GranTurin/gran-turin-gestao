import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÃO ---
URL = "https://vfbzvzajgbllbbnfrqbh.supabase.co"
KEY = "SUA_CHAVE_AQUI" # Lembre-se de usar st.secrets em produção

try:
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error(f"Erro de Conexão: {e}")

# Alteração de Nome conforme solicitado
st.set_page_config(page_title="Gestão de Estoque Gran Turin", layout="centered", page_icon="🍊")

# --- FUNÇÕES ---
def carregar_dados():
    try:
        res = supabase.table("estoque").select("*").execute()
        if res.data:
            df_res = pd.DataFrame(res.data)
            df_res.columns = [c.lower() for c in df_res.columns]
            return df_res.sort_values(['categoria', 'produto'])
        return pd.DataFrame()
    except Exception as e:
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
            with st.expander(f"📁 {cat.upper()}", expanded=True):
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
    df_compras = df[df['quantidade_atual'] < df['estoque_minimo']]
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

# --- ABA 3: GERENCIAR (Com melhorias de categorias) ---
with tab3:
    st.subheader("Cadastrar Novo Item")
    
    # Lógica para categorias inteligentes
    if not df.empty:
        lista_categorias = sorted(df['categoria'].unique().tolist())
    else:
        lista_categorias = []
    
    opcoes_cat = ["Selecione uma categoria...", "+ Nova Categoria"] + lista_categorias
    
    with st.form("novo_item_form", clear_on_submit=True):
        cat_selecionada = st.selectbox("Categoria", options=opcoes_cat)
        
        # Se escolher "Nova Categoria", aparece campo de texto
        nova_cat_input = ""
        if cat_selecionada == "+ Nova Categoria":
            nova_cat_input = st.text_input("Digite o nome da nova categoria")
        
        col_prod, col_min = st.columns([3, 1])
        new_prod = col_prod.text_input("Nome do Produto")
        new_min = col_min.number_input("Mínimo", value=5, min_value=0)
        
        enviar = st.form_submit_button("ADICIONAR AO SISTEMA", use_container_width=True)
        
        if enviar:
            # Define qual categoria usar
            categoria_final = nova_cat_input if cat_selecionada == "+ Nova Categoria" else cat_selecionada
            
            if categoria_final and categoria_final != "Selecione uma categoria..." and new_prod:
                try:
                    supabase.table("estoque").insert({
                        "categoria": categoria_final.strip().upper(),
                        "produto": new_prod.strip(),
                        "quantidade_atual": 0,
                        "estoque_minimo": new_min
                    }).execute()
                    st.success(f"'{new_prod}' adicionado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.warning("Por favor, preencha a Categoria e o Nome do Produto.")

    st.divider()
    if not df.empty:
        st.subheader("Remover Itens")
        with st.expander("Visualizar lista para exclusão"):
            for _, row in df.iterrows():
                ca, cb = st.columns([4, 1])
                ca.write(f"**{row['categoria']}** | {row['produto']}")
                if cb.button("🗑️", key=f"del_{row['id']}"):
                    supabase.table("estoque").delete().eq("id", row['id']).execute()
                    st.rerun()
