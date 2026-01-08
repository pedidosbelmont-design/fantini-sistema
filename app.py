import streamlit as st
import pandas as pd
import os
import time
import base64

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(
    layout="wide", 
    page_title="Fantini App", 
    page_icon="📱",
    initial_sidebar_state="collapsed" # Começa fechado para focar no conteúdo
)

PASTA_IMAGENS = "static"
ARQUIVO_DB = "banco_produtos_dinamico.csv"
COLUNAS_FIXAS = ["codigo", "barras", "nome", "imagem", "fabricante"]
EMPRESAS = ["Vinagre Belmont", "Serve Sempre"]

LOGOS_FABRICANTES = {
    "Vinagre Belmont": "belmont.png",
    "Serve Sempre": "serve.png"
}

def get_img_as_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# --- CSS OTIMIZADO PARA DEDO (TOUCH) ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f5; }
    h1, h2, h3, p, div, span, label { color: #1c1e21 !important; }
    
    /* Remove margens inúteis do topo no celular */
    .block-container {
        padding-top: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }

    /* Estilo dos Botões de Filtro (Pills) */
    div[data-testid="stSegmentedControl"] button {
        font-size: 14px;
        padding: 5px 10px;
    }

    /* CARD DE PRODUTO OTIMIZADO */
    .produto-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 8px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .nome-produto {
        font-family: sans-serif; 
        font-size: 12px; 
        font-weight: 600;
        color: #333 !important; 
        height: 34px; 
        overflow: hidden;
        margin-top: 5px; 
        display: -webkit-box; 
        -webkit-line-clamp: 2; 
        -webkit-box-orient: vertical;
        line-height: 1.2;
    }
    
    .preco-destaque { 
        font-size: 16px; 
        font-weight: 800; 
        color: #2e7d32 !important; 
        margin: 4px 0; 
    }
    
    /* Botão Ver Detalhes (Largo para facilitar o clique) */
    .stButton button {
        width: 100%;
        border-radius: 6px;
        padding: 0.25rem 0.5rem;
        font-size: 14px;
    }

    /* Tags pequenas */
    .tag-tabela {
        background-color: #eee; color: #666 !important; font-size: 9px;
        padding: 2px 4px; border-radius: 4px; font-weight: bold; text-transform: uppercase;
    }
    
    .logo-fabrica-card {
        max-height: 20px;
        max-width: 50px;
        object-fit: contain;
    }
    
    /* Centraliza imagens */
    div[data-testid="stImage"] { display: flex; justify-content: center; }
    header {visibility: visible !important; background-color: transparent !important;}
    .stDecoration { display: none; }
    
    /* HACK CSS PARA 2 COLUNAS NO MOBILE */
    /* Força as colunas do Streamlit a terem 50% de largura em telas pequenas */
    @media (max-width: 640px) {
        div[data-testid="column"] {
            width: 50% !important;
            flex: 0 0 50% !important;
            min-width: 50% !important;
            padding: 0 0.2rem !important; /* Espaçamento pequeno entre cards */
        }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA ---
def inicializar():
    if not os.path.exists(PASTA_IMAGENS): os.makedirs(PASTA_IMAGENS)
    if not os.path.exists(ARQUIVO_DB):
        pd.DataFrame(columns=COLUNAS_FIXAS).to_csv(ARQUIVO_DB, index=False)

def carregar_dados(): 
    df = pd.read_csv(ARQUIVO_DB)
    if "fabricante" not in df.columns:
        df["fabricante"] = "Geral"; salvar_dados(df)
    return df

def salvar_dados(df): df.to_csv(ARQUIVO_DB, index=False)

def criar_categoria(nome):
    df = carregar_dados()
    if nome not in df.columns:
        df[nome] = 0.0; salvar_dados(df); return True, "Criado!"
    return False, "Existe."

def excluir_categoria(nome):
    df = carregar_dados()
    if nome in df.columns and nome not in COLUNAS_FIXAS:
        df = df.drop(columns=[nome]); salvar_dados(df); return True, "Removida."
    return False, "Erro."

def salvar_produto(codigo, barras, nome, fabricante, imagem_file, precos_dict, modo_edicao=False):
    df = carregar_dados()
    if not codigo:
        if modo_edicao: return False, "Erro ref."
        else: codigo = f"AUTO-{int(time.time())}"
    
    if not modo_edicao and codigo in df["codigo"].values: return False, "Cód existe!"

    nome_imagem = "sem_foto.png"
    if modo_edicao:
        idx = df[df["codigo"] == codigo].index
        if not idx.empty:
            nome_imagem = df.loc[idx[0], "imagem"]
            df = df.drop(idx)

    if imagem_file:
        nome_imagem = f"{codigo}_{imagem_file.name}"
        with open(os.path.join(PASTA_IMAGENS, nome_imagem), "wb") as f:
            f.write(imagem_file.getbuffer())

    novo_item = {"codigo": codigo, "barras": barras, "nome": nome, "fabricante": fabricante, "imagem": nome_imagem}
    novo_item.update(precos_dict)
    
    df = pd.concat([df, pd.DataFrame([novo_item])], ignore_index=True)
    df = df.fillna(0)
    salvar_dados(df)
    return True, "Salvo!"

def excluir_produto(codigo):
    df = carregar_dados()
    df = df[df["codigo"] != codigo]
    salvar_dados(df)

@st.dialog("Detalhes")
def mostrar_detalhes(row, img_path, colunas_precos):
    st.markdown(f"### {row['nome']}")
    if os.path.exists(img_path): st.image(img_path, use_container_width=True)
    
    st.write("")
    c1, c2 = st.columns(2)
    with c1: st.caption(f"Fab: {row['fabricante']}")
    with c2: 
        if row['barras'] and str(row['barras']) != "nan": st.caption(f"EAN: {row['barras']}")
    
    st.divider()
    html = "| Tabela | Preço |\n| :--- | :--- |\n"
    for col in colunas_precos:
        html += f"| {col} | **R$ {row[col]:,.2f}** |\n"
    st.markdown(html)

# --- 3. APP ---
inicializar()
if "edit_codigo" not in st.session_state: st.session_state["edit_codigo"] = None

df = carregar_dados()
colunas_de_preco = [c for c in df.columns if c not in COLUNAS_FIXAS]

# --- CABEÇALHO DO APP (SEMPRE VISÍVEL) ---
# Aqui ficam os filtros principais, fora da sidebar para acesso rápido
c_logo, c_titulo = st.columns([1, 4])
with c_logo:
    # Pequeno logo no topo
    if os.path.exists(os.path.join(PASTA_IMAGENS, "logo.png")):
        st.image(os.path.join(PASTA_IMAGENS, "logo.png"), width=50)
with c_titulo:
    st.markdown("**Fantini App**")

# FILTROS PRINCIPAIS (TIPO SHOPEE)
st.write("") # Espaço
filtro_fabrica = st.pills("🏭 Fabricante", ["Todos"] + EMPRESAS, default="Todos")

tabela_ativa = None
if colunas_de_preco:
    tabela_ativa = st.pills("💲 Tabela", colunas_de_preco, default=colunas_de_preco[0] if colunas_de_preco else None)
else:
    st.warning("Cadastre tabelas na aba Configurações.")

st.divider()

# TABS PRINCIPAIS
tab_vitrine, tab_novo, tab_config = st.tabs(["💎 Vitrine", "📝 Cadastro", "⚙️ Ajustes"])

# ABA VITRINE
with tab_vitrine:
    df_vitrine = df.copy()
    if filtro_fabrica != "Todos":
        df_vitrine = df_vitrine[df_vitrine["fabricante"] == filtro_fabrica]

    if df_vitrine.empty:
        st.info("Nenhum produto encontrado.")
    elif not tabela_ativa:
        st.info("Selecione uma tabela.")
    else:
        # GRID RESPONSIVO AUTOMÁTICO
        # No PC serão 6 colunas. No Celular, o CSS lá em cima força virar 2 colunas.
        colunas = st.columns(6)
        
        for idx, row in df_vitrine.iterrows():
            # O truque do módulo % garante que distribua nas colunas
            with colunas[idx % 6]:
                img_path = os.path.join(PASTA_IMAGENS, str(row["imagem"]))
                preco_show = row[tabela_ativa] if tabela_ativa else 0.0
                
                # Logo da fábrica pequena
                nome_arq_logo = LOGOS_FABRICANTES.get(row['fabricante'])
                html_logo = ""
                if nome_arq_logo:
                    path_full_logo = os.path.join(PASTA_IMAGENS, nome_arq_logo)
                    b64_logo = get_img_as_base64(path_full_logo)
                    if b64_logo:
                        html_logo = f"<img src='data:image/png;base64,{b64_logo}' class='logo-fabrica-card'>"
                
                # Container do Card
                with st.container():
                    st.markdown(f"""
                    <div class="produto-card">
                        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;'>
                             {html_logo if html_logo else "<span class='tag-tabela'>FAB</span>"}
                             <span class='tag-tabela'>Ref {row['codigo']}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if os.path.exists(img_path): st.image(img_path, use_container_width=True) 
                    else: st.text("S/ Foto")

                    st.markdown(f"""
                        <div class='nome-produto'>{row['nome']}</div>
                        <div class='preco-destaque'>R$ {preco_show:,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Ver", key=f"btn_{row['codigo']}", use_container_width=True):
                        mostrar_detalhes(row, img_path, colunas_de_preco)
                    
                    st.write("") # Espaço entre linhas no mobile

# ABA GERENCIAR
with tab_novo:
    col_cad, col_search = st.columns([1.5, 1])
    with col_search:
        st.markdown("##### 🔎 Buscar")
        df_view = carregar_dados()
        if not df_view.empty:
            df_view['codigo'] = df_view['codigo'].astype(str)
            lista_produtos = df_view["codigo"] + " | " + df_view["nome"]
            escolha = st.selectbox("Editar:", ["Selecione..."] + list(lista_produtos))
            if st.button("Carregar", type="primary", use_container_width=True):
                if escolha != "Selecione...":
                    st.session_state["edit_codigo"] = escolha.split(" | ")[0]; st.rerun()
    
    with col_cad:
        codigo_em_edicao = st.session_state["edit_codigo"]
        dados_edicao = None
        if codigo_em_edicao:
            df['codigo'] = df['codigo'].astype(str)
            filtro = df[df["codigo"] == str(codigo_em_edicao)]
            if not filtro.empty: dados_edicao = filtro.iloc[0]
        
        st.markdown(f"##### ✏️ {dados_edicao['nome']}" if dados_edicao else "##### ➕ Novo Produto")
        if dados_edicao and st.button("Cancelar Edição", use_container_width=True): 
            st.session_state["edit_codigo"] = None; st.rerun()

        with st.container(border=True):
            cod_val = dados_edicao["codigo"] if dados_edicao else ""
            barras_val = dados_edicao["barras"] if dados_edicao else ""
            nome_val = dados_edicao["nome"] if dados_edicao else ""
            fab_index = 0
            if dados_edicao and dados_edicao["fabricante"] in EMPRESAS:
                fab_index = EMPRESAS.index(dados_edicao["fabricante"])
            if str(cod_val).startswith("AUTO-"): cod_val = ""

            fabricante = st.selectbox("Fabricante *", EMPRESAS, index=fab_index)
            c1, c2 = st.columns(2)
            codigo = c1.text_input("Cód Interno", value=cod_val, disabled=(dados_edicao is not None))
            barras = c2.text_input("EAN/Barras", value=barras_val)
            nome = st.text_input("Nome *", value=nome_val)
            f_img = st.file_uploader("Imagem", type=['jpg','png'])
            
            if dados_edicao and not f_img: st.caption(f"Foto atual: {dados_edicao['imagem']}")
            st.divider()
            
            if colunas_de_preco:
                st.write("💰 **Preços**")
                precos_input = {}
                for col in colunas_de_preco:
                    val = float(dados_edicao[col]) if dados_edicao else 0.0
                    precos_input[col] = st.number_input(f"{col} (R$)", value=val)
                
                b1, b2 = st.columns(2)
                lbl = "Atualizar" if dados_edicao else "Salvar"
                if b1.button(f"💾 {lbl}", type="primary", use_container_width=True):
                    cod_final = codigo
                    if dados_edicao and not codigo: cod_final = dados_edicao["codigo"]
                    if nome and fabricante:
                        ok, m = salvar_produto(cod_final, barras, nome, fabricante, f_img, precos_input, modo_edicao=(dados_edicao is not None))
                        if ok: st.success(m); st.session_state["edit_codigo"] = None; st.rerun()
                        else: st.error(m)
                    else: st.warning("Nome/Fabricante obrigatórios")
                
                if dados_edicao and b2.button("🗑️ Excluir", use_container_width=True):
                    excluir_produto(dados_edicao["codigo"]); st.session_state["edit_codigo"] = None; st.success("Excluído"); st.rerun()
            else: st.warning("Crie tabelas primeiro.")

# ABA CONFIG
with tab_config:
    st.markdown("##### Tabelas")
    c1, c2 = st.columns(2)
    with c1:
        new_cat = st.text_input("Nova Tabela")
        if st.button("Criar", use_container_width=True):
            if new_cat:
                ok, m = criar_categoria(new_cat)
                if ok: st.success(m); time.sleep(0.5); st.rerun()
    with c2:
        if colunas_de_preco:
            del_cat = st.selectbox("Apagar:", colunas_de_preco)
            if st.button("Apagar", use_container_width=True):
                ok, m = excluir_categoria(del_cat)
                if ok: st.warning(m); time.sleep(0.5); st.rerun()