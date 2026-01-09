import streamlit as st
import pandas as pd
import os
import time
import base64
import io
from datetime import datetime
from PIL import Image

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

# --- FUNÇÃO MÁGICA: CRIAR THUMBNAIL (MINIATURA) ---
def get_thumbnail_as_base64(file_path, size=(80, 80)):
    """
    Lê a imagem, REDIMENSIONA para ficar bem pequena (thumbnail)
    e retorna o código para o HTML. Isso evita travar o navegador.
    """
    if os.path.exists(file_path):
        try:
            img = Image.open(file_path)
            # Converte para RGB (evita erro em PNG transparente)
            if img.mode in ("RGBA", "P"): 
                img = img.convert("RGB")
            
            # Força o tamanho pequeno (Thumbnail)
            img.thumbnail(size)
            
            # Salva na memória
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            
            # Gera código
            encoded = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{encoded}"
        except Exception:
            return None
    return None

# --- CSS A4 + IMPRESSÃO ---
st.markdown("""
<style>
    .stApp { background-color: #525659; } /* Fundo cinza escuro tipo Acrobat Reader */
    h1, h2, h3, p, div, span, label { color: #1c1e21 !important; }

    /* --- SIMULAÇÃO FOLHA A4 --- */
    .folha-a4 {
        background-color: white;
        width: 210mm;
        min-height: 297mm;
        margin: 20px auto;
        padding: 15mm;
        box-shadow: 0 0 15px rgba(0,0,0,0.5);
        position: relative;
    }

    /* CABEÇALHO */
    .header-tabela {
        display: flex; justify-content: space-between; align-items: flex-end;
        border-bottom: 2px solid #2c3e50; padding-bottom: 15px; margin-bottom: 20px;
    }
    .titulo-tabela { font-size: 20px; font-weight: bold; color: #2c3e50; margin: 0; text-transform: uppercase; }
    
    /* TABELA */
    .tabela-produtos {
        width: 100%; border-collapse: collapse; font-family: 'Segoe UI', sans-serif;
    }
    .tabela-produtos th {
        background-color: #34495e !important; color: white !important;
        padding: 8px 5px; text-align: left; font-size: 11px; text-transform: uppercase;
        border-bottom: 2px solid #000;
        -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }
    .tabela-produtos td {
        padding: 8px 5px; border-bottom: 1px solid #ddd; vertical-align: middle;
        color: #333; font-size: 12px;
    }
    .tabela-produtos tr:nth-child(even) {
        background-color: #f3f3f3 !important;
        -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }

    /* THUMBNAILS NA TABELA */
    .thumb-img {
        width: 50px; height: 50px; object-fit: contain;
        border: 1px solid #eee; background: #fff; padding: 2px;
        display: block; margin: 0 auto;
    }

    /* IMPRESSÃO PERFEITA */
    @page { size: A4; margin: 0; }
    @media print {
        body { background-color: white; }
        [data-testid="stSidebar"], [data-testid="stHeader"], .stTabs, .stButton, .stAlert, footer, .no-print {
            display: none !important;
        }
        .block-container { padding: 0 !important; margin: 0 !important; }
        .folha-a4 {
            width: 100%; margin: 0; box-shadow: none; border: none; padding: 10mm;
        }
        tr { page-break-inside: avoid; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DADOS ---
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
    
    if not modo_edicao and str(codigo) in df["codigo"].astype(str).values:
        return False, "⚠️ Código já existe!"

    nome_imagem = "sem_foto.png"
    if modo_edicao:
        df = df[df["codigo"].astype(str) != str(codigo)]
        idx_antigo = pd.read_csv(ARQUIVO_DB)
        filtro = idx_antigo[idx_antigo["codigo"].astype(str) == str(codigo)]
        if not filtro.empty: nome_imagem = filtro.iloc[0]["imagem"]

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
    df = df[df["codigo"].astype(str) != str(codigo)]
    salvar_dados(df)

def criar_categoria(nome):
    df = carregar_dados()
    if nome not in df.columns: df[nome] = 0.0; salvar_dados(df); return True, "Criado!"
    return False, "Já existe."

def excluir_categoria(nome):
    df = carregar_dados()
    if nome in df.columns and nome not in COLUNAS_FIXAS: df = df.drop(columns=[nome]); salvar_dados(df); return True, "Removida."
    return False, "Erro."

# --- APP ---
inicializar()
if "edit_codigo" not in st.session_state: st.session_state["edit_codigo"] = None
df = carregar_dados()
colunas_de_preco = [c for c in df.columns if c not in COLUNAS_FIXAS]

with st.sidebar:
    caminhos_logo = [os.path.join(PASTA_IMAGENS, x) for x in ["logo.png", "logo.jpg"]]
    path_logo_fantini = next((c for c in caminhos_logo if os.path.exists(c)), None)
    if path_logo_fantini: st.image(path_logo_fantini, use_container_width=True)
    
    st.header("1. Filtros")
    filtro_fabrica = st.selectbox("Fabricante:", ["Todos"] + EMPRESAS)
    tabela_selecionada = st.selectbox("Tabela:", colunas_de_preco) if colunas_de_preco else None
    if not tabela_selecionada: st.warning("Crie tabelas em Ajustes.")
    st.divider()

tab_gerador, tab_cadastro, tab_config = st.tabs(["📄 Tabela A4", "📝 Produtos", "⚙️ Ajustes"])

# --- ABA 1: GERADOR A4 COM THUMBNAILS ---
with tab_gerador:
    df_filtrado = df.copy()
    if filtro_fabrica != "Todos":
        df_filtrado = df_filtrado[df_filtrado["fabricante"] == filtro_fabrica]
    
    if df_filtrado.empty:
        st.warning("Sem produtos.")
    elif not tabela_selecionada:
        st.info("Selecione a tabela.")
    else:
        st.markdown("### Selecione para imprimir:")
        df_filtrado.insert(0, "Incluir", False)
        
        # Editor
        df_edicao = st.data_editor(
            df_filtrado[["Incluir", "codigo", "nome", "barras", tabela_selecionada]],
            hide_index=True,
            column_config={"Incluir": st.column_config.CheckboxColumn("Add", default=False),
                           tabela_selecionada: st.column_config.NumberColumn("Preço", format="R$ %.2f")},
            disabled=["codigo", "nome", "barras", tabela_selecionada],
            use_container_width=True, height=250
        )
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        cliente_nome = c1.text_input("Cliente:", placeholder="Mercado X")
        observacao = c2.text_input("Nota:", placeholder="Validade...")

        itens_marcados = df_edicao[df_edicao["Incluir"] == True]
        
        if not itens_marcados.empty:
            # Logo Fantini
            logo_b64 = ""
            if path_logo_fantini:
                res = get_thumbnail_as_base64(path_logo_fantini, size=(200, 100))
                if res: logo_b64 = res

            # GERA LINHAS (TR) COM THUMBNAILS
            html_rows = ""
            for idx, row in itens_marcados.iterrows():
                # 1. Pega Thumb do Produto
                img_tag = ""
                try:
                    nome_arq = df.loc[df["codigo"] == row["codigo"], "imagem"].values[0]
                    caminho_img = os.path.join(PASTA_IMAGENS, str(nome_arq))
                    # Cria miniatura de 80x80 na hora
                    thumb_b64 = get_thumbnail_as_base64(caminho_img, size=(80, 80))
                    
                    if thumb_b64:
                        img_tag = f"<img src='{thumb_b64}' class='thumb-img'>"
                    else:
                        img_tag = "<span style='color:#ccc; font-size:10px; text-align:center; display:block;'>S/ FOTO</span>"
                except:
                    img_tag = ""

                cod = row['codigo'] if not str(row['codigo']).startswith("AUTO-") else ""
                ean = f"<br><span style='font-size:10px; color:#777'>EAN: {row['barras']}</span>" if row['barras'] and str(row['barras']) != "nan" else ""
                preco = row[tabela_selecionada]

                # HTML COMPACTADO PARA NÃO DAR ERRO
                html_rows += f"<tr><td style='text-align:center; width:60px;'>{img_tag}</td><td style='font-weight:bold; color:#555;'>{cod}</td><td><div style='font-weight:bold; font-size:12px;'>{row['nome']}</div>{ean}</td><td style='text-align:right; font-weight:bold; font-size:14px;'>R$ {preco:,.2f}</td></tr>"

            # 2. MONTA A FOLHA A4
            data_hoje = datetime.now().strftime("%d/%m/%Y")
            tit_fab = f" - {filtro_fabrica}" if filtro_fabrica != "Todos" else ""
            logo_html = f'<img src="{logo_b64}" style="max-height:60px;">' if logo_b64 else '<h2>FANTINI</h2>'

            html_final = f"""
<div class="folha-a4">
<div class="header-tabela">
    <div>{logo_html}<div style="font-size:11px; margin-top:5px; color:#555;">Representação Comercial</div></div>
    <div style="text-align:right;">
        <div class="titulo-tabela">Tabela de Preços{tit_fab}</div>
        <div style="font-size:13px;">Condição: <strong>{tabela_selecionada}</strong> | Data: {data_hoje}</div>
        {f'<div style="font-weight:bold; margin-top:5px;">Cliente: {cliente_nome}</div>' if cliente_nome else ''}
    </div>
</div>
<table class="tabela-produtos">
    <thead>
        <tr>
            <th style="text-align:center;">Foto</th>
            <th>Cód.</th>
            <th>Descrição</th>
            <th style="text-align:right;">Preço</th>
        </tr>
    </thead>
    <tbody>{html_rows}</tbody>
</table>
<div style="margin-top:30px; border-top:1px solid #ccc; padding-top:5px; font-size:10px; text-align:center; color:#777;">
    {observacao if observacao else 'Sujeito a alteração sem aviso prévio.'}
</div>
</div>
"""
            st.markdown(html_final, unsafe_allow_html=True)
            st.markdown("<div class='no-print' style='text-align:center; margin-top:10px;'>🖨️ <b>Ctrl + P</b> (Marque 'Gráficos de plano de fundo')</div>", unsafe_allow_html=True)
        else:
            st.info("Selecione produtos.")

# --- ABA 2: CADASTRO ---
with tab_cadastro:
    c1, c2 = st.columns([2, 1])
    with c2:
        st.markdown("##### Buscar")
        if not df.empty:
            df['codigo'] = df['codigo'].astype(str)
            opts = df["codigo"] + " | " + df["nome"]
            sel = st.selectbox("Editar:", ["Novo..."] + list(opts))
            if st.button("Carregar", use_container_width=True):
                st.session_state["edit_codigo"] = sel.split(" | ")[0] if sel != "Novo..." else None
                st.rerun()
    with c1:
        cod_edit = st.session_state["edit_codigo"]
        dados = df[df["codigo"].astype(str) == str(cod_edit)].iloc[0] if cod_edit else None
        st.markdown(f"##### {'✏️ ' + dados['nome'] if dados else '➕ Novo'}")
        if dados and st.button("Cancelar"): st.session_state["edit_codigo"] = None; st.rerun()
        
        with st.container(border=True):
            fab_idx = EMPRESAS.index(dados["fabricante"]) if dados and dados["fabricante"] in EMPRESAS else 0
            fabricante = st.selectbox("Fabricante", EMPRESAS, index=fab_idx)
            nome = st.text_input("Nome *", value=dados["nome"] if dados else "")
            c_a, c_b = st.columns(2)
            val_cod = dados["codigo"] if dados else ""; 
            if str(val_cod).startswith("AUTO-"): val_cod = ""
            codigo = c_a.text_input("Cód.", value=val_cod, disabled=(dados is not None))
            barras = c_b.text_input("EAN", value=dados["barras"] if dados else "")
            f_img = st.file_uploader("Foto", type=['jpg','png'])
            if dados and not f_img: st.caption(f"Foto atual: {dados['imagem']}")
            st.divider()
            
            if colunas_de_preco:
                precos = {col: st.number_input(col, value=float(dados[col]) if dados else 0.0) for col in colunas_de_preco}
                c_sv, c_dl = st.columns(2)
                if c_sv.button("💾 Salvar", type="primary", use_container_width=True):
                    cod_fin = codigo if codigo else (dados["codigo"] if dados else None)
                    if nome:
                        ok, m = salvar_produto(cod_fin, barras, nome, fabricante, f_img, precos, modo_edicao=(dados is not None))
                        if ok: st.success(m); st.session_state["edit_codigo"] = None; time.sleep(1); st.rerun()
                        else: st.error(m)
                    else: st.warning("Nome obrigatório")
                if dados and c_dl.button("🗑️ Excluir", use_container_width=True):
                    excluir_produto(dados["codigo"]); st.session_state["edit_codigo"] = None; st.rerun()
            else: st.warning("Crie tabelas primeiro.")

# --- ABA 3: AJUSTES ---
with tab_config:
    c1, c2 = st.columns(2)
    with c1:
        new = st.text_input("Nova Tabela")
        if st.button("Criar", use_container_width=True):
             if new: ok, m = criar_categoria(new); 
             if ok: st.success(m); time.sleep(0.5); st.rerun()
    with c2:
        if colunas_de_preco:
            dele = st.selectbox("Apagar:", colunas_de_preco)
            if st.button("Apagar", use_container_width=True):
                ok, m = excluir_categoria(dele)
                if ok: st.warning(m); time.sleep(0.5); st.rerun()