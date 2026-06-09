import pandas as pd
import plotly.express as px
import streamlit as st

# --- Configuração da página ---
st.set_page_config(page_title="Churn CS", layout="wide")

# --- Dicionários de tradução ---
MAP_CONTRATO = {
    "Month-to-month": "Mensal",
    "One year": "Anual",
    "Two year": "Bianual",
}
MAP_INTERNET = {
    "Fiber optic": "Fibra óptica",
    "DSL": "DSL",
    "No": "Sem internet",
}
MAP_PAGAMENTO = {
    "Electronic check": "Cheque eletrônico",
    "Mailed check": "Cheque por correio",
    "Bank transfer (automatic)": "Transferência bancária (auto.)",
    "Credit card (automatic)": "Cartão de crédito (auto.)",
}
MAP_CHURN = {"Yes": "Cancelou", "No": "Ativo"}
MAP_SIM_NAO = {"Yes": "Sim", "No": "Não"}
MAP_SERVICO = {
    "TechSupport": "Suporte Técnico",
    "OnlineSecurity": "Segurança Online",
    "OnlineBackup": "Backup Online",
}

# --- Paletas de cor padrão (do melhor ao pior resultado) ---
# A última cor representa sempre o resultado mais negativo (maior churn)
PALETAS = {
    2: ["#feb24c", "#f03b20"],
    3: ["#ffeda0", "#feb24c", "#f03b20"],
    4: ["#ffffb2", "#fecc5c", "#fd8d3c", "#e31a1c"],
    5: ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"],
    6: ["#ffffb2", "#fed976", "#feb24c", "#fd8d3c", "#f03b20", "#bd0026"],
    7: ["#ffffb2", "#fed976", "#feb24c", "#fd8d3c", "#fc4e2a", "#e31a1c", "#b10026"],
    8: ["#ffffcc", "#ffeda0", "#fed976", "#feb24c", "#fd8d3c", "#fc4e2a", "#e31a1c", "#b10026"],
}

def mapa_cores(valores_asc):
    """
    Recebe uma lista de categorias ordenadas do MELHOR para o PIOR (taxa_churn crescente).
    Retorna {categoria: cor} — cor mais escura sempre no resultado mais negativo.
    """
    n = len(valores_asc)
    if n == 0:
        return {}
    if n == 1:
        return {valores_asc[0]: PALETAS[2][-1]}
    cores = PALETAS.get(n, PALETAS[8])
    return {v: c for v, c in zip(valores_asc, cores)}


# Cores fixas para gráficos de 2 variáveis Cancelou / Ativo e Sim / Não
COR_MELHOR   = PALETAS[2][0]   # #feb24c — ativo / com serviço
COR_PIOR     = PALETAS[2][1]   # #f03b20 — cancelou / sem serviço

# --- Carregamento e tradução dos dados ---
df_completo = pd.read_csv("dados/churn_processado.csv")

# Colunas traduzidas para exibição nos gráficos e filtros
df_completo["Contrato"]  = df_completo["Contract"].map(MAP_CONTRATO)
df_completo["Internet"]  = df_completo["InternetService"].map(MAP_INTERNET)
df_completo["Pagamento"] = df_completo["PaymentMethod"].map(MAP_PAGAMENTO)
df_completo["Situação"]  = df_completo["Churn"].map(MAP_CHURN)

# Serviços: Yes/No → Sim/Não (mantém "Não contratado" gerado pelo 1_processar.py)
for orig, pt in MAP_SERVICO.items():
    df_completo[pt] = df_completo[orig].map(lambda x: MAP_SIM_NAO.get(x, x))

# --- Título e subtítulo ---
st.title("Análise de Churn — Customer Success")

total_clientes = len(df_completo)
taxa_geral = df_completo["churn_num"].mean() * 100
st.markdown(f"**{total_clientes:,} clientes analisados** — Taxa de churn geral: **{taxa_geral:.1f}%**")

# --- Barra lateral com filtros (usa valores traduzidos) ---
with st.sidebar:
    st.header("Filtros")

    contratos_disp = sorted(df_completo["Contrato"].dropna().unique())
    sel_contrato = st.multiselect("Tipo de contrato", contratos_disp, default=contratos_disp)

    internets_disp = sorted(df_completo["Internet"].dropna().unique())
    sel_internet = st.multiselect("Tipo de internet", internets_disp, default=internets_disp)

