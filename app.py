import streamlit as st
import pandas as pd
import os
import time
import base64
import io
from datetime import datetime
from PIL import Image
from xhtml2pdf import pisa # Biblioteca Nova para gerar o PDF real

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

# --- FUNÇÃO: THUMBNAIL (Para visualização na tela) ---
def get_thumbnail_base64(file_path):
    if not os.path.exists(file_path): return None
    try:
        img = Image.open(file_path)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.thumbnail((100, 100)) 
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=80)
        return base64.b64encode(buffered.getvalue()).decode()
    except: return None

# --- FUNÇÃO: GERAR PDF BINÁRIO (Para o botão de download) ---
def criar_pdf_binario(html_string):
    """Converte a string HTML em um arquivo PDF real na memória"""
    result = io.BytesIO()
    # PISA/XHTML2PDF converte o HTML para PDF
    pisa_status = pisa.CreatePDF(
        io.BytesIO(html_string.encode("utf-8")),
        dest=result,
        encoding='utf-8'
    )
    if pisa_status.err:
        return None
    return result.getvalue()

# --- CSS APENAS PARA A TELA (Visualização) ---
st.markdown("""
<style>
    .stApp { background-color: #eaeff2; }
    /* Estilo do Preview na Tela */
    .preview-box {
        background: white; padding: 20px; border: 1px solid #ddd;
        border-radius: 8px; margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO ---
if not os.path.exists(PASTA_IMAGENS): os.makedirs(PASTA_IMAGENS)
if not os.path.exists(ARQUIVO_DB): pd.DataFrame(columns=COLUNAS_FIXAS).to_csv(ARQUIVO_DB, index=False)
if "edit_codigo" not in st.session_state: st.session_state["edit_codigo"] = None

def carregar(): 
    df = pd.read_csv(ARQUIVO_DB)
    if "fabricante" not in df.columns: df["fabricante"] = "Geral"; df.to_csv(ARQUIVO_DB, index=False)
    return df

# --- INTERFACE ---
df = carregar()
colunas_preco = [c for c in df.columns if c not in COLUNAS_FIXAS]

with st.sidebar:
    logo_path = None
    for ext in ["png", "jpg"]:
        if os.path.exists(f"static/logo.{ext}"): logo_path = f"static/logo.{ext}"
    if logo_path: st.image(logo_path, use_container_width=True)
    
    st.header("Filtros")
    filtro_fabrica = st.selectbox("Fabricante:", ["Todos"] + EMPRESAS)
    tabela_ativa = st.selectbox("Tabela:", colunas_preco) if colunas_preco else None

tab_gerador, tab_cadastro, tab_config = st.tabs(["📄 Exportar PDF", "📝 Cadastro", "⚙️ Tabelas"])

# --- ABA 1: GERADOR PDF (SEM IMPRESSÃO DE NAVEGADOR) ---
with tab_gerador:
    if not tabela_ativa:
        st.warning("Crie tabelas primeiro.")
    else:
        df_show = df.copy()
        if filtro_fabrica != "Todos": df_show = df_show[df_show["fabricante"] == filtro_fabrica]
        
        st.write("Selecione os produtos:")
        df_show.insert(0, "Sel", False)
        
        edited = st.data_editor(
            df_show[["Sel", "codigo", "nome", tabela_ativa]],
            hide_index=True,
            column_config={"Sel": st.column_config.CheckboxColumn("", default=False),
                           tabela_ativa: st.column_config.NumberColumn("Preço", format="R$ %.2f")},
            disabled=["codigo", "nome", tabela_ativa],
            use_container_width=True
        )
        
        st.divider()
        c1, c2 = st.columns(2)
        cliente = c1.text_input("Cliente:")
        obs = c2.text_input("Obs:")
        
        selecionados = edited[edited["Sel"] == True]
        
        if not selecionados.empty:
            # --- 1. PREPARAR DADOS PARA O HTML ---
            # Para o PDF ficar perfeito, usamos tabelas HTML clássicas (sem flexbox)
            # pois o gerador de PDF entende melhor tabelas antigas.
            
            logo_img_tag = ""
            if logo_path:
                b64 = get_thumbnail_base64(logo_path)
                if b64: logo_img_tag = f'<img src="data:image/jpeg;base64,{b64}" style="width:120px;">'
            
            data_hoje = datetime.now().strftime("%d/%m/%Y")
            
            # Montando as linhas da tabela
            linhas_html = ""
            for i, row in selecionados.iterrows():
                # Imagem
                img_tag = ""
                try:
                    full_row = df[df["codigo"] == row["codigo"]].iloc[0]
                    path_img = os.path.join(PASTA_IMAGENS, str(full_row["imagem"]))
                    b64_prod = get_thumbnail_base64(path_img)
                    if b64_prod: 
                        img_tag = f'<img src="data:image/jpeg;base64,{b64_prod}" style="width:40px; height:40px;">'
                except: pass

                cod = row['codigo']
                if "AUTO-" in str(cod): cod = ""
                
                linhas_html += f"""
                <tr>
                    <td style="border-bottom:1px solid #ccc; padding:5px; text-align:center;">{img_tag}</td>
                    <td style="border-bottom:1px solid #ccc; padding:5px;"><b>{cod}</b></td>
                    <td style="border-bottom:1px solid #ccc; padding:5px;">{row['nome']}</td>
                    <td style="border-bottom:1px solid #ccc; padding:5px; text-align:right;">R$ {row[tabela_ativa]:,.2f}</td>
                </tr>
                """

            # --- 2. O HTML COMPLETO (TEMPLATE) ---
            # CSS inline para garantir que o PDF entenda as cores e bordas
            html_template = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Helvetica, sans-serif; font-size: 12px; }}
                    table {{ width: 100%; border-collapse: collapse; }}
                    th {{ background-color: #2c3e50; color: white; padding: 8px; text-align: left; }}
                    .header-tbl td {{ border: none; vertical-align: bottom; }}
                </style>
            </head>
            <body>
                <table class="header-tbl" style="margin-bottom:20px;">
                    <tr>
                        <td width="50%">
                            {logo_img_tag}<br>
                            <span style="color:#666;">Representação Comercial</span>
                        </td>
                        <td width="50%" style="text-align:right;">
                            <h2 style="margin:0; color:#2c3e50;">TABELA DE PREÇOS</h2>
                            <div>Tabela: <b>{tabela_ativa}</b></div>
                            <div>Data: {data_hoje}</div>
                            <div>Cliente: <b>{cliente}</b></div>
                        </td>
                    </tr>
                </table>

                <table>
                    <thead>
                        <tr>
                            <th width="50">Foto</th>
                            <th width="80">Cód</th>
                            <th>Produto</th>
                            <th width="100" align="right">Preço</th>
                        </tr>
                    </thead>
                    <tbody>
                        {linhas_html}
                    </tbody>
                </table>

                <div style="margin-top:30px; text-align:center; color:#777; font-size:10px; border-top:1px solid #ccc; padding-top:10px;">
                    {obs if obs else 'Sujeito a alteração sem aviso prévio.'}
                </div>
            </body>
            </html>
            """
            
            # --- 3. MOSTRAR PREVIEW E BOTÃO ---
            st.markdown("### Visualização Prévia:")
            # Mostra uma versão simplificada na tela
            st.markdown(f'<div class="preview-box">{html_template}</div>', unsafe_allow_html=True)
            
            # GERA O PDF
            pdf_bytes = criar_pdf_binario(html_template)
            
            if pdf_bytes:
                st.success("✅ PDF Gerado com sucesso!")
                # BOTÃO DE DOWNLOAD REAL
                st.download_button(
                    label="📥 BAIXAR ARQUIVO PDF AGORA",
                    data=pdf_bytes,
                    file_name=f"Tabela_{cliente}_{data_hoje.replace('/','-')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            else:
                st.error("Erro ao gerar PDF. Verifique se instalou o 'xhtml2pdf'.")

# --- ABA 2: CADASTRO ---
with tab_cadastro:
    c1, c2 = st.columns([2, 1])
    with c2:
        st.write("Buscar:")
        opcoes = df["codigo"].astype(str) + " | " + df["nome"]
        busca = st.selectbox("Editar:", ["Novo"] + list(opcoes))
        if st.button("Carregar"):
            st.session_state["edit_codigo"] = busca.split(" | ")[0] if busca != "Novo" else None
            st.rerun()
            
    with c1:
        edit_cod = st.session_state["edit_codigo"]
        item = df[df["codigo"].astype(str) == str(edit_cod)].iloc[0] if edit_cod else None
        
        st.subheader(f"Editando: {item['nome']}" if item is not None else "Novo Produto")
        if item is not None and st.button("Cancelar Edição"): 
            st.session_state["edit_codigo"] = None; st.rerun()
            
        with st.container(border=True):
            idx_fab = EMPRESAS.index(item["fabricante"]) if item is not None and item["fabricante"] in EMPRESAS else 0
            fab = st.selectbox("Fab:", EMPRESAS, index=idx_fab)
            nome = st.text_input("Nome:", value=item["nome"] if item is not None else "")
            
            cc1, cc2 = st.columns(2)
            val_cod = item["codigo"] if item is not None else ""
            if "AUTO-" in str(val_cod): val_cod = ""
            
            cod = cc1.text_input("Cód:", value=val_cod, disabled=(item is not None))
            ean = cc2.text_input("EAN:", value=item["barras"] if item is not None else "")
            
            file = st.file_uploader("Foto:", type=["jpg", "png"])
            if item is not None and not file: st.caption(f"Atual: {item['imagem']}")
            
            st.divider()
            if colunas_preco:
                precos = {}
                for cp in colunas_preco:
                    v = float(item[cp]) if item is not None else 0.0
                    precos[cp] = st.number_input(f"{cp} (R$)", value=v)
                
                if st.button("Salvar", type="primary"):
                    if not nome: st.warning("Nome obrigatório"); st.stop()
                    final_cod = cod if cod else (item["codigo"] if item is not None else f"AUTO-{int(time.time())}")
                    
                    if not item and str(final_cod) in df["codigo"].astype(str).values:
                        st.error("Código já existe!"); st.stop()

                    img_name = "sem_foto.png"
                    if item is not None:
                        df = df[df["codigo"].astype(str) != str(final_cod)]
                        old_row = pd.read_csv(ARQUIVO_DB)
                        old_row = old_row[old_row["codigo"].astype(str) == str(final_cod)]
                        if not old_row.empty: img_name = old_row.iloc[0]["imagem"]

                    if file:
                        img_name = f"{final_cod}_{file.name}"
                        with open(f"{PASTA_IMAGENS}/{img_name}", "wb") as f: f.write(file.getbuffer())

                    new_row = {"codigo": final_cod, "barras": ean, "nome": nome, "fabricante": fab, "imagem": img_name}
                    new_row.update(precos)
                    
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True).fillna(0)
                    df.to_csv(ARQUIVO_DB, index=False)
                    st.success("Salvo!"); st.session_state["edit_codigo"] = None; time.sleep(0.5); st.rerun()
                
                if item is not None and st.button("Excluir"):
                    df = df[df["codigo"].astype(str) != str(final_cod)]
                    df.to_csv(ARQUIVO_DB, index=False)
                    st.success("Apagado!"); st.session_state["edit_codigo"] = None; st.rerun()

# --- ABA 3: TABELAS ---
with tab_config:
    c1, c2 = st.columns(2)
    with c1:
        n = st.text_input("Nova Tabela:")
        if st.button("Criar Tabela"):
            if n and n not in df.columns: 
                df[n] = 0.0; df.to_csv(ARQUIVO_DB, index=False); st.rerun()
    with c2:
        if colunas_preco:
            d = st.selectbox("Apagar:", colunas_preco)
            if st.button("Apagar Tabela"):
                df = df.drop(columns=[d]); df.to_csv(ARQUIVO_DB, index=False); st.rerun()