import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path

# 1. Configurações Iniciais da Página
st.set_page_config(page_title="Dashboard Missões Espaciais", layout="wide", initial_sidebar_state="expanded")

# 2. Conexão e Carga de Dados (Com Fail-Safe / Tratamento de Exceções)
@st.cache_data
def carregar_dados():
    try:
        base_dir = Path(__file__).parent.parent
        caminho_db = base_dir / "database" / "Space_Corrected.db"
        
        # Fallback caso o dashboard seja executado na mesma pasta do banco
        if not caminho_db.exists():
            caminho_db = Path("database/Space_Corrected.db")
            if not caminho_db.exists():
                caminho_db = Path("Space_Corrected.db")
        
        if not caminho_db.exists():
            return None
            
        with sqlite3.connect(str(caminho_db)) as conn:
            df = pd.read_sql("SELECT * FROM missoes", conn)
            
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'], errors='coerce')
        df['ano'] = df['data_lancamento'].dt.year
        return df
    except Exception as e:
        return None

df_bruto = carregar_dados()

# Interrompe a execução graciosamente se o banco não existir
if df_bruto is None or df_bruto.empty:
    st.error("Base de dados não encontrada ou vazia. Execute o pipeline de engenharia (Jupyter Notebook) primeiro para gerar o arquivo Space_Corrected.db.")
    st.stop()

# 3. Motor de Formatação Financeira
def formatar_bi(valor, is_milhoes=True):
    if pd.isna(valor):
        return "$0,0"
    valor_absoluto = valor * 1_000_000 if is_milhoes else valor
    if valor_absoluto >= 1_000_000_000:
        return f"${valor_absoluto / 1_000_000_000:.1f}B".replace(".", ",")
    elif valor_absoluto >= 1_000_000:
        return f"${valor_absoluto / 1_000_000:.1f}M".replace(".", ",")
    elif valor_absoluto >= 1_000:
        return f"${valor_absoluto / 1_000:.1f}K".replace(".", ",")
    else:
        return f"${valor_absoluto:.1f}".replace(".", ",")

