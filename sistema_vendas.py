import streamlit as st
import pandas as pd
import os

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(layout="wide", page_title="Fantini Sales System")
ARQUIVO_DB = "meus_produtos.csv"

# --- FUNÇÕES DE "BANCO DE DADOS" (Sem SQL, apenas arquivo local) ---
def carregar_dados():
    if not os.path.exists(ARQUIVO_DB):
        # Se não existe arquivo, cria dados iniciais de exemplo
        dados_iniciais = [
            {"sku": "JBL-01", "produto": "Caixa JBL Boombox 3", "imagem_url": "https://m.media-amazon.com/images/I/61s+N9j+bCL._AC_SL1000_.jpg", "custo_base": 1200.00, "moeda_base": "BRL"},
            {"sku": "PIO-12", "produto": "Subwoofer Pioneer 12 pol", "imagem_url": "https://m.media-amazon.com/images/I/61bM8f5iVvL._AC_SL1000_.jpg", "custo_base": 85.00, "moeda_base": "USD"},
            {"sku": "INT-CAM", "produto": "Câmera Intelbras iM3", "imagem_url": "https://m.media-amazon.com/images/I/61O0N9y+YLL._AC_SL1500_.jpg", "custo_base": 250.00, "moeda_base": "BRL"},
        ]
        df = pd.DataFrame(dados_iniciais)
        df.to_csv(ARQUIVO_DB, index=False)
        return df
    else:
        return pd.read_csv(ARQUIVO_DB)

def salvar_dados(df):
    df.to_csv(ARQUIVO_DB, index=False)
    st.toast("✅ Alterações salvas com sucesso!", icon="💾")

# Carrega os dados na memória ao abrir
if "df_produtos" not in st.session_state:
    st.session_state["df_produtos"] = carregar_dados()

df = st.session_state["df_produtos"]

# --- INTERFACE ---
st.title("🚀 Fantini - Sistema de Formação de Preço")

tab_vitrine, tab_cadastro = st.tabs(["💎 Vitrine & Preços (Simulador)", "📝 Cadastro de Produtos"])

# ==============================================================================
# ABA 1: VITRINE (A Mágica dos Cálculos)
# ==============================================================================
with tab_vitrine:
    # 1. Painel de Controle (Variáveis Globais)
    with st.container():
        st.markdown("### 🎛️ Painel de Variáveis")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            dolar = st.number_input("💵 Dólar Hoje (R$)", value=5.60, step=0.01, format="%.2f")
        with col2:
            imposto = st.number_input("🏛️ Impostos Totais (%)", value=12.0, step=0.5)
        with col3:
            margem = st.slider("📈 Margem de Lucro (%)", 0, 100, 35)
        with col4:
            desconto = st.toggle("Aplicar Desconto Pix (5%)")

    st.divider()

    # 2. Lógica de Cálculo
    # Cria uma cópia para não estragar os dados originais
    df_calc = df.copy()

    # Normaliza tudo para BRL
    # Se a moeda base for USD, multiplica pelo dolar. Se for BRL, mantém.
    df_calc["custo_reais"] = df_calc.apply(
        lambda x: x["custo_base"] * dolar if x["moeda_base"] == "USD" else x["custo_base"], axis=1
    )

    # Aplica Imposto + Margem
    df_calc["preco_venda"] = df_calc["custo_reais"] * (1 + imposto/100) * (1 + margem/100)

    # Aplica Desconto se ativado
    if desconto:
        df_calc["preco_final"] = df_calc["preco_venda"] * 0.95
    else:
        df_calc["preco_final"] = df_calc["preco_venda"]

    # 3. Exibição Visual
    st.subheader(f"Catálogo Atualizado ({len(df_calc)} itens)")
    
    column_config_vitrine = {
        "imagem_url": st.column_config.ImageColumn("Foto", width="small"),
        "sku": st.column_config.TextColumn("Ref."),
        "produto": st.column_config.TextColumn("Descrição", width="large"),
        "custo_base": st.column_config.NumberColumn("Custo Base", format="%.2f"),
        "moeda_base": st.column_config.TextColumn("Moeda", width="small"),
        # Oculta calculos intermediarios
        "custo_reais": None, 
        "preco_venda": None,
        # Destaque
        "preco_final": st.column_config.NumberColumn(
            "PREÇO FINAL (R$)", 
            format="R$ %.2f",
            help="Preço calculado com as variáveis atuais"
        )
    }

    st.dataframe(
        df_calc[["imagem_url", "sku", "produto", "custo_base", "moeda_base", "preco_final"]],
        column_config=column_config_vitrine,
        use_container_width=True,
        hide_index=True,
        height=600
    )

# ==============================================================================
# ABA 2: CADASTRO (Edição direta)
# ==============================================================================
with tab_cadastro:
    st.info("💡 Adicione, edite ou remova produtos aqui. As alterações vão para a Vitrine automaticamente.")
    
    column_config_editor = {
        "imagem_url": st.column_config.TextColumn("URL da Imagem", help="Cole o link da imagem aqui"),
        "sku": st.column_config.TextColumn("Código SKU", required=True),
        "produto": st.column_config.TextColumn("Nome do Produto", required=True),
        "custo_base": st.column_config.NumberColumn("Custo de Fábrica", min_value=0.0, format="%.2f"),
        "moeda_base": st.column_config.SelectboxColumn("Moeda do Custo", options=["BRL", "USD"], required=True)
    }

    # Editor de dados (permite adicionar linhas)
    df_editado = st.data_editor(
        df,
        column_config=column_config_editor,
        num_rows="dynamic", # Permite adicionar novas linhas
        use_container_width=True,
        hide_index=True,
        key="editor_dados"
    )

    # Botão Salvar
    if st.button("💾 Gravar Alterações", type="primary"):
        st.session_state["df_produtos"] = df_editado # Atualiza sessão
        salvar_dados(df_editado) # Atualiza arquivo físico
        st.rerun() # Recarrega para atualizar a Vitrine