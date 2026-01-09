import streamlit as st
import pandas as pd
import os
import time
import io
from datetime import datetime
from PIL import Image
from fpdf import FPDF
from fpdf.fonts import FontFace

# --- 1. CONFIGURAÇÃO GERAL ---
st.set_page_config(layout="wide", page_title="Sistema Fantini", page_icon="📄")

PASTA_IMAGENS = "static"
ARQUIVO_DB = "banco_produtos_dinamico.csv"
COLUNAS_FIXAS = ["codigo", "barras", "nome", "imagem", "fabricante"]
EMPRESAS = ["Vinagre Belmont", "Serve Sempre"]

# --- CSS PARA O PREVIEW NA TELA ---
st.markdown("""
<style>
    .stApp { background-color: #eaeff2; }
    .preview-card {
        background: white; padding: 10px 15px; border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 8px;
        display: flex; align-items: center; border-left: 4px solid #2c3e50;
    }
    .preview-img { width: 40px; height: 40px; object-fit: contain; margin-right: 15px; border: 1px solid #eee; border-radius: 4px;}
    .preview-info { flex-grow: 1; }
    .preview-title { font-weight: bold; font-size: 14px; color: #333; }
    .preview-code { font-size: 11px; color: #777; }
    .preview-price { font-weight: bold; color: #27ae60; font-size: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 2. CLASSE PDF (AJUSTADA: LOGO NÃO CORTA MAIS) ---
class PDF(FPDF):
    def header(self):
        # 1. LOGO (Ajustei X=15 para não cortar)
        logo_path = None
        for ext in ["png", "jpg"]:
            if os.path.exists(f"static/logo.{ext}"): logo_path = f"static/logo.{ext}"
        
        if logo_path:
            # x=15 (mais para direita), y=10, w=30 (largura)
            self.image(logo_path, 15, 10, 30) 
        
        # 2. TÍTULO (Alinhado com a nova posição da logo)
        self.set_y(15) # Alinha verticalmente com o meio da logo
        self.set_font('helvetica', 'B', 16)
        self.cell(50) # Empurra para direita (pula a logo)
        self.cell(0, 10, 'FANTINI REPRESENTAÇÕES', ln=False, align='L')
        self.ln(25) # Espaço após o cabeçalho

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}/{{nb}}', align='C')

def gerar_pdf_final(df_itens, cliente, obs, tabela_col, df_completo):
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # --- BLOCO CINZA DE INFORMAÇÕES ---
    pdf.set_fill_color(245, 245, 245) # Cinza bem clarinho e elegante
    # x=10, y=35, w=190, h=25
    pdf.rect(10, 35, 190, 25, 'F') 
    
    pdf.set_y(38)
    pdf.set_x(15)
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(0, 5, f"TABELA: {tabela_col.upper()}", ln=True)
    
    pdf.set_x(15)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 5, f"CLIENTE: {cliente}", ln=True)
    
    pdf.set_x(15)
    pdf.cell(0, 5, f"DATA: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10) # Espaço antes da tabela
    
    # --- TABELA DE PRODUTOS ---
    # Definição exata das larguras (Soma ~190mm)
    # Foto: 15mm | Cód: 25mm | Descrição: 110mm | Preço: 40mm
    col_widths = (15, 25, 110, 40) 
    
    with pdf.table(col_widths=col_widths, text_align=("C", "L", "L", "R"), line_height=7) as table:
        # CABEÇALHO
        row = table.row()
        estilo_header = FontFace(emphasis="BOLD", color=255, fill_color=(44, 62, 80)) # Azul Escuro
        row.cell("FOTO", style=estilo_header)
        row.cell("CÓDIGO", style=estilo_header)
        row.cell("DESCRIÇÃO", style=estilo_header)
        row.cell("PREÇO", style=estilo_header)
        
        # LINHAS DOS ITENS
        pdf.set_font("helvetica", size=9)
        
        for idx, item in df_itens.iterrows():
            row = table.row()
            
            # 1. FOTO
            try:
                nome_arq = df_completo.loc[df_completo["codigo"] == item["codigo"], "imagem"].values[0]
                caminho_img = os.path.join(PASTA_IMAGENS, str(nome_arq))
                if os.path.exists(caminho_img):
                    row.cell(img=caminho_img, img_fill_width=True)
                else:
                    row.cell("-")
            except:
                row.cell("-")

            # 2. CÓDIGO
            cod_str = str(item['codigo']).replace("AUTO-", "")
            row.cell(cod_str)
            
            # 3. DESCRIÇÃO
            ean = item['barras'] if 'barras' in item and str(item['barras']) != "nan" else ""
            desc_text = f"{item['nome']}\nEAN: {ean}"
            row.cell(desc_text)
            
            # 4. PREÇO (Negrito)
            preco = f"R$ {item[tabela_col]:,.2f}"
            row.cell(preco, style=FontFace(emphasis="BOLD"))

    # --- RODAPÉ OBS ---
    pdf.ln(5)
    pdf.set_font("helvetica", 'I', 8)
    pdf.multi_cell(0, 5, f"Observações: {obs if obs else 'Validade conforme estoque.'}")
    
    return pdf.output(dest='S')

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
    
    st.header("Menu")
    filtro_fabrica = st.selectbox("Fabricante:", ["Todos"] + EMPRESAS)
    tabela_ativa = st.selectbox("Tabela:", colunas_preco) if colunas_preco else None

tab_gerador, tab_cadastro, tab_config = st.tabs(["📄 Exportar PDF", "📝 Cadastro", "⚙️ Tabelas"])

# --- ABA 1: GERADOR ---
with tab_gerador:
    if not tabela_ativa:
        st.warning("Crie tabelas primeiro.")
    else:
        df_show = df.copy()
        if filtro_fabrica != "Todos": df_show = df_show[df_show["fabricante"] == filtro_fabrica]
        
        st.write("1. Marque os produtos:")
        df_show.insert(0, "Sel", False)
        
        edited = st.data_editor(
            df_show[["Sel", "codigo", "nome", "barras", tabela_ativa]], 
            hide_index=True,
            column_config={
                "Sel": st.column_config.CheckboxColumn("Add", default=False),
                tabela_ativa: st.column_config.NumberColumn("Preço", format="R$ %.2f")
            },
            disabled=["codigo", "nome", "barras", tabela_ativa],
            use_container_width=True, height=300
        )
        
        st.divider()
        c1, c2 = st.columns(2)
        cliente = c1.text_input("Cliente:")
        obs = c2.text_input("Obs:")
        
        selecionados = edited[edited["Sel"] == True]
        
        if not selecionados.empty:
            st.markdown("### 2. Confira:")
            
            # PREVIEW (MELHORADO)
            for i, row in selecionados.iterrows():
                # HTML Seguro para Imagem
                img_html = ""
                try:
                    nome_arq = df.loc[df["codigo"] == row["codigo"], "imagem"].values[0]
                    path = os.path.join(PASTA_IMAGENS, str(nome_arq))
                    if os.path.exists(path):
                        with open(path, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        img_html = f'<img src="data:image/jpeg;base64,{b64}" class="preview-img">'
                except: pass
                
                st.markdown(f"""
                <div class="preview-card">
                    {img_html}
                    <div class="preview-info">
                        <div class="preview-title">{row['nome']}</div>
                        <div class="preview-code">{row['codigo']}</div>
                    </div>
                    <div class="preview-price">R$ {row[tabela_ativa]:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            try:
                pdf_bytes = gerar_pdf_final(selecionados, cliente, obs, tabela_ativa, df)
                st.download_button(
                    label="📥 BAIXAR PDF (FINAL)",
                    data=bytes(pdf_bytes),
                    file_name=f"Tabela_{cliente if cliente else 'Geral'}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Erro: {e}")

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
        
        st.subheader(f"{'✏️ ' + item['nome'] if item is not None else '➕ Novo'}")
        if item is not None and st.button("Cancelar"): 
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
                    st.success("Salvo!"); st.session_state["edit_codigo"] = None; st.rerun()
                
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