# 4. Configuração da Aba Lateral (Sidebar) e Filtros Dinâmicos
st.sidebar.markdown("### Navegação")
menu_selecionado = st.sidebar.radio(
    "",
    [
        "Visão Geral",
        "Financeiro e Sucesso",
        "Análise Geopolítica"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Filtros Dinâmicos")

# Filtro de Ano (Tratando possíveis NaNs com dropna antes de converter para int)
df_anos_validos = df_bruto.dropna(subset=['ano'])
min_ano = int(df_anos_validos['ano'].min())
max_ano = int(df_anos_validos['ano'].max())

anos_selecionados = st.sidebar.slider(
    "Período (Anos)",
    min_value=min_ano,
    max_value=max_ano,
    value=(min_ano, max_ano)
)

# Filtro de Status
status_disponiveis = df_bruto['status_missao'].dropna().unique().tolist()
status_selecionados = st.sidebar.multiselect(
    "Status da Missão",
    options=status_disponiveis,
    default=status_disponiveis
)

# Aplicação dos Filtros ao DataFrame Principal
df = df_bruto[
    (df_bruto['ano'] >= anos_selecionados[0]) &
    (df_bruto['ano'] <= anos_selecionados[1]) &
    (df_bruto['status_missao'].isin(status_selecionados))
].copy()

st.sidebar.markdown("---")
st.sidebar.caption("Pipeline Analítico: Data Quality Pro")

# Se o filtro remover todos os dados, avisa o usuário
if df.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# ==========================================
# PÁGINA 1: VISÃO GERAL
# ==========================================
if menu_selecionado == "Visão Geral":
    st.title("Visão Geral das Missões")
    
    st.markdown("### Métricas Principais")
    st.markdown("<br>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    total_missoes = len(df)
    sucesso = len(df[df["status_missao"] == "Sucesso"])
    
    c1.metric("Total de Missões", f"{total_missoes:,}".replace(",", "."))
    c2.metric("Empresas Envolvidas", df["empresa"].nunique())
    c3.metric("Missões Bem-sucedidas", f"{sucesso:,}".replace(",", "."))
    c4.metric("Taxa de Sucesso (Filtro)", f"{(sucesso/total_missoes)*100:.1f}%" if total_missoes > 0 else "0%")
    
    st.markdown("<hr style='margin-top: 2rem; margin-bottom: 2rem;'>", unsafe_allow_html=True)
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("#### Evolução do Volume de Lançamentos por Ano")
        df_ano = df.groupby("ano").agg(Quantidade=('status_missao', 'count')).reset_index()
        
        fig1 = px.area(
            df_ano,
            x="ano",
            y="Quantidade",
            template="plotly_white",
            labels={"ano": "Ano", "Quantidade": "Quantidade de Missões"}
        )
        fig1.update_layout(xaxis_title="", yaxis_title="Quantidade de Missões", margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig1, use_container_width=True)
        
    with col_g2:
        st.markdown("#### Top 10 Empresas (Volume de Lançamentos)")
        df_empresas = df.groupby("empresa").agg(
            Quantidade=('status_missao', 'count'),
            Paises_Operacao=('pais', 'nunique')
        ).reset_index().sort_values("Quantidade", ascending=False).head(10)
        
        fig2 = px.bar(
            df_empresas, x="Quantidade", y="empresa", orientation="h",
            template="plotly_white", color="Quantidade", color_continuous_scale="Teal",
            hover_data={"empresa": True, "Quantidade": True, "Paises_Operacao": True}
        )
        fig2.update_layout(yaxis={'categoryorder': 'total ascending'}, xaxis_title="Total de Missões", yaxis_title="", margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig2, use_container_width=True)

# ==========================================
# PÁGINA 2: FINANCEIRO E SUCESSO
# ==========================================
elif menu_selecionado == "Financeiro e Sucesso":
    st.title("Análise Financeira e de Sucesso")
    
    df_custo = df.dropna(subset=["custo_foguete"])
    df_sem_custo = df[df["custo_foguete"].isna() | (df["custo_foguete"] == 0)]
    
    custo_tot = df_custo["custo_foguete"].sum()
    custo_med = df_custo["custo_foguete"].mean()
    
    st.markdown("### Visão Geral Financeira")
    st.markdown("<br>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Investimento Total Catalogado", formatar_bi(custo_tot))
    c2.metric("Custo Médio por Lançamento", formatar_bi(custo_med))
    c3.metric("Missões com Custo Informado", f"{len(df_custo):,}".replace(",", "."))
    c4.metric("Missões SEM Custo Informado", f"{len(df_sem_custo):,}".replace(",", "."))
    
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🔍 Auditar Missões SEM Informação de Custo (Dados Omitidos/Confidenciais)"):
        st.warning(f"Existem {len(df_sem_custo)} missões neste período que não possuem registros financeiros públicos. Veja a listagem abaixo:")
        
        df_sem_custo_visao = df_sem_custo.copy().drop(columns=["pais_en"], errors="ignore")
        df_sem_custo_visao['data_lancamento'] = df_sem_custo_visao['data_lancamento'].dt.strftime('%Y-%m-%d')
        df_sem_custo_visao = df_sem_custo_visao.drop(columns=["custo_foguete"], errors="ignore")
        
        st.dataframe(df_sem_custo_visao, use_container_width=True, hide_index=True)
   
    st.markdown("<hr style='margin-top: 2rem; margin-bottom: 2rem;'>", unsafe_allow_html=True)
    col_g3, col_g4 = st.columns(2)
   
    with col_g3:
        st.markdown("#### Investimento Financeiro Consolidado por Ano")
        df_custo_ano = df_custo.groupby("ano")["custo_foguete"].sum().reset_index()
        fig3 = px.line(df_custo_ano, x="ano", y="custo_foguete", markers=True, template="plotly_white")
        fig3.update_traces(line_color="#2b5c8f", line_width=3, marker=dict(size=8))
        fig3.update_layout(xaxis_title="", yaxis_title="Investimento (Mi USD)", margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig3, use_container_width=True)
        
    with col_g4:
        st.markdown("#### Distribuição do Status das Missões")
        df_status = df["status_missao"].value_counts().reset_index()
        df_status.columns = ["Status", "Quantidade"]
        fig4 = px.bar(df_status, x="Quantidade", y="Status", orientation="h", template="plotly_white", color="Status")
        fig4.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False, xaxis_title="Quantidade de Missões", yaxis_title="", margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig4, use_container_width=True)

# ==========================================
# PÁGINA 3: ANÁLISE GEOPOLÍTICA
# ==========================================
elif menu_selecionado == "Análise Geopolítica":
    st.title("Análise Geopolítica")
    st.markdown("Insights sobre a operação e infraestrutura aeroespacial segmentados por país sede.")
   
    # Mapa de tradução robusto integrado às correções feitas no banco
    mapa_traducao = {
        "Estados Unidos": "United States", "USA": "United States",
        "Rússia": "Russia", "Brasil": "Brazil", "França": "France",
        "Japão": "Japan", "Índia": "India", "Cazaquistão": "Kazakhstan",
        "Coreia do Sul": "South Korea", "Coreia do Norte": "North Korea",
        "Nova Zelândia": "New Zealand", "Irã": "Iran", "China": "China",
        "Israel": "Israel", "Reino Unido": "United Kingdom", "Itália": "Italy",
        "Austrália": "Australia", "Ilhas Marshall": "Marshall Islands", "Quênia": "Kenya"
    }
   
    df["pais_en"] = df["pais"].map(lambda x: mapa_traducao.get(x, x))
   
    df_pais = df.groupby(["pais", "pais_en"]).agg(
        Quantidade=('status_missao', 'count'),
        Bases_Ativas=('base_lancamento', 'nunique'),
        Empresas=('empresa', 'nunique')
    ).reset_index()
   
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Total de Lançamentos por País")
   
    fig_map = px.choropleth(
        df_pais,
        locations="pais_en",
        locationmode="country names",
        color="Quantidade",
        hover_name="pais",
        hover_data={"pais_en": False, "pais": False, "Quantidade": True, "Bases_Ativas": True, "Empresas": True},
        color_continuous_scale="Blues",
        projection="natural earth",
        template="plotly_white"
    )
   
    fig_map.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        geo=dict(showframe=False, showcoastlines=True, coastlinecolor="LightGray"),
        coloraxis_colorbar=dict(title="Lançamentos", thicknessmode="pixels", thickness=15, lenmode="pixels", len=200, yanchor="middle", y=0.5, xanchor="left", x=1.0)
    )
    st.plotly_chart(fig_map, use_container_width=True)
   
    st.markdown("<hr style='margin-top: 2rem; margin-bottom: 2rem;'>", unsafe_allow_html=True)
    st.markdown("#### Top 10 Países (Volume de Lançamentos)")
   
    df_pais_top = df_pais.sort_values("Quantidade", ascending=False).head(10).sort_values("Quantidade", ascending=True)
    fig_bar_pais = px.bar(
        df_pais_top, x="Quantidade", y="pais", orientation="h",
        template="plotly_white", color="Quantidade", color_continuous_scale="Blues",
        hover_data={"pais": True, "Quantidade": True, "Bases_Ativas": True}
    )
    fig_bar_pais.update_layout(xaxis_title="", yaxis_title="", margin=dict(t=20, b=20, l=0, r=0))
    st.plotly_chart(fig_bar_pais, use_container_width=True)

# ==========================================
# MÓDULO COMUM: EXPORTAÇÃO E DADOS BRUTOS
# ==========================================
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("Ver Dados Brutos e Exportar (Baseado nos filtros atuais)"):
   
    df_visao = df.copy()
    df_visao = df_visao.drop(columns=["pais_en"], errors="ignore")
   
    df_visao['data_lancamento'] = df_visao['data_lancamento'].dt.strftime('%Y-%m-%d')
   
    colunas_originais = df_visao.columns.tolist()
    if 'data_lancamento' in colunas_originais and 'hora_lancamento' in colunas_originais:
        colunas_originais.remove('hora_lancamento')
        idx_data = colunas_originais.index('data_lancamento')
        colunas_originais.insert(idx_data + 1, 'hora_lancamento')
        df_visao = df_visao[colunas_originais]
       
    st.dataframe(df_visao, use_container_width=True, hide_index=True)
   
    csv = df_visao.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Baixar Dados Filtrados (CSV)",
        data=csv,
        file_name='missoes_espaciais_filtradas.csv',
        mime='text/csv',
        key="btn_download_dados_filtrados"
    )