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
# Removemos o background global para corrigir o erro dos campos invisíveis
st.markdown("""
<style>
    /* Card do Produto no Preview (Forçamos cores para garantir contraste) */
    .card-produto {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .card-img {
        width: 50px;
        height: 50px;
        object-fit: contain;
        border-radius: 4px;
        border: 1px solid #eee;
        margin-right: 15px;
        background-color: white;
    }
    .card-body { flex: 1; }
    /* Textos do card forçados para preto para não sumir no modo dark */
    .card-title { font-weight: bold; font-size: 14px; color: #000 !important; margin: 0; }
    .card-sub { font-size: 11px; color: #555 !important; margin-top: 2px; }
    .card-price { font-weight: bold; font-size: 16px; color: #2e7d32 !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. CLASSE PDF (LAYOUT AJUSTADO) ---
class PDF(FPDF):
    def header(self):
        # Logo
        logo_path = None
        for ext in ["png", "jpg"]:
            if os.path.exists(f"static/logo.{ext}"): logo_path = f"static/logo.{ext}"
        
        if logo_path:
            # x=10, y=10, w=30 (Aumentei um pouco o Y para descer a logo)
            self.image(logo_path, 10, 10, 30) 
        
        # Título
        self.set_y(18) # Desci o título para alinhar com a logo
        self.set_font('helvetica', 'B', 15)
        self.cell(45) # Pula a largura da logo
        self.cell(0, 10, 'FANTINI REPRESENTAÇÕES', ln=False)
        self.ln(25) # Quebra de linha maior para afastar do conteúdo

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Pag. {self.page_no()}/{{nb}}', align='C')

def gerar_pdf_final(df_itens, cliente, obs, tabela_col, df_completo):
    # PDF SETUP
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # --- CABEÇALHO CINZA (POSICIONAMENTO NOVO) ---
    # Antes estava em Y=30. Mudei para Y=45 para não cobrir a logo.
    y_inicio_box = 45 
    
    pdf.set_fill_color(240, 240, 240)
    # x=10, y=45, w=190, h=25
    pdf.rect(10, y_inicio_box, 190, 25, 'F')
    
    # Textos dentro da caixa cinza
    pdf.set_y(y_inicio_box + 2) 
    pdf.set_x(15)
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(0, 5, f"TABELA: {tabela_col.upper()}", ln=True)
    
    pdf.set_x(15)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 5, f"CLIENTE: {cliente}", ln=True)
    
    pdf.set_x(15)
    pdf.cell(0, 5, f"DATA: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    
    # Espaço para começar a tabela (pula a caixa cinza)
    pdf.set_y(y_inicio_box + 30) 
    
    # --- TABELA DE PRODUTOS ---
    w_foto = 15
    w_cod = 25
    w_desc = 110
    w_preco = 40
    col_widths = (w_foto, w_cod, w_desc, w_preco)
    
    # line_height=15 garante espaço vertical para a foto
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
                nome_arq = df_completo.loc[df_completo["codigo"] == item["codigo"], "imagem"].values[0]
                caminho_img = os.path.join(PASTA_IMAGENS, str(nome_arq))
                
                if os.path.exists(caminho_img):
                    # img_fill_width=True força largura 15mm
                    row.cell(img=caminho_img, img_fill_width=True)
                    img_inserida = True
            except:
                pass
            
            if not img_inserida:
                row.cell("-")

            # 2. CÓDIGO
            cod_limpo = str(item['codigo']).replace("AUTO-", "")
            row.cell(cod_limpo, align="C")
            
            # 3. DESCRIÇÃO
            ean = item['barras'] if str(item['barras']) != "nan" else ""
            txt_desc = f"{item['nome']}\nEAN: {ean}"
            row.cell(txt_desc)
            
            # 4. PREÇO
            txt_preco = f"R$ {item[tabela_col]:,.2f}"
            row.cell(txt_preco, style=FontFace(emphasis="BOLD"))

    # --- RODAPÉ OBS ---
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
            st.markdown("### 2. Confira (Preview):")
            
            for i, row in selecionados.iterrows():
                # Preview Imagem
                img_tag = ""
                try:
                    nome_arq = df.loc[df["codigo"] == row["codigo"], "imagem"].values[0]
                    caminho_img = os.path.join(PASTA_IMAGENS, str(nome_arq))
                    if os.path.exists(caminho_img):
                        with open(caminho_img, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        img_tag = f'<img src="data:image/jpeg;base64,{b64}" class="card-img">'
                except: pass
                
                # HTML Card Seguro
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
                st.error(f"Erro ao gerar PDF: {e}")

# --- ABA 2: CADASTRO ---
with tab_cadastro:
    # Ajuste de Layout para melhorar visibilidade
    c1, c2 = st.columns([2, 1])
    
    with c2:
        st.info("🔍 **Buscar Produto**")
        opcoes = df["codigo"].astype(str) + " | " + df["nome"]
        busca = st.selectbox("Selecione para Editar:", ["Novo"] + list(opcoes))
        if st.button("Carregar Dados", use_container_width=True):
            st.session_state["edit_codigo"] = busca.split(" | ")[0] if busca != "Novo" else None
            st.rerun()
            
    with c1:
        edit_cod = st.session_state["edit_codigo"]
        item = df[df["codigo"].astype(str) == str(edit_cod)].iloc[0] if edit_cod else None
        
        st.subheader(f"{'✏️ Editando: ' + item['nome'] if item is not None else '➕ Cadastrar Novo Produto'}")
        
        if item is not None:
            if st.button("Cancelar Edição", type="secondary"): 
                st.session_state["edit_codigo"] = None; st.rerun()
            
        with st.container(border=True):
            idx_fab = EMPRESAS.index(item["fabricante"]) if item is not None and item["fabricante"] in EMPRESAS else 0
            fab = st.selectbox("Fabricante:", EMPRESAS, index=idx_fab)
            nome = st.text_input("Nome do Produto *", value=item["nome"] if item is not None else "")
            
            cc1, cc2 = st.columns(2)
            val_cod = item["codigo"] if item is not None else ""
            if "AUTO-" in str(val_cod): val_cod = ""
            
            cod = cc1.text_input("Código Interno:", value=val_cod, disabled=(item is not None), placeholder="Deixe vazio p/ automático")
            ean = cc2.text_input("EAN / Barras:", value=item["barras"] if item is not None else "")
            
            file = st.file_uploader("Foto do Produto:", type=["jpg", "png"])
            if item is not None and not file: st.caption(f"Imagem atual: {item['imagem']}")
            
            st.markdown("---")
            if colunas_preco:
                st.write("💰 **Preços:**")
                precos = {}
                cols_p = st.columns(len(colunas_preco) if len(colunas_preco) < 4 else 3)
                for idx, cp in enumerate(colunas_preco):
                    with cols_p[idx % 3]: # Distribui em colunas
                        v = float(item[cp]) if item is not None else 0.0
                        precos[cp] = st.number_input(f"{cp} (R$)", value=v)
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 SALVAR PRODUTO", type="primary", use_container_width=True):
                    if not nome: st.warning("Nome obrigatório"); st.stop()
                    final_cod = cod if cod else (item["codigo"] if item is not None else f"AUTO-{int(time.time())}")
                    
                    if not item and str(final_cod) in df["codigo"].astype(str).values:
                        st.error("Código já existe!"); st.stop()

                    img_name = "sem_foto.png"
                    if item is not None:
                        # Remove antigo para salvar novo
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
                    st.success("✅ Produto Salvo!"); st.session_state["edit_codigo"] = None; st.rerun()
                
                if item is not None:
                    if st.button("🗑️ Excluir Produto", use_container_width=True):
                        df = df[df["codigo"].astype(str) != str(final_cod)]
                        df.to_csv(ARQUIVO_DB, index=False)
                        st.success("Produto Excluído!"); st.session_state["edit_codigo"] = None; st.rerun()

# --- ABA 3: TABELAS ---
with tab_config:
    c1, c2 = st.columns(2)
    with c1:
        n = st.text_input("Nova Tabela de Preço:")
        if st.button("Criar Tabela"):
            if n and n not in df.columns: 
                df[n] = 0.0; df.to_csv(ARQUIVO_DB, index=False); st.rerun()
    with c2:
        if colunas_preco:
            d = st.selectbox("Apagar Tabela:", colunas_preco)
            if st.button("Apagar Definitivamente"):
                df = df.drop(columns=[d]); df.to_csv(ARQUIVO_DB, index=False); st.rerun()
