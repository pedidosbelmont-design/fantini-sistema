import streamlit as st
import pandas as pd
import os
import time
import base64
from datetime import datetime
from fpdf import FPDF
from fpdf.fonts import FontFace

# --- 1. CONFIGURAÇÃO GERAL ---
st.set_page_config(layout="wide", page_title="Sistema Fantini", page_icon="📄")

PASTA_IMAGENS = "static"
ARQUIVO_DB = "banco_produtos_dinamico.csv"
COLUNAS_FIXAS = ["codigo", "barras", "nome", "imagem", "fabricante"]
EMPRESAS = ["Vinagre Belmont", "Serve Sempre"]

# --- CSS VISUAL (PREVIEW NA TELA) ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    
    /* Card do Produto no Preview */
    .card-produto {
        background-color: white;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .card-img {
        width: 50px;
        height: 50px;
        object-fit: contain;
        border-radius: 4px;
        border: 1px solid #eee;
        margin-right: 15px;
    }
    .card-body { flex: 1; }
    .card-title { font-weight: bold; font-size: 14px; color: #333; margin: 0; }
    .card-sub { font-size: 11px; color: #666; margin-top: 2px; }
    .card-price { font-weight: bold; font-size: 16px; color: #2e7d32; }
</style>
""", unsafe_allow_html=True)

# --- 2. CLASSE PDF (LAYOUT RIGIDO) ---
class PDF(FPDF):
    def header(self):
        # Logo
        logo_path = None
        for ext in ["png", "jpg"]:
            if os.path.exists(f"static/logo.{ext}"): logo_path = f"static/logo.{ext}"
        
        if logo_path:
            # x=10, y=8, w=30
            self.image(logo_path, 10, 8, 30) 
        
        # Título
        self.set_y(15)
        self.set_font('helvetica', 'B', 15)
        self.cell(45) # Pula logo
        self.cell(0, 10, 'FANTINI REPRESENTAÇÕES', ln=False)
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Pag. {self.page_no()}/{{nb}}', align='C')

def gerar_pdf_final(df_itens, cliente, obs, tabela_col, df_completo):
    # A4 Portrait = 210mm largura. Margens default = 10mm esq/dir. Útil = 190mm.
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # --- CABEÇALHO CINZA ---
    pdf.set_fill_color(240, 240, 240)
    pdf.rect(10, 30, 190, 25, 'F')
    
    pdf.set_y(32)
    pdf.set_x(15)
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(0, 5, f"TABELA: {tabela_col.upper()}", ln=True)
    
    pdf.set_x(15)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 5, f"CLIENTE: {cliente}", ln=True)
    
    pdf.set_x(15)
    pdf.cell(0, 5, f"DATA: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10)
    
    # --- TABELA DE PRODUTOS ---
    # Larguras Fixas (Total 190mm)
    # Foto: 15mm | Cód: 25mm | Descrição: 110mm | Preço: 40mm
    w_foto = 15
    w_cod = 25
    w_desc = 110
    w_preco = 40
    col_widths = (w_foto, w_cod, w_desc, w_preco)
    
    # line_height=15 é o segredo para a foto caber verticalmente sem quebrar layout
    with pdf.table(col_widths=col_widths, text_align=("C", "L", "L", "R"), line_height=15) as table:
        
        # Cabeçalho da Tabela
        row = table.row()
        header_style = FontFace(emphasis="BOLD", color=255, fill_color=(44, 62, 80))
        row.cell("FOTO", style=header_style)
        row.cell("CÓDIGO", style=header_style)
        row.cell("DESCRIÇÃO", style=header_style)
        row.cell("PREÇO", style=header_style)
        
        # Dados
        pdf.set_font("helvetica", size=9)
        
        for idx, item in df_itens.iterrows():
            row = table.row()
            
            # 1. FOTO
            img_inserida = False
            try:
                # Pega nome da imagem do banco original
                nome_arq = df_completo.loc[df_completo["codigo"] == item["codigo"], "imagem"].values[0]
                caminho_img = os.path.join(PASTA_IMAGENS, str(nome_arq))
                
                if os.path.exists(caminho_img):
                    # img_fill_width=True força a imagem a ter 15mm de largura
                    # Como definimos a linha com 15mm de altura, fica quadrado perfeito.
                    row.cell(img=caminho_img, img_fill_width=True)
                    img_inserida = True
            except:
                pass
            
            if not img_inserida:
                row.cell("-")

            # 2. CÓDIGO
            cod_limpo = str(item['codigo']).replace("AUTO-", "")
            row.cell(cod_limpo, align="C") # Centralizado verticalmente pelo fpdf
            
            # 3. DESCRIÇÃO
            ean = item['barras'] if str(item['barras']) != "nan" else ""
            txt_desc = f"{item['nome']}\nEAN: {ean}"
            row.cell(txt_desc)
            
            # 4. PREÇO
            txt_preco = f"R$ {item[tabela_col]:,.2f}"
            row.cell(txt_preco, style=FontFace(emphasis="BOLD"))

    # --- OBSERVAÇÕES ---
    pdf.ln(5)
    pdf.set_font("helvetica", 'I', 8)
    pdf.multi_cell(0, 5, f"Obs: {obs if obs else 'Sujeito a alteração sem aviso prévio.'}")
    
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
        
        st.write("1. Selecione os produtos:")
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
            st.markdown("### 2. Confira (Preview Simplificado):")
            
            # PREVIEW HTML LIMPO (RESOLVE O PROBLEMA DOS "2 CÓDIGOS")
            for i, row in selecionados.iterrows():
                # Tenta achar imagem para preview
                img_tag = ""
                try:
                    nome_arq = df.loc[df["codigo"] == row["codigo"], "imagem"].values[0]
                    caminho_img = os.path.join(PASTA_IMAGENS, str(nome_arq))
                    if os.path.exists(caminho_img):
                        with open(caminho_img, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        img_tag = f'<img src="data:image/jpeg;base64,{b64}" class="card-img">'
                except: pass
                
                # HTML CARD
                st.markdown(f"""
                <div class="card-produto">
                    {img_tag}
                    <div class="card-body">
                        <div class="card-title">{row['nome']}</div>
                        <div class="card-sub">Cód: {row['codigo']}</div>
                    </div>
                    <div class="card-price">R$ {row[tabela_ativa]:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            
            # GERAR PDF
            try:
                pdf_bytes = gerar_pdf_final(selecionados, cliente, obs, tabela_ativa, df)
                
                st.download_button(
                    label="📥 BAIXAR PDF CORRIGIDO",
                    data=bytes(pdf_bytes),
                    file_name=f"Pedido_{cliente}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")

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
