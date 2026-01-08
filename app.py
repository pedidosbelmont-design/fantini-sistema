import streamlit as st
import pandas as pd
import os
import time
import base64

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(
    layout="wide", 
    page_title="Fantini Dynamic System", 
    page_icon="♾️",
    initial_sidebar_state="expanded"
)

PASTA_IMAGENS = "static"
ARQUIVO_DB = "banco_produtos_dinamico.csv"
COLUNAS_FIXAS = ["codigo", "barras", "nome", "imagem", "fabricante"]
EMPRESAS = ["Vinagre Belmont", "Serve Sempre"]

# --- MAPA DE LOGOS DAS FÁBRICAS ---
# Aqui associamos o Nome da Fábrica ao arquivo na pasta static
LOGOS_FABRICANTES = {
    "Vinagre Belmont": "belmont.png",
    "Serve Sempre": "serve.png"
}

# --- FUNÇÃO AUXILIAR PARA IMAGEM NO HTML ---
def get_img_as_base64(file_path):
    """Transforma a imagem em código para poder usar dentro do HTML/CSS"""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# --- CSS BLINDADO ---
st.markdown("""
<style>
    .stApp { background-color: #f4f7f6; }
    h1, h2, h3, p, div, span, label { color: #2c3e50 !important; }
    
    /* Inputs */
    input[type="text"], input[type="number"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #ccc !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Card Style */
    .produto-card {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        height: 100%;
        position: relative;
    }
    .produto-card:hover { transform: translateY(-3px); border-color: #2980b9; }
    
    .nome-produto {
        font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 700;
        color: #34495e !important; height: 38px; overflow: hidden;
        margin-top: 5px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    }
    .preco-destaque { font-size: 20px; font-weight: 800; color: #27ae60 !important; margin: 5px 0; }
    
    /* Tags */
    .tag-tabela {
        background-color: #ecf0f1; color: #7f8c8d !important; font-size: 10px;
        padding: 4px 8px; border-radius: 4px; font-weight: bold; text-transform: uppercase;
    }
    .tag-codigo {
        font-size: 10px; color: #bdc3c7 !important; margin-bottom: 2px; display: block;
    }
    
    /* Logo da Fábrica no Card */
    .logo-fabrica-card {
        max-height: 25px; /* Altura fixa pequena */
        max-width: 80px;
        object-fit: contain;
    }
    
    [data-testid="stSidebar"] img { display: block; margin-left: auto; margin-right: auto; margin-bottom: 20px; }
    div[data-testid="stImage"] { display: flex; justify-content: center; }
    header {visibility: visible !important; background-color: rgba(0,0,0,0) !important;}
    .stDecoration { display: none; }
    .block-container {padding-top: 3rem;}
</style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE DADOS ---
def inicializar():
    if not os.path.exists(PASTA_IMAGENS): os.makedirs(PASTA_IMAGENS)
    if not os.path.exists(ARQUIVO_DB):
        pd.DataFrame(columns=COLUNAS_FIXAS).to_csv(ARQUIVO_DB, index=False)

def carregar_dados(): 
    df = pd.read_csv(ARQUIVO_DB)
    if "fabricante" not in df.columns:
        df["fabricante"] = "Geral"
        salvar_dados(df)
    return df

def salvar_dados(df): df.to_csv(ARQUIVO_DB, index=False)

def criar_categoria(nome):
    df = carregar_dados()
    if nome not in df.columns:
        df[nome] = 0.0
        salvar_dados(df)
        return True, "Categoria criada!"
    return False, "Categoria já existe."

def excluir_categoria(nome):
    df = carregar_dados()
    if nome in df.columns and nome not in COLUNAS_FIXAS:
        df = df.drop(columns=[nome])
        salvar_dados(df)
        return True, "Removida."
    return False, "Erro."

def salvar_produto(codigo, barras, nome, fabricante, imagem_file, precos_dict, modo_edicao=False):
    df = carregar_dados()
    if not codigo:
        if modo_edicao: return False, "Erro de referência."
        else: codigo = f"AUTO-{int(time.time())}"
    
    if not modo_edicao and codigo in df["codigo"].values: return False, "⚠️ Código já existe!"

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
    return True, "Salvo com sucesso!"

def excluir_produto(codigo):
    df = carregar_dados()
    df = df[df["codigo"] != codigo]
    salvar_dados(df)

@st.dialog("Ficha do Produto")
def mostrar_detalhes(row, img_path, colunas_precos):
    c1, c2 = st.columns([1, 1.5])
    with c1:
        if os.path.exists(img_path): st.image(img_path, use_container_width=True)
        else: st.text("Sem foto")
        
        # Mostra logo da fabrica no detalhe também
        arq_logo = LOGOS_FABRICANTES.get(row['fabricante'])
        if arq_logo:
            caminho_logo = os.path.join(PASTA_IMAGENS, arq_logo)
            if os.path.exists(caminho_logo):
                st.image(caminho_logo, width=100)
            else:
                st.caption(f"Fab: {row['fabricante']}")
        else:
            st.caption(f"Fab: {row['fabricante']}")

        if row['barras'] and str(row['barras']) != "nan":
            st.markdown(f"**EAN:** `{row['barras']}`")

    with c2:
        st.subheader(row['nome'])
        st.divider()
        st.markdown("📋 **Tabela de Preços:**")
        html = "| Categoria | Preço |\n| :--- | :--- |\n"
        for col in colunas_precos:
            html += f"| {col} | **R$ {row[col]:,.2f}** |\n"
        st.markdown(html)

# --- 3. APP PRINCIPAL ---
inicializar()

if "edit_codigo" not in st.session_state:
    st.session_state["edit_codigo"] = None

df = carregar_dados()
colunas_de_preco = [c for c in df.columns if c not in COLUNAS_FIXAS]

# SIDEBAR
with st.sidebar:
    # Busca Logo da Fantini
    caminhos_possiveis = [os.path.join(PASTA_IMAGENS, x) for x in ["logo.png", "logo.jpg", "Logo.png"]]
    logo_encontrado = next((c for c in caminhos_possiveis if os.path.exists(c)), None)
    
    if logo_encontrado: st.image(logo_encontrado, use_container_width=True)
    else: st.header("FANTINI")
    
    st.divider()
    st.header("🏭 Fabricante")
    filtro_fabrica = st.radio("Filtrar Vitrine:", ["Todos"] + EMPRESAS)
    st.divider()
    
    tabela_ativa = None
    if colunas_de_preco:
        st.header("💲 Tabela de Preço")
        tabela_ativa = st.radio("Visualizar:", colunas_de_preco)
    else: st.warning("Crie tabelas na aba Configurações.")

# TABS
st.title("Fantini Dynamic OS")
tab_vitrine, tab_novo, tab_config = st.tabs(["💎 Vitrine", "📝 Gerenciar Produtos", "⚙️ Configurações"])

# ABA VITRINE
with tab_vitrine:
    df_vitrine = df.copy()
    if filtro_fabrica != "Todos":
        df_vitrine = df_vitrine[df_vitrine["fabricante"] == filtro_fabrica]

    if df_vitrine.empty:
        if df.empty: st.info("Cadastre produtos.")
        else: st.warning(f"Sem produtos de {filtro_fabrica}.")
    elif not colunas_de_preco:
        st.info("Cadastre tabelas.")
    else:
        st.markdown(f"Mostrando **{filtro_fabrica}** na tabela **{tabela_ativa}**")
        colunas = st.columns(6) 
        
        for idx, row in df_vitrine.iterrows():
            with colunas[idx % 6]:
                img_path = os.path.join(PASTA_IMAGENS, str(row["imagem"]))
                preco_show = row[tabela_ativa] if tabela_ativa else 0.0
                
                # --- LÓGICA PARA RENDERIZAR LOGO PEQUENA ---
                nome_arq_logo = LOGOS_FABRICANTES.get(row['fabricante'])
                html_logo = f"<span class='tag-tabela'>{row['fabricante'][:10]}</span>" # Fallback texto
                
                if nome_arq_logo:
                    path_full_logo = os.path.join(PASTA_IMAGENS, nome_arq_logo)
                    b64_logo = get_img_as_base64(path_full_logo)
                    if b64_logo:
                        # Se achou a imagem, cria a tag HTML img
                        html_logo = f"<img src='data:image/png;base64,{b64_logo}' class='logo-fabrica-card'>"
                
                # Código (esconde se for auto)
                display_cod = f"#{row['codigo']}" if not str(row['codigo']).startswith("AUTO-") else ""

                with st.container(border=True):
                    # Cabeçalho do Card: Logo Fabrica (esq) | Tabela (dir)
                    st.markdown(f"""
                        <div style='display:flex; justify-content:space-between; align-items:center; height:30px;'>
                             {html_logo}
                             <span class='tag-tabela'>{tabela_ativa}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if display_cod:
                        st.markdown(f"<span class='tag-codigo'>{display_cod}</span>", unsafe_allow_html=True)
                    
                    if os.path.exists(img_path): st.image(img_path, width=100) 
                    else: st.text("S/ Imagem")

                    st.markdown(f"""
                        <div class='nome-produto'>{row['nome']}</div>
                        <div class='preco-destaque'>R$ {preco_show:,.2f}</div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Ver Detalhes", key=f"btn_{row['codigo']}"):
                        mostrar_detalhes(row, img_path, colunas_de_preco)



# ABA CONFIG
# ABA CONFIG (CORRIGIDA)
with tab_config:
    st.header("Gerenciar Tabelas")
    c1, c2 = st.columns(2)
    # ABA GERENCIAR (CORRIGIDA)
with tab_novo:
    col_cad, col_search = st.columns([1.5, 1])
    
    # --- COLUNA DE BUSCA ---
    with col_search:
        st.subheader("🔎 Buscar")
        df_view = carregar_dados()
        if not df_view.empty:
            df_view['codigo'] = df_view['codigo'].astype(str)
            lista_produtos = df_view["codigo"] + " | " + df_view["nome"]
            escolha = st.selectbox("Editar:", ["Selecione..."] + list(lista_produtos))
            if st.button("Carregar Edição", type="primary"):
                if escolha != "Selecione...":
                    st.session_state["edit_codigo"] = escolha.split(" | ")[0]
                    st.rerun()
    
    # --- COLUNA DE CADASTRO ---
    with col_cad:
        codigo_em_edicao = st.session_state["edit_codigo"]
        dados_edicao = None
        
        if codigo_em_edicao:
            df['codigo'] = df['codigo'].astype(str)
            filtro = df[df["codigo"] == str(codigo_em_edicao)]
            if not filtro.empty: 
                dados_edicao = filtro.iloc[0]
        
        # Cabeçalho dinâmico
        if dados_edicao is not None:
            st.subheader(f"✏️ Editando: {dados_edicao['nome']}")
            if st.button("❌ Cancelar"): 
                st.session_state["edit_codigo"] = None
                st.rerun()
        else: 
            st.subheader("➕ Novo Produto")

        with st.container(border=True):
            # Carregar valores (com proteção None)
            cod_val = dados_edicao["codigo"] if dados_edicao is not None else ""
            barras_val = dados_edicao["barras"] if dados_edicao is not None else ""
            nome_val = dados_edicao["nome"] if dados_edicao is not None else ""
            
            # Index do Fabricante
            fab_index = 0
            if dados_edicao is not None and dados_edicao["fabricante"] in EMPRESAS:
                fab_index = EMPRESAS.index(dados_edicao["fabricante"])

            # Limpa visualmente se for código automático
            if str(cod_val).startswith("AUTO-"): 
                cod_val = ""

            # --- CAMPOS DO FORMULÁRIO ---
            fabricante = st.selectbox("Fabricante *", EMPRESAS, index=fab_index)
            
            c_cod, c_barras = st.columns(2)
            codigo = c_cod.text_input("Código Interno (Opcional)", value=cod_val, disabled=(dados_edicao is not None))
            barras = c_barras.text_input("Cód. Barras (Opcional)", value=barras_val)
            
            nome = st.text_input("Nome do Produto *", value=nome_val)
            f_img = st.file_uploader("Imagem", type=['jpg','png'])
            
            if dados_edicao is not None and not f_img: 
                st.caption(f"Imagem atual: {dados_edicao['imagem']}")
            
            st.divider()
            
            # --- TABELAS DE PREÇO ---
            if colunas_de_preco:
                st.write("💰 **Preços:**")
                precos_input = {}
                for col in colunas_de_preco:
                    # Pega valor se existir, senão 0.0
                    val = float(dados_edicao[col]) if dados_edicao is not None else 0.0
                    precos_input[col] = st.number_input(f"{col} (R$)", value=val)
                
                c_btn1, c_btn2 = st.columns(2)
                
                # --- AQUI ESTAVA O ERRO (CORRIGIDO) ---
                # Usamos 'is not None' para evitar ambiguidade do Pandas
                label_botao = "Atualizar" if dados_edicao is not None else "Cadastrar"
                
                if c_btn1.button(f"💾 {label_botao}", type="primary"):
                    cod_final = codigo
                    # Se for edição e o campo código estiver vazio (era AUTO-), recupera o original
                    if dados_edicao is not None and not codigo: 
                        cod_final = dados_edicao["codigo"]

                    if nome and fabricante:
                        ok, msg = salvar_produto(cod_final, barras, nome, fabricante, f_img, precos_input, modo_edicao=(dados_edicao is not None))
                        if ok: 
                            st.success(msg)
                            st.session_state["edit_codigo"] = None
                            st.rerun()
                        else: 
                            st.error(msg)
                    else: 
                        st.warning("Nome e Fabricante obrigatórios.")
                
                # Botão Excluir (Só aparece se estiver editando)
                if dados_edicao is not None:
                    if c_btn2.button("🗑️ Excluir"):
                        excluir_produto(dados_edicao["codigo"])
                        st.session_state["edit_codigo"] = None
                        st.success("Excluído!")
                        st.rerun()
            else: 
                st.warning("Crie tabelas primeiro.")
    # --- COLUNA 1: CRIAR ---
    with c1:
        new_cat = st.text_input("Nova Tabela")
        if st.button("Criar"):
            if new_cat:
                ok, m = criar_categoria(new_cat)
                if ok: 
                    st.success(m)
                    time.sleep(0.5) # Pausa rápida para ver a mensagem
                    st.rerun()
            else:
                st.warning("Digite um nome para a tabela.")

    # --- COLUNA 2: APAGAR ---
    with c2:
        if colunas_de_preco:
            del_cat = st.selectbox("Apagar Tabela:", colunas_de_preco)
            if st.button("Apagar"):
                ok, m = excluir_categoria(del_cat)
                if ok: 
                    st.warning(m)
                    time.sleep(0.5)
                    st.rerun()
        else:
            st.info("Nenhuma tabela para apagar.")