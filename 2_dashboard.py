import pandas as pd
import plotly.express as px
import streamlit as st

# --- Configuração da página ---
st.set_page_config(page_title="Churn CS", layout="wide")

# --- Carregamento dos dados ---
df_completo = pd.read_csv("dados/churn_processado.csv")

# --- Título e subtítulo ---
st.title("Análise de Churn — Customer Success")

total_clientes = len(df_completo)
taxa_geral = df_completo["churn_num"].mean() * 100
st.markdown(f"**{total_clientes:,} clientes analisados** — Taxa de churn geral: **{taxa_geral:.1f}%**")

# --- Barra lateral com filtros ---
with st.sidebar:
    st.header("Filtros")

    contratos_disponiveis = sorted(df_completo["Contract"].unique())
    sel_contrato = st.multiselect(
        "Tipo de contrato",
        contratos_disponiveis,
        default=contratos_disponiveis
    )

    internets_disponiveis = sorted(df_completo["InternetService"].unique())
    sel_internet = st.multiselect(
        "Tipo de internet",
        internets_disponiveis,
        default=internets_disponiveis
    )

# --- Aplicar filtros ---
df = df_completo[
    df_completo["Contract"].isin(sel_contrato) &
    df_completo["InternetService"].isin(sel_internet)
]

# --- Três métricas no topo ---
churned = df[df["churn_num"] == 1]

