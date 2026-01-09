import streamlit as st
import pandas as pd
import os
import time
import base64
import io
from datetime import datetime
from PIL import Image # Mantemos para a logo do cabeçalho

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

# --- FUNÇÃO PARA A LOGO DO CABEÇALHO ---
def get_img_as_base64_resized(file_path):
    """Lê e redimensiona apenas a logo principal para o cabeçalho."""
    if os.path.exists(file_path):
        try:
            img = Image.open(file_path)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            # Redimensiona para logo pequena
            img.thumbnail((200, 100)) 
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=80)
            encoded = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{encoded}"
        except Exception:
            return None
    return None

# --- CSS PROFISSIONAL PARA IMPRESSÃO ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    h1, h2, h3, p, div, span, label { color: #1c1e21 !important; }

    /* --- FOLHA A4 --- */
    .folha-a4-preview {
        background-color: white;
        width: 100%;
        max-width: 210mm;
        margin: 20px auto;
        padding: 15mm;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }

    /* --- CABEÇALHO --- */
    .header-tabela {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        border-bottom: 3px solid #2c3e50;
        padding-bottom: 20px;
        margin-bottom: 30px;
    }
    .titulo-tabela { font-size: 22px; font-weight: bold; color: #2c3e50; margin: 0; text-transform: uppercase; }
    .subtitulo-tabela { font-size: 14px; color: #555; margin-top: 5px; }

    /* --- TABELA LIMPA (SEM FOTOS) --- */
    .tabela-produtos {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', sans-serif;
    }
    .tabela-produtos th {
        background-color: #34495e !important;
        color: white !important;
        padding: 12px 10px; /* Mais espaçamento */
        text-align: left;
        font-size: 12px;
        text-transform: uppercase;
        -webkit-print-color-adjust: exact; 
        print-color-adjust: exact;
    }
    .tabela-produtos td {
        padding: 10px;
        border-bottom: 1px solid #eee;
        vertical-align: middle;
        color: #333;
        font-size: 13px;
    }
    .tabela-produtos tr:nth-child(even) {
        background-color: #f9f9f9 !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }

    /* --- DADOS --- */
    .prod-nome { font-weight: bold; font-size: 14px; margin-bottom: 4px; }
    .prod-ean { font-size: 11px; color: #777; }
    .prod-cod { font-weight: bold; color: #555; font-size: 12px; }
    .prod-preco { font-weight: bold; font-size: 16px; color: #2c3e50; }

    /* --- IMPRESSÃO --- */
    @media print {
        [data-testid="stSidebar"], [data-testid="stHeader"], .stTabs, .stButton, .stAlert, footer, .no-print {
            display: none !important;
        }
        .block-container { padding: 0 !important; margin: 0 !important; }
        .folha-a4-preview {
            box-shadow: none; border: none; padding: 0; margin: 0;
            width: 100%; max-width: none;
        }
        tr { page-break-inside: avoid; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. GERENCIAMENTO DE DADOS ---
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
        return False, "⚠️ Este código já existe!"

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
    if nome not in df.columns: df[nome] = 0.0; salvar_dados(df); return True, "Tabela criada!"
    return False, "Já existe."

def excluir_categoria(nome):
    df = carregar_dados()
    if nome in df.columns and nome not in COLUNAS_FIXAS: df = df.drop(columns=[nome]); salvar_dados(df); return True, "Removida."
    return False, "Erro."

# --- 3. APP PRINCIPAL ---
inicializar()
if "edit_codigo" not in st.session_state: st.session_state["edit_codigo"] = None

df = carregar_dados()
colunas_de_preco = [c for c in df.columns if c not in COLUNAS_FIXAS]

# --- SIDEBAR ---
with st.sidebar:
    caminhos_logo = [os.path.join(PASTA_IMAGENS, x) for x in ["logo.png", "logo.jpg", "Logo.png"]]
    path_logo_fantini = next((c for c in caminhos_logo if os.path.exists(c)), None)
    if path_logo_fantini: st.image(path_logo_fantini, use_container_width=True)
    
    st.header("Configuração")
    filtro_fabrica = st.selectbox("1. Fabricante:", ["Todos"] + EMPRESAS)
    
    tabela_selecionada = None
    if colunas_de_preco:
        tabela_selecionada = st.selectbox("2. Tabela de Preço:", colunas_de_preco)
    else:
        st.warning("Crie uma tabela na aba Ajustes.")
    
    st.divider()
    st.info("Vá para a aba 'Gerador PDF' para ver o resultado.")

# --- ABAS ---
tab_gerador, tab_cadastro, tab_config = st.tabs(["📄 Gerador PDF", "📝 Cadastro Produtos", "⚙️ Ajustes"])

# ABA 1: GERADOR (AGORA SEM FOTOS NA TABELA)
with tab_gerador:
    df_filtrado = df.copy()
    if filtro_fabrica != "Todos":
        df_filtrado = df_filtrado[df_filtrado["fabricante"] == filtro_fabrica]
    
    if df_filtrado.empty:
        st.warning("Nenhum produto encontrado.")
    elif not tabela_selecionada:
        st.info("Selecione uma tabela de preços.")
    else:
        st.markdown("### Seleção de Produtos")
        df_filtrado.insert(0, "Incluir", False)
        
        colunas_visiveis = ["Incluir", "codigo", "nome", "barras", tabela_selecionada]
        df_edicao = st.data_editor(
            df_filtrado[colunas_visiveis],
            hide_index=True,
            column_config={
                "Incluir": st.column_config.CheckboxColumn("Selecionar", default=False),
                tabela_selecionada: st.column_config.NumberColumn("Preço", format="R$ %.2f"),
                "codigo": st.column_config.TextColumn("Cód."),
            },
            disabled=["codigo", "nome", "barras", tabela_selecionada],
            use_container_width=True,
            height=300
        )
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        cliente_nome = c1.text_input("Nome do Cliente:", placeholder="Ex: Mercado Central")
        observacao = c2.text_input("Observação:", placeholder="Ex: Promoção válida até sexta.")

        itens_marcados = df_edicao[df_edicao["Incluir"] == True]
        
        if not itens_marcados.empty:
            # 1. Logo Fantini do Cabeçalho (Mantida)
            img_logo_b64 = ""
            if path_logo_fantini:
                res = get_img_as_base64_resized(path_logo_fantini)
                if res: img_logo_b64 = res

            # 2. Linhas da Tabela (SEM FOTOS AGORA)
            html_rows = ""
            for idx, row in itens_marcados.iterrows():
                cod_show = row['codigo'] if not str(row['codigo']).startswith("AUTO-") else "---"
                ean_show = f"EAN: {row['barras']}" if row['barras'] and str(row['barras']) != "nan" else ""
                preco = row[tabela_selecionada]

                html_rows += f"""
                <tr>
                    <td class='prod-cod' style='padding-left:15px;'>{cod_show}</td>
                    <td>
                        <div class='prod-nome'>{row['nome']}</div>
                        <div class='prod-ean'>{ean_show}</div>
                    </td>
                    <td style='text-align:right; padding-right:15px;' class='prod-preco'>R$ {preco:,.2f}</td>
                </tr>
                """

            data_hoje = datetime.now().strftime("%d/%m/%Y")
            titulo_extra = f" - {filtro_fabrica}" if filtro_fabrica != "Todos" else ""
            logo_html = f'<img src="{img_logo_b64}" style="max-height:70px;">' if img_logo_b64 else '<h2>FANTINI</h2>'

            html_final = f"""
            <div class="folha-a4-preview">
                <div class="header-tabela">
                    <div>
                        {logo_html}
                        <div style="color:#666; font-size:12px; margin-top:5px;">Representação Comercial</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="titulo-tabela">Tabela de Preços{titulo_extra}</div>
                        <div class="subtitulo-tabela">Condição: <strong>{tabela_selecionada}</strong></div>
                        <div class="subtitulo-tabela">Data: {data_hoje}</div>
                        {f'<div style="margin-top:5px; font-weight:bold; color:#2c3e50;">Cliente: {cliente_nome}</div>' if cliente_nome else ''}
                    </div>
                </div>
                
                <table class="tabela-produtos">
                    <thead>
                        <tr>
                            <th width="100px" style="padding-left:15px;">Código</th>
                            <th>Produto / EAN</th>
                            <th width="140px" style="text-align:right; padding-right:15px;">Valor Unit.</th>
                        </tr>
                    </thead>
                    <tbody>
                        {html_rows}
                    </tbody>
                </table>
                
                <div style="margin-top:40px; border-top:1px solid #ccc; padding-top:10px; font-size:11px; color:#666; text-align:center;">
                    {observacao if observacao else 'Documento gerado pelo Sistema Fantini. Sujeito a alteração.'}
                </div>
            </div>
            """
            st.markdown(html_final, unsafe_allow_html=True)
            st.markdown("""
                <div class='no-print' style='margin-top:20px; background-color:#e8f5e9; color:#1b5e20; padding:15px; border-radius:8px; text-align:center;'>
                    <strong>🖨️ Pronto!</strong> Pressione <b>Ctrl + P</b> > Salvar como PDF.
                    <br><small>Marque "Gráficos de plano de fundo" para sair colorido.</small>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Selecione pelo menos um produto.")

# ABA 2: CADASTRO
with tab_cadastro:
    c1, c2 = st.columns([2, 1])
    with c2:
        st.markdown("##### Buscar Produto")
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
        
        titulo = f"✏️ Editando: {dados['nome']}" if dados is not None else "➕ Novo Produto"
        st.markdown(f"##### {titulo}")
        if dados is not None and st.button("Cancelar"): st.session_state["edit_codigo"] = None; st.rerun()
        
        with st.container(border=True):
            fab_idx = 0
            if dados is not None and dados["fabricante"] in EMPRESAS:
                fab_idx = EMPRESAS.index(dados["fabricante"])
            
            fabricante = st.selectbox("Fabricante", EMPRESAS, index=fab_idx)
            nome = st.text_input("Nome *", value=dados["nome"] if dados is not None else "")
            
            c_a, c_b = st.columns(2)
            val_cod = dados["codigo"] if dados is not None else ""
            if str(val_cod).startswith("AUTO-"): val_cod = ""
            
            codigo = c_a.text_input("Cód. (Opcional)", value=val_cod, disabled=(dados is not None))
            barras = c_b.text_input("EAN", value=dados["barras"] if dados is not None else "")
            
            f_img = st.file_uploader("Foto", type=['jpg','png'])
            if dados is not None and not f_img: st.caption(f"Imagem atual: {dados['imagem']}")
            
            st.divider()
            if colunas_de_preco:
                st.write("💰 **Preços:**")
                precos = {}
                for col in colunas_de_preco:
                    val = float(dados[col]) if dados is not None else 0.0
                    precos[col] = st.number_input(f"{col} (R$)", value=val)
                
                c_save, c_del = st.columns(2)
                if c_save.button("💾 Salvar", type="primary", use_container_width=True):
                    cod_final = codigo
                    if dados is not None and not codigo: cod_final = dados["codigo"]
                    if nome:
                        ok, msg = salvar_produto(cod_final, barras, nome, fabricante, f_img, precos, modo_edicao=(dados is not None))
                        if ok: st.success(msg); st.session_state["edit_codigo"] = None; time.sleep(1); st.rerun()
                        else: st.error(msg)
                    else: st.warning("Nome obrigatório.")
                
                if dados is not None and c_del.button("🗑️ Excluir", use_container_width=True):
                    excluir_produto(dados["codigo"]); st.session_state["edit_codigo"] = None; st.success("Excluído!"); time.sleep(1); st.rerun()
            else: st.warning("Cadastre tabelas na aba 'Ajustes' primeiro.")

# ABA 3: AJUSTES (CORRIGIDA)
with tab_config:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Criar Tabela")
        new = st.text_input("Nome")
        if st.button("Criar", use_container_width=True):
             if new:
                 ok, m = criar_categoria(new)
                 if ok: st.success(m); time.sleep(0.5); st.rerun()
             else: st.warning("Digite um nome.")
    with c2:
        st.markdown("##### Apagar Tabela")
        if colunas_de_preco:
            dele = st.selectbox("Selecione:", colunas_de_preco)
            if st.button("Apagar", use_container_width=True):
                ok, m = excluir_categoria(dele)
                if ok: st.warning(m); time.sleep(0.5); st.rerun()
        else: st.info("Nenhuma tabela.")