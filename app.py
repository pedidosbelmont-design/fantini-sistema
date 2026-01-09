import streamlit as st
import pandas as pd
import os
import time
import base64
from datetime import datetime

# --- 1. CONFIGURAÇÃO GERAL ---
st.set_page_config(
    layout="wide", 
    page_title="Sistema Fantini", 
    page_icon="📄",
    initial_sidebar_state="expanded"
)

PASTA_IMAGENS = "static"
ARQUIVO_DB = "banco_produtos_dinamico.csv"
COLUNAS_FIXAS = ["codigo", "barras", "nome", "imagem", "fabricante"]
EMPRESAS = ["Vinagre Belmont", "Serve Sempre"]

# --- FUNÇÃO ESSENCIAL: CONVERTER IMAGEM PARA CÓDIGO (BASE64) ---
# Isso garante que a imagem apareça na impressão do PDF
def get_img_as_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            # Lê a imagem em binário
            data = f.read()
        # Converte para base64 string
        encoded = base64.b64encode(data).decode()
        # Retorna já no formato HTML pronto
        return f"data:image/png;base64,{encoded}"
    return None

# --- CSS PROFISSIONAL PARA IMPRESSÃO ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    h1, h2, h3, p, div, span, label { color: #1c1e21 !important; }

    /* --- ESTILO DA FOLHA A4 NA TELA --- */
    .folha-a4-preview {
        background-color: white;
        width: 100%;
        max-width: 850px; /* Largura aproximada A4 */
        margin: 20px auto;
        padding: 40px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }

    /* --- CABEÇALHO DA TABELA --- */
    .header-tabela {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        border-bottom: 3px solid #2c3e50;
        padding-bottom: 20px;
        margin-bottom: 30px;
    }
    .titulo-tabela {
        font-size: 24px; font-weight: bold; color: #2c3e50; margin: 0;
    }
    .subtitulo-tabela {
        font-size: 14px; color: #555; margin-top: 5px;
    }

    /* --- A TABELA EM SI --- */
    .tabela-produtos {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .tabela-produtos th {
        background-color: #34495e !important; /* Cor escura no cabeçalho */
        color: white !important;
        padding: 12px 8px;
        text-align: left;
        font-size: 14px;
        text-transform: uppercase;
        /* OBRIGA O NAVEGADOR A IMPRIMIR A COR DE FUNDO */
        -webkit-print-color-adjust: exact; 
        print-color-adjust: exact;
    }
    .tabela-produtos td {
        padding: 10px 8px;
        border-bottom: 1px solid #eee;
        vertical-align: middle;
        color: #333;
    }
    /* Zebra na tabela para facilitar leitura */
    .tabela-produtos tr:nth-child(even) {
        background-color: #f9f9f9 !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }

    /* --- IMAGEM DO PRODUTO NA TABELA --- */
    .img-produto-tabela {
        width: 60px;
        height: 60px;
        object-fit: contain;
        border: 1px solid #eee;
        background-color: #fff;
        padding: 2px;
    }

    /* --- DADOS DO PRODUTO --- */
    .prod-nome { font-weight: bold; font-size: 14px; margin-bottom: 4px; }
    .prod-ean { font-size: 11px; color: #777; }
    .prod-cod { font-weight: bold; color: #555; }
    .prod-preco { font-weight: bold; font-size: 16px; color: #2c3e50; }

    /* ========================================================================
       REGRAS CRÍTICAS PARA IMPRESSÃO (CTRL+P)
       ======================================================================== */
    @media print {
        /* Esconde tudo do Streamlit que não é a tabela */
        [data-testid="stSidebar"], [data-testid="stHeader"], .stTabs, .stButton, .stAlert, footer, .no-print {
            display: none !important;
        }
        /* Remove margens do site */
        .block-container { padding: 0 !important; margin: 0 !important; }
        
        /* Ajusta a folha para ocupar o papel todo */
        .folha-a4-preview {
            box-shadow: none;
            border: none;
            padding: 0;
            margin: 0;
            width: 100%;
            max-width: none;
        }
        /* Evita quebrar uma linha de produto no meio de duas páginas */
        tr { page-break-inside: avoid; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. FUNÇÕES DE DADOS ---
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

# --- 3. APP PRINCIPAL ---
inicializar()
if "edit_codigo" not in st.session_state: st.session_state["edit_codigo"] = None

df = carregar_dados()
colunas_de_preco = [c for c in df.columns if c not in COLUNAS_FIXAS]

# SIDEBAR
with st.sidebar:
    # Busca logo da Fantini
    caminhos_logo = [os.path.join(PASTA_IMAGENS, x) for x in ["logo.png", "logo.jpg"]]
    path_logo_fantini = next((c for c in caminhos_logo if os.path.exists(c)), None)
    if path_logo_fantini: st.image(path_logo_fantini, use_container_width=True)
    
    st.header("Configuração da Tabela")
    filtro_fabrica = st.selectbox("1. Fabricante:", ["Todos"] + EMPRESAS)
    
    tabela_selecionada = None
    if colunas_de_preco:
        tabela_selecionada = st.selectbox("2. Tabela de Preço:", colunas_de_preco)
    
    st.divider()
    st.info("Vá para a aba 'Gerador PDF' para criar o documento.")

# TABS
tab_gerador, tab_cadastro, tab_config = st.tabs(["📄 Gerador PDF", "📝 Cadastro Produtos", "⚙️ Tabelas"])

# ==============================================================================
# ABA 1: GERADOR DE PDF PROFISSIONAL
# ==============================================================================
with tab_gerador:
    # 1. PREPARAR DADOS
    df_filtrado = df.copy()
    if filtro_fabrica != "Todos":
        df_filtrado = df_filtrado[df_filtrado["fabricante"] == filtro_fabrica]
    
    if df_filtrado.empty:
        st.warning("Nenhum produto encontrado para este fabricante.")
    elif not tabela_selecionada:
        st.warning("Selecione uma tabela de preços na barra lateral.")
    else:
        st.markdown("### 1. Selecione os produtos para a tabela:")
        # Adiciona checkbox
        df_filtrado.insert(0, "Incluir", False)
        
        # Editor de dados
        colunas_visiveis = ["Incluir", "codigo", "nome", "barras", tabela_selecionada]
        df_edicao = st.data_editor(
            df_filtrado[colunas_visiveis],
            hide_index=True,
            column_config={
                "Incluir": st.column_config.CheckboxColumn("Selecionar", default=False),
                tabela_selecionada: st.column_config.NumberColumn("Preço", format="R$ %.2f"),
            },
            disabled=["codigo", "nome", "barras", tabela_selecionada],
            use_container_width=True,
            height=300
        )
        
        st.markdown("---")
        st.markdown("### 2. Personalizar e Gerar:")
        
        # Inputs do cliente
        c_cli, c_obs = st.columns(2)
        cliente_nome = c_cli.text_input("Nome do Cliente:", placeholder="Ex: Supermercado ABC")
        observacao = c_obs.text_input("Observação (Rodapé):", placeholder="Ex: Validade de 5 dias.")

        itens_marcados = df_edicao[df_edicao["Incluir"] == True]
        
        if itens_marcados.empty:
            st.info("Selecione pelo menos um produto acima para gerar a tabela.")
        else:
            # --- GERAÇÃO DO HTML PARA IMPRESSÃO ---
            
            # 1. Prepara a Logo da Fantini em Base64
            img_logo_b64 = ""
            if path_logo_fantini:
                img_logo_b64 = get_img_as_base64(path_logo_fantini)

            # 2. Monta as linhas da tabela (TR)
            html_rows = ""
            for idx, row in itens_marcados.iterrows():
                # Busca imagem do produto e converte para Base64
                img_prod_path = os.path.join(PASTA_IMAGENS, df.loc[df["codigo"] == row["codigo"], "imagem"].values[0])
                img_prod_b64 = get_img_as_base64(img_prod_path)
                
                # Tag da imagem (ou vazio se não tiver)
                img_tag = f"<img src='{img_prod_b64}' class='img-produto-tabela'>" if img_prod_b64 else "<span style='color:#ccc; font-size:10px;'>S/ Foto</span>"
                
                # Formata dados
                codigo_display = row['codigo'] if not str(row['codigo']).startswith("AUTO-") else "---"
                ean_display = f"EAN: {row['barras']}" if row['barras'] and str(row['barras']) != "nan" else ""
                preco = row[tabela_selecionada]

                html_rows += f"""
                <tr>
                    <td style='text-align:center;'>{img_tag}</td>
                    <td class='prod-cod'>{codigo_display}</td>
                    <td>
                        <div class='prod-nome'>{row['nome']}</div>
                        <div class='prod-ean'>{ean_display}</div>
                    </td>
                    <td style='text-align:right;' class='prod-preco'>R$ {preco:,.2f}</td>
                </tr>
                """

            # 3. Monta o Documento Completo
            data_hoje = datetime.now().strftime("%d/%m/%Y")
            fab_titulo = f" - {filtro_fabrica}" if filtro_fabrica != "Todos" else ""
            
            html_final = f"""
            <div class="folha-a4-preview">
                <div class="header-tabela">
                    <div>
                        <img src="{img_logo_b64}" style="max-height:70px; margin-bottom:10px;">
                        <div style="color:#555;">Representação Comercial</div>
                    </div>
                    <div style="text-align:right;">
                        <h2 class="titulo-tabela">TABELA DE PREÇOS{fab_titulo}</h2>
                        <div class="subtitulo-tabela">Tabela Base: <strong>{tabela_selecionada}</strong></div>
                        <div class="subtitulo-tabela">Data: {data_hoje}</div>
                        {f'<div style="margin-top:10px; font-weight:bold; font-size:16px;">Cliente: {cliente_nome}</div>' if cliente_nome else ''}
                    </div>
                </div>
                
                <table class="tabela-produtos">
                    <thead>
                        <tr>
                            <th width="70px" style="text-align:center;">Foto</th>
                            <th width="100px">Código</th>
                            <th>Descrição do Produto / EAN</th>
                            <th width="130px" style="text-align:right;">Preço Unit.</th>
                        </tr>
                    </thead>
                    <tbody>
                        {html_rows}
                    </tbody>
                </table>
                
                <div style="margin-top:40px; border-top:1px solid #ccc; padding-top:15px; font-size:12px; color:#666;">
                    <div><strong>Observações:</strong> {observacao if observacao else 'Preços sujeitos a alteração sem aviso prévio.'}</div>
                </div>
            </div>
            """
            
            # Mostra o resultado na tela
            st.markdown(html_final, unsafe_allow_html=True)
            
            # Botão de instrução (não sai na impressão porque tem a classe no-print)
            st.success("✅ Tabela gerada com sucesso abaixo!", icon="🖨️")
            st.markdown("""
                <div class='no-print' style='background-color:#d4edda; color:#155724; padding:15px; border-radius:8px; border:1px solid #c3e6cb; margin-bottom:20px;'>
                    <strong>Como salvar em PDF com fotos e cores:</strong>
                    <ol>
                        <li>Pressione <b>Ctrl + P</b> (ou Cmd + P no Mac).</li>
                        <li>Em "Destino", escolha <b>"Salvar como PDF"</b>.</li>
                        <li><b>MUITO IMPORTANTE:</b> Nas opções de impressão (clique em "Mais definições"), marque a caixa <b>"Gráficos de segundo plano"</b> (ou "Background graphics"). Isso fará o cabeçalho cinza aparecer.</li>
                        <li>Clique em Salvar.</li>
                    </ol>
                </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# ABA 2: CADASTRO (Funcionalidade mantida)
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
            
            f_img = st.file_uploader("Foto (Ideal: Quadrada)", type=['jpg','png'])
            
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
# ABA CONFIG
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