taxa_churn = df["churn_num"].mean() * 100
tempo_medio_cancelados = churned["tenure"].mean() if len(churned) > 0 else 0
receita_em_risco = churned["MonthlyCharges"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Taxa de churn", f"{taxa_churn:.1f}%")
col2.metric("Tempo médio de casa (cancelados)", f"{tempo_medio_cancelados:.1f} meses")
col3.metric("Receita mensal em risco", f"US$ {receita_em_risco:,.2f}")

st.divider()

# --- Gráfico 1 — Churn por tipo de contrato (barras verticais) ---
# 3 categorias curtas: barras verticais são ideais para comparar alturas
contrato = df.groupby("Contract")["churn_num"].mean().mul(100).round(1)
contrato = contrato.reset_index()
contrato.columns = ["Contract", "taxa_churn"]
contrato = contrato.sort_values("taxa_churn", ascending=False)

fig1 = px.bar(contrato, x="Contract", y="taxa_churn",
              text="taxa_churn", color_discrete_sequence=["#E8341C"])
fig1.update_traces(texttemplate="%{text}%", textposition="outside")
fig1.update_layout(yaxis_visible=False, yaxis_showgrid=False,
                   title="Taxa de churn por tipo de contrato",
                   xaxis=dict(tickangle=0, automargin=True))
fig1.add_hline(y=df["churn_num"].mean() * 100, line_dash="dash",
               line_color="gray", layer="below", annotation_text="Média geral")

# --- Gráfico 2 — Churn por tempo de casa (barras verticais em ordem cronológica) ---
# Ordem cronológica intencional: a história é que o churn cai com o tempo de casa
ordem = ["0-12 meses", "13-24 meses", "25-48 meses", "49+ meses"]
tenure = df.groupby("tenure_grupo")["churn_num"].mean().mul(100).round(1)
tenure = tenure.reindex(ordem).reset_index()
tenure.columns = ["tenure_grupo", "taxa_churn"]

fig2 = px.bar(tenure, x="tenure_grupo", y="taxa_churn",
              text="taxa_churn", color_discrete_sequence=["#E8341C"])
fig2.update_traces(texttemplate="%{text}%", textposition="outside")
fig2.update_layout(yaxis_visible=False, yaxis_showgrid=False,
                   xaxis_title="Tempo de casa",
                   title="Churn por tempo de casa",
                   xaxis=dict(tickangle=0, automargin=True))

col_g1, col_g2 = st.columns(2)
with col_g1:
    st.plotly_chart(fig1, use_container_width=True)
with col_g2:
    st.plotly_chart(fig2, use_container_width=True)

# --- Gráfico 3 — Churn por método de pagamento (barras horizontais) ---
# Nomes longos ("Electronic check", "Bank transfer") ficam na diagonal em barras verticais
pagamento = df.groupby("PaymentMethod")["churn_num"].mean().mul(100).round(1)
pagamento = pagamento.reset_index()
pagamento.columns = ["PaymentMethod", "taxa_churn"]
pagamento = pagamento.sort_values("taxa_churn", ascending=True)

fig3 = px.bar(pagamento, x="taxa_churn", y="PaymentMethod",
              orientation="h", text="taxa_churn",
              color_discrete_sequence=["#E8341C"])
fig3.update_traces(texttemplate="%{text}%", textposition="outside")
fig3.update_layout(xaxis_visible=False,
                   title="Churn por método de pagamento")

# --- Gráfico 4 — Churn por tipo de internet (barras verticais) ---
# Fibra óptica cancela muito mais que DSL — um dos insights mais fortes do dataset
internet = df.groupby("InternetService")["churn_num"].mean().mul(100).round(1)
internet = internet.reset_index()
internet.columns = ["InternetService", "taxa_churn"]
internet = internet.sort_values("taxa_churn", ascending=False)

fig4 = px.bar(internet, x="InternetService", y="taxa_churn",
              text="taxa_churn", color_discrete_sequence=["#E8341C"])
fig4.update_traces(texttemplate="%{text}%", textposition="outside")
fig4.update_layout(yaxis_visible=False, yaxis_showgrid=False,
                   title="Churn por tipo de internet",
                   xaxis=dict(tickangle=0, automargin=True))
fig4.add_hline(y=df["churn_num"].mean() * 100, line_dash="dash",
               line_color="gray", layer="below", annotation_text="Média geral")

col_g3, col_g4 = st.columns(2)
with col_g3:
    st.plotly_chart(fig3, use_container_width=True)
with col_g4:
    st.plotly_chart(fig4, use_container_width=True)

# --- Gráfico 5 — Cobrança mensal: cancelados vs ativos (box plot) ---
# Box plot revela mediana, quartis e outliers — médias esconderiam que cancelados
# pagam mais E com menor variação
fig5 = px.box(df, x="Churn", y="MonthlyCharges",
              color="Churn",
              color_discrete_map={"Yes": "#E8341C", "No": "#2E5FA3"},
              title="Cobrança mensal — cancelados vs ativos")
fig5.update_layout(showlegend=False)

# --- Gráfico 6 — Impacto dos serviços na retenção (barras horizontais agrupadas) ---
# Compara "tem o serviço" vs "não tem" para 3 serviços lado a lado.
# Horizontal porque os nomes dos serviços são longos.
servicos = ["TechSupport", "OnlineSecurity", "OnlineBackup"]
dados_servicos = []

for s in servicos:
    for valor in ["Yes", "No"]:
        taxa = df[df[s] == valor]["churn_num"].mean() * 100
        dados_servicos.append({"Servico": s, "Contratado": valor,
                               "taxa_churn": round(taxa, 1)})

df_servicos = pd.DataFrame(dados_servicos)

fig6 = px.bar(df_servicos, x="taxa_churn", y="Servico",
              color="Contratado", orientation="h",
              barmode="group", text="taxa_churn",
              color_discrete_map={"Yes": "#2E5FA3", "No": "#E8341C"},
              title="Impacto dos serviços na retenção")
fig6.update_traces(texttemplate="%{text}%", textposition="outside")
fig6.update_layout(xaxis_visible=False)

col_g5, col_g6 = st.columns(2)
with col_g5:
    st.plotly_chart(fig5, use_container_width=True)
with col_g6:
    st.plotly_chart(fig6, use_container_width=True)

# --- Tabela detalhada ---
st.subheader("Dados detalhados")
colunas_tabela = ["tenure", "Contract", "MonthlyCharges", "InternetService", "TechSupport", "Churn"]
st.dataframe(df[colunas_tabela], use_container_width=True)
