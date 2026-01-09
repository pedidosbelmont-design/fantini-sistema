import streamlit as st
import streamlit.components.v1 as components # Necessário para o botão de imprimir
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

# --- FUNÇÃO THUMBNAIL ---
def get_thumbnail_as_base64(file_path):
    if not os.path.exists(file_path): return None
    try:
        img = Image.open(file_path)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.thumbnail((100, 100)) 
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=80)
        return base64.b64encode(buffered.getvalue()).decode()
    except: return None

# --- CSS DEFINITIVO ---
st.markdown("""
<style>
    .stApp { background-color: #eaeff2; }
    
    /* FOLHA A4 */
    .folha-a4 {
        background: white;
        width: 210mm; min-height: 297mm;
        margin: 20px auto; padding: 15mm;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        font-family: Arial, sans-serif;
    }
    
    /* CABEÇALHO */
    .header-box {
        display: flex; justify-content: space-between; align-items: flex-end;
        border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px;
    }
    
    /* TABELA */
    .tabela-clean {
        width: 100%; border-collapse: collapse;
    }
    .tabela-clean th {
        background: #2c3e50 !important; color: white !important;
        padding: 8px; text-align: left; font-size: 12px;
        -webkit-print-color-adjust: exact;
    }
    .tabela-clean td {
        padding: 8px; border-bottom: 1px solid #ccc;
        font-size: 12px; color: #000; vertical-align: middle;
    }
    .tabela-clean tr:nth-child(even) { background: #f9f9f9 !important; -webkit-print-color-adjust: exact; }

    /* IMAGEM */
    .img-thumb { width: 50px; height: 50px; object-fit: contain; display: block; }

    /* IMPRESSÃO (CTRL+P) */
    @media print {
        body { background: white; }
        [data-testid="stSidebar"], [data-testid="stHeader"], .stTabs, .stButton, footer, .no-print { display: none !important; }
        .block-container { padding: 0 !important; margin: 0 !important; }
        .folha-a4 { margin: 0; box-shadow: none; border: none; width: 100%; }
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

tab_gerador, tab_cadastro, tab_config = st.tabs(["📄 Gerador A4", "📝 Cadastro", "⚙️ Tabelas"])

# --- ABA 1: GERADOR A4 ---
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
            # BOTÃO DE IMPRESSÃO VIA JAVASCRIPT
            st.markdown("---")
            col_print, col_info = st.columns([1, 4])
            with col_print:
                # Esse botão aciona o Ctrl+P automaticamente
                if st.button("🖨️ IMPRIMIR / PDF", type="primary"):
                    components.html("<script>window.print()</script>", height=0, width=0)
            
            # GERAÇÃO HTML
            logo_html = "<h2>FANTINI</h2>"
            if logo_path:
                b64_logo = get_thumbnail_as_base64(logo_path)
                if b64_logo: logo_html = f'<img src="data:image/jpeg;base64,{b64_logo}" style="max-height:60px">'
            
            data_hoje = datetime.now().strftime("%d/%m/%Y")
            
            html_content = f"""
            <div class="folha-a4">
                <div class="header-box">
                    <div>{logo_html}<br><small>Representação Comercial</small></div>
                    <div style="text-align:right">
                        <h3>TABELA DE PREÇOS</h3>
                        <div>Tabela: <strong>{tabela_ativa}</strong></div>
                        <div>Data: {data_hoje}</div>
                        <div>Cliente: <strong>{cliente}</strong></div>
                    </div>
                </div>
                <table class="tabela-clean">
                    <thead><tr>
                        <th width="60">Foto</th>
                        <th>Cód</th>
                        <th>Produto</th>
                        <th style="text-align:right">Preço</th>
                    </tr></thead>
                    <tbody>
            """
            
            for i, row in selecionados.iterrows():
                img_cell = "<span style='color:#ccc; font-size:10px'>S/ FOTO</span>"
                try:
                    full_row = df[df["codigo"] == row["codigo"]].iloc[0]
                    path_img = os.path.join(PASTA_IMAGENS, str(full_row["imagem"]))
                    b64_prod = get_thumbnail_as_base64(path_img)
                    if b64_prod: img_cell = f'<img src="data:image/jpeg;base64,{b64_prod}" class="img-thumb">'
                except: pass

                cod = row['codigo']
                if "AUTO-" in str(cod): cod = ""
                
                html_content += "<tr>"
                html_content += f"<td align='center'>{img_cell}</td>"
                html_content += f"<td><b>{cod}</b></td>"
                html_content += f"<td>{row['nome']}</td>"
                html_content += f"<td align='right'><b>R$ {row[tabela_ativa]:,.2f}</b></td>"
                html_content += "</tr>"

            html_content += f"""
                    </tbody>
                </table>
                <div style="margin-top:20px; text-align:center; font-size:11px; color:#666; border-top:1px solid #ddd; padding-top:5px">
                    {obs if obs else 'Sujeito a alteração.'}
                </div>
            </div>
            """
            st.markdown(html_content, unsafe_allow_html=True)
            
            # GUIA VISUAL DE IMPRESSÃO (PARA NÃO ESQUECER)
            st.markdown("""
            <div class="no-print" style="margin-top:20px; background:#e3f2fd; padding:15px; border-radius:8px; border:1px solid #90caf9;">
                <h4 style="margin:0; color:#1565c0 !important;">📝 Como Salvar em PDF:</h4>
                <ol style="margin-top:5px; color:#333;">
                    <li>Clique no botão <b>Imprimir</b> acima ou aperte <b>Ctrl + P</b>.</li>
                    <li>Em "Destino", escolha <b>Salvar como PDF</b>.</li>
                    <li><b>IMPORTANTE:</b> Vá em "Mais definições" e marque a caixinha <b>☑️ Gráficos de segundo plano</b>.</li>
                    <li>Clique em Salvar!</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)

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