# --- Aplicar filtros ---
df = df_completo[
    df_completo["Contrato"].isin(sel_contrato) &
    df_completo["Internet"].isin(sel_internet)
]

# --- Três métricas no topo ---
churned = df[df["churn_num"] == 1]

taxa_churn        = df["churn_num"].mean() * 100
tempo_medio_churn = churned["tenure"].mean() if len(churned) > 0 else 0
receita_em_risco  = churned["MonthlyCharges"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Taxa de churn",                    f"{taxa_churn:.1f}%")
col2.metric("Tempo médio de casa (cancelados)",  f"{tempo_medio_churn:.1f} meses")
col3.metric("Receita mensal em risco",           f"US$ {receita_em_risco:,.2f}")

st.divider()

# --- Gráfico 1 — Churn por tipo de contrato (3 variáveis) ---
# Paleta calculada dinamicamente: menor churn → cor mais clara, maior → mais escura
contrato = df.groupby("Contrato")["churn_num"].mean().mul(100).round(1).reset_index()
contrato.columns = ["Contrato", "taxa_churn"]
cores_contrato = mapa_cores(contrato.sort_values("taxa_churn")["Contrato"].tolist())
contrato = contrato.sort_values("taxa_churn", ascending=False)

fig1 = px.bar(contrato, x="Contrato", y="taxa_churn",
              text="taxa_churn", color="Contrato",
              color_discrete_map=cores_contrato)
fig1.update_traces(texttemplate="%{text}%", textposition="outside")
fig1.update_layout(yaxis_visible=False, yaxis_showgrid=False, showlegend=False,
                   title="Taxa de churn por tipo de contrato",
                   xaxis=dict(tickangle=0, automargin=True))
fig1.add_hline(y=df["churn_num"].mean() * 100, line_dash="dash",
               line_color="gray", layer="below", annotation_text="Média geral")

# --- Gráfico 2 — Churn por tempo de casa (4 variáveis, ordem cronológica) ---
# Paleta por severidade de churn; exibição mantém ordem temporal
ordem = ["0-12 meses", "13-24 meses", "25-48 meses", "49+ meses"]
tenure = df.groupby("tenure_grupo")["churn_num"].mean().mul(100).round(1)
tenure = tenure.reindex(ordem).reset_index()
tenure.columns = ["Tempo de casa", "taxa_churn"]
cores_tenure = mapa_cores(tenure.sort_values("taxa_churn")["Tempo de casa"].tolist())

fig2 = px.bar(tenure, x="Tempo de casa", y="taxa_churn",
              text="taxa_churn", color="Tempo de casa",
              color_discrete_map=cores_tenure,
              category_orders={"Tempo de casa": ordem})
fig2.update_traces(texttemplate="%{text}%", textposition="outside")
fig2.update_layout(yaxis_visible=False, yaxis_showgrid=False, showlegend=False,
                   xaxis_title="Tempo de casa",
                   title="Churn por tempo de casa",
                   xaxis=dict(tickangle=0, automargin=True))

col_g1, col_g2 = st.columns(2)
with col_g1:
    st.plotly_chart(fig1, use_container_width=True)
with col_g2:
    st.plotly_chart(fig2, use_container_width=True)

# --- Gráfico 3 — Churn por método de pagamento (4 variáveis, barras horizontais) ---
# Ordenação ascendente serve tanto para a paleta quanto para a exibição
pagamento = df.groupby("Pagamento")["churn_num"].mean().mul(100).round(1).reset_index()
pagamento.columns = ["Método de pagamento", "taxa_churn"]
pagamento = pagamento.sort_values("taxa_churn", ascending=True)
cores_pagamento = mapa_cores(pagamento["Método de pagamento"].tolist())

fig3 = px.bar(pagamento, x="taxa_churn", y="Método de pagamento",
              orientation="h", text="taxa_churn",
              color="Método de pagamento",
              color_discrete_map=cores_pagamento)
fig3.update_traces(texttemplate="%{text}%", textposition="outside")
fig3.update_layout(xaxis_visible=False, showlegend=False,
                   title="Churn por método de pagamento")

# --- Gráfico 4 — Churn por tipo de internet (3 variáveis) ---
internet = df.groupby("Internet")["churn_num"].mean().mul(100).round(1).reset_index()
internet.columns = ["Internet", "taxa_churn"]
cores_internet = mapa_cores(internet.sort_values("taxa_churn")["Internet"].tolist())
internet = internet.sort_values("taxa_churn", ascending=False)

fig4 = px.bar(internet, x="Internet", y="taxa_churn",
              text="taxa_churn", color="Internet",
              color_discrete_map=cores_internet)
fig4.update_traces(texttemplate="%{text}%", textposition="outside")
fig4.update_layout(yaxis_visible=False, yaxis_showgrid=False, showlegend=False,
                   title="Churn por tipo de internet",
                   xaxis=dict(tickangle=0, automargin=True))
fig4.add_hline(y=df["churn_num"].mean() * 100, line_dash="dash",
               line_color="gray", layer="below", annotation_text="Média geral")

col_g3, col_g4 = st.columns(2)
with col_g3:
    st.plotly_chart(fig3, use_container_width=True)
with col_g4:
    st.plotly_chart(fig4, use_container_width=True)

# --- Gráfico 5 — Cobrança mensal: cancelados vs ativos (2 variáveis) ---
# Paleta 2 vars: Ativo (melhor) → COR_MELHOR | Cancelou (pior) → COR_PIOR

# Esquerda: cobrança média por grupo
media_cobranca = df.groupby("Churn")["MonthlyCharges"].mean().round(2).reset_index()
media_cobranca.columns = ["Churn", "media"]
media_cobranca["Churn"] = media_cobranca["Churn"].map({"Yes": "Cancelou", "No": "Ativo"})

fig5a = px.bar(media_cobranca, x="Churn", y="media",
               text="media", color="Churn",
               color_discrete_map={"Cancelou": COR_PIOR, "Ativo": COR_MELHOR},
               title="Cobrança média — cancelados vs ativos")
fig5a.update_traces(texttemplate="R$ %{text:.2f}", textposition="outside")
fig5a.update_layout(yaxis_visible=False, yaxis_showgrid=False, showlegend=False)

# Direita: box plot com distribuição completa
fig5b = px.box(df, x="Situação", y="MonthlyCharges",
               color="Situação",
               color_discrete_map={"Cancelou": COR_PIOR, "Ativo": COR_MELHOR},
               title="Cobrança mensal — cancelados vs ativos",
               labels={"MonthlyCharges": "Cobrança mensal (US$)"})
fig5b.update_layout(showlegend=False)

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig5a, use_container_width=True)
with col2:
    st.plotly_chart(fig5b, use_container_width=True)

