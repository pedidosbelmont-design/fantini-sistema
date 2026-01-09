import streamlit as st
import pandas as pd
import os
import time
import base64
from datetime import datetime

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(
    layout="wide", 
    page_title="Fantini Tabela", 
    page_icon="📄",
    initial_sidebar_state="expanded"
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

# --- CSS PARA IMPRESSÃO E TABELA ---
st.markdown("""
<style>
    .stApp { background-color: #f5f5f5; }
    h1, h2, h3, p, div, span, label { color: #000 !important; }

    /* Estilo da Folha de Papel (Tabela Gerada) */
    .folha-tabela {
        background-color: white;
        padding: 30px;
        border: 1px solid #ddd;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        margin-top: 20px;
    }

    /* Tabela HTML Bonita */
    .tabela-clean {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
    }
    .tabela-clean th {
        background-color: #2c3e50;
        color: white !important;
        padding: 10px;
        text-align: left;
    }
    .tabela-clean td {
        border-bottom: 1px solid #ddd;
        padding: 8px;
        color: #333 !important;
    }
    .tabela-clean tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    
    /* Imagem na tabela */
    .thumb-tabela {
        width: 40px;
        height: 40px;
        object-fit: contain;
    }

    /* Cabeçalho da Folha */
    .header-folha {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #2c3e50;
        padding-bottom: 15px;
        margin-bottom: 20px;
    }

    /* Ocultar elementos do Streamlit na hora de imprimir (Ctrl+P) */
    @media print {
        [data-testid="stSidebar"], 
        [data-testid="stHeader"], 
        .no-print {
            display: none !important;
        }
        .folha-tabela {
            box-shadow: none;
            border: none;
            margin: 0;
            padding: 0;
        }
        .block-container {
            padding: 0 !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. FUNÇÕES ---
def inicializar():
    if not os.path.exists(PASTA_IMAGENS): os.makedirs(PASTA_IMAGENS)
    if not os.path.exists(ARQUIVO_DB):
        pd.DataFrame(columns=COLUNAS_FIXAS).to_csv(ARQUIVO_DB, index=False)

def carregar_dados(): 
    df = pd.read_csv(ARQUIVO_DB)
    if "fabricante" not in df.columns: df["fabricante"] = "Geral"; salvar_dados(df)
    return df

def salvar_dados(df): df.to_csv(ARQUIVO_DB, index=False)

def salvar_produto(codigo, barras, nome, fabricante, imagem_file, precos_dict, modo_edicao=False):
    df = carregar_dados()
    if not codigo: codigo = f"AUTO-{int(time.time())}"
    
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

def criar_categoria(nome):
    df = carregar_dados()
    if nome not in df.columns: df[nome] = 0.0; salvar_dados(df); return True, "Criado!"
    return False, "Existe."

def excluir_categoria(nome):
    df = carregar_dados()
    if nome in df.columns and nome not in COLUNAS_FIXAS: df = df.drop(columns=[nome]); salvar_dados(df); return True, "Removida."
    return False, "Erro."

# --- 3. APP ---
inicializar()
if "edit_codigo" not in st.session_state: st.session_state["edit_codigo"] = None

df = carregar_dados()
colunas_de_preco = [c for c in df.columns if c not in COLUNAS_FIXAS]

# SIDEBAR (FILTROS)
with st.sidebar:
    caminhos_possiveis = [os.path.join(PASTA_IMAGENS, x) for x in ["logo.png", "logo.jpg", "Logo.png"]]
    logo_encontrado = next((c for c in caminhos_possiveis if os.path.exists(c)), None)
    if logo_encontrado: st.image(logo_encontrado, use_container_width=True)
    
    st.header("1. Seleção")
    filtro_fabrica = st.selectbox("Fabricante:", ["Todos"] + EMPRESAS)
    
    tabela_selecionada = None
    if colunas_de_preco:
        tabela_selecionada = st.selectbox("Tabela de Preço:", colunas_de_preco)
    
    st.divider()
    st.info("💡 Vá na aba 'Gerador' para criar o PDF.")

# TABS
tab_gerador, tab_cadastro, tab_config = st.tabs(["📄 Gerador de Tabela", "📝 Cadastro", "⚙️ Ajustes"])

# ==============================================================================
# ABA 1: GERADOR DE TABELA (O CORAÇÃO DO SISTEMA AGORA)
# ==============================================================================
with tab_gerador:
    st.markdown("### Selecione os produtos para a tabela")
    
    # 1. PREPARAR DADOS PARA SELEÇÃO
    df_filtrado = df.copy()
    if filtro_fabrica != "Todos":
        df_filtrado = df_filtrado[df_filtrado["fabricante"] == filtro_fabrica]
    
    if df_filtrado.empty:
        st.warning("Nenhum produto encontrado.")
    elif not tabela_selecionada:
        st.warning("Crie uma tabela de preços na aba Ajustes.")
    else:
        # Adiciona coluna de Checkbox
        df_filtrado.insert(0, "Selecionar", False)
        
        # Mostra Tabela Editável
        colunas_visiveis = ["Selecionar", "codigo", "nome", "fabricante", tabela_selecionada]
        
        # O data_editor permite marcar os checkboxes
        df_edicao = st.data_editor(
            df_filtrado[colunas_visiveis],
            hide_index=True,
            column_config={
                "Selecionar": st.column_config.CheckboxColumn("Incluir?", default=False),
                tabela_selecionada: st.column_config.NumberColumn("Preço", format="R$ %.2f"),
                "imagem": st.column_config.ImageColumn("Foto")
            },
            disabled=["codigo", "nome", "fabricante", tabela_selecionada], # Trava edição de dados
            use_container_width=True
        )
        
        # 2. BOTÃO GERAR
        st.markdown("---")
        col_input, col_btn = st.columns([3, 1])
        cliente_nome = col_input.text_input("Nome do Cliente (Opcional):", placeholder="Ex: Supermercado Central")
        
        # Lógica para pegar os itens marcados
        itens_selecionados = df_edicao[df_edicao["Selecionar"] == True]
        
        if not itens_selecionados.empty:
            st.success(f"{len(itens_selecionados)} produtos selecionados.")
            
            # --- ÁREA DA FOLHA DE PAPEL (PREVIEW) ---
            with st.container(border=True):
                # Conversão de logo Fantini para Base64 (para aparecer na impressão)
                logo_b64 = ""
                if logo_encontrado:
                    logo_b64 = get_img_as_base64(logo_encontrado)
                
                # Montagem do HTML
                html_rows = ""
                for idx, row in itens_selecionados.iterrows():
                    # Busca imagem original
                    img_row_path = os.path.join(PASTA_IMAGENS, df.loc[df["codigo"] == row["codigo"], "imagem"].values[0])
                    img_b64 = get_img_as_base64(img_row_path)
                    
                    img_tag = ""
                    if img_b64:
                        img_tag = f"<img src='data:image/png;base64,{img_b64}' class='thumb-tabela'>"
                    
                    # Preço
                    preco = row[tabela_selecionada]
                    
                    html_rows += f"""
                    <tr>
                        <td style='text-align:center'>{img_tag}</td>
                        <td>{row['codigo']}</td>
                        <td><strong>{row['nome']}</strong></td>
                        <td style='text-align:right'><strong>R$ {preco:,.2f}</strong></td>
                    </tr>
                    """

                # Data atual
                data_hoje = datetime.now().strftime("%d/%m/%Y")
                
                # HTML COMPLETO
                html_tabela = f"""
                <div class="folha-tabela">
                    <div class="header-folha">
                        <div>
                            <img src="data:image/png;base64,{logo_b64}" style="max-height:60px;">
                            <div style="font-size:12px; margin-top:5px; color:#555 !important;">Representação Comercial</div>
                        </div>
                        <div style="text-align:right;">
                            <h3 style="margin:0;">TABELA DE PREÇOS</h3>
                            <div style="font-size:14px;">Condição: <strong>{tabela_selecionada}</strong></div>
                            <div style="font-size:14px;">Data: {data_hoje}</div>
                            <div style="font-size:16px; margin-top:5px; color:#2c3e50 !important;">{cliente_nome}</div>
                        </div>
                    </div>
                    
                    <table class="tabela-clean">
                        <thead>
                            <tr>
                                <th width="50px">Foto</th>
                                <th width="100px">Cód.</th>
                                <th>Produto</th>
                                <th width="120px" style="text-align:right">Preço Unit.</th>
                            </tr>
                        </thead>
                        <tbody>
                            {html_rows}
                        </tbody>
                    </table>
                    
                    <div style="margin-top:30px; border-top:1px solid #ddd; padding-top:10px; font-size:11px; text-align:center; color:#777 !important;">
                        Documento gerado pelo Sistema Fantini. Sujeito a alteração sem aviso prévio.
                    </div>
                </div>
                """
                
                st.markdown(html_tabela, unsafe_allow_html=True)
                
                st.info("🖨️ Para enviar: Pressione **Ctrl + P** e escolha 'Salvar como PDF'.")

# ==============================================================================
# ABA 2: CADASTRO (IGUAL AO ANTERIOR, MAS COMPACTO)
# ==============================================================================
with tab_cadastro:
    c1, c2 = st.columns([2, 1])
    with c2:
        st.markdown("##### Buscar")
        if not df.empty:
            df['codigo'] = df['codigo'].astype(str)
            opts = df["codigo"] + " | " + df["nome"]
            sel = st.selectbox("Editar:", ["Selecione..."] + list(opts))
            if st.button("Carregar", use_container_width=True):
                if sel != "Selecione...": st.session_state["edit_codigo"] = sel.split(" | ")[0]; st.rerun()

    with c1:
        cod_edit = st.session_state["edit_codigo"]
        dados = df[df["codigo"] == str(cod_edit)].iloc[0] if cod_edit else None
        
        st.markdown(f"##### {'✏️ ' + dados['nome'] if dados is not None else '➕ Novo Produto'}")
        if dados is not None and st.button("Cancelar"): st.session_state["edit_codigo"] = None; st.rerun()
        
        with st.container(border=True):
            fab_idx = EMPRESAS.index(dados["fabricante"]) if dados is not None and dados["fabricante"] in EMPRESAS else 0
            
            fabricante = st.selectbox("Fabricante", EMPRESAS, index=fab_idx)
            nome = st.text_input("Nome", value=dados["nome"] if dados is not None else "")
            
            c_a, c_b = st.columns(2)
            codigo = c_a.text_input("Cód (Opcional)", value="" if dados is not None and str(dados["codigo"]).startswith("AUTO") else (dados["codigo"] if dados is not None else ""))
            barras = c_b.text_input("EAN", value=dados["barras"] if dados is not None else "")
            
            f_img = st.file_uploader("Foto", type=['jpg','png'])
            
            if colunas_de_preco:
                st.write("Preços:")
                precos = {col: st.number_input(col, value=float(dados[col]) if dados is not None else 0.0) for col in colunas_de_preco}
                
                if st.button("💾 Salvar", type="primary", use_container_width=True):
                    cod_final = codigo if codigo else (dados["codigo"] if dados is not None else None)
                    if nome:
                        salvar_produto(cod_final, barras, nome, fabricante, f_img, precos, modo_edicao=(dados is not None))
                        st.session_state["edit_codigo"] = None; st.rerun()
                    else: st.warning("Nome obrigatório")
                
                if dados is not None and st.button("🗑️ Excluir"):
                    excluir_produto(dados["codigo"]); st.session_state["edit_codigo"] = None; st.rerun()

# ==============================================================================
# ABA 3: AJUSTES
# ==============================================================================
with tab_config:
    c1, c2 = st.columns(2)
    with c1:
        new = st.text_input("Nova Tabela")
        if st.button("Criar"):
             if new: criar_categoria(new); st.rerun()
    with c2:
        if colunas_de_preco:
            dele = st.selectbox("Apagar:", colunas_de_preco)
            if st.button("Apagar"): excluir_categoria(dele); st.rerun()