# --- Gráfico 6 — Impacto dos serviços na retenção (2 variáveis por serviço) ---
# Sim/contratado (melhor) → COR_MELHOR | Não (pior, maior churn) → COR_PIOR
dados_servicos = []
for orig, pt in MAP_SERVICO.items():
    for valor_orig, valor_pt in MAP_SIM_NAO.items():
        taxa = df[df[orig] == valor_orig]["churn_num"].mean() * 100
        dados_servicos.append({"Serviço": pt, "Contratado": valor_pt,
                               "taxa_churn": round(taxa, 1)})

df_servicos = pd.DataFrame(dados_servicos)

fig6 = px.bar(df_servicos, x="taxa_churn", y="Serviço",
              color="Contratado", orientation="h",
              barmode="group", text="taxa_churn",
              color_discrete_map={"Sim": COR_MELHOR, "Não": COR_PIOR},
              title="Impacto dos serviços na retenção")
fig6.update_traces(texttemplate="%{text}%", textposition="outside")
fig6.update_layout(xaxis_visible=False)

st.plotly_chart(fig6, use_container_width=True)

# --- Tabela detalhada ---
st.subheader("Dados detalhados")

tabela = df[["tenure", "Contrato", "MonthlyCharges", "Internet",
             "Suporte Técnico", "Situação"]].copy()
tabela = tabela.rename(columns={
    "tenure": "Meses de casa",
    "MonthlyCharges": "Cobrança mensal (US$)",
})
st.dataframe(tabela, use_container_width=True)
