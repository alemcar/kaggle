import pandas as pd
import plotly.express as px
import streamlit as st

COR_PRINCIPAL = "#E8341C"
COR_ATIVO = "#2E5FA3"
ARQUIVO = "dados/churn_processado.csv"
ORDEM_TENURE = ["0-12 meses", "13-24 meses", "25-48 meses", "49+ meses"]


@st.cache_data
def carregar_dados():
    return pd.read_csv(ARQUIVO)


def calcular_taxa_churn(df):
    return df["churn_num"].mean() * 100


def grafico_contrato(df, taxa_media):
    agg = (
        df.groupby("Contract")["churn_num"]
        .agg(total="count", cancelaram="sum")
        .assign(taxa=lambda x: (x["cancelaram"] / x["total"] * 100).round(1))
        .sort_values("taxa", ascending=False)
        .reset_index()
    )
    fig = px.bar(
        agg,
        x="Contract",
        y="taxa",
        title="Taxa de churn por tipo de contrato",
        color_discrete_sequence=[COR_PRINCIPAL],
        text="taxa",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(yaxis_visible=False, xaxis_title="", yaxis_title="")
    fig.add_hline(y=taxa_media, line_dash="dash", line_color="gray", layer="below",
                  annotation_text=f"Média: {taxa_media:.1f}%")
    return fig


def grafico_tenure(df):
    agg = (
        df.groupby("tenure_grupo")["churn_num"]
        .agg(total="count", cancelaram="sum")
        .assign(taxa=lambda x: (x["cancelaram"] / x["total"] * 100).round(1))
        .reindex(ORDEM_TENURE)
        .reset_index()
    )
    fig = px.bar(
        agg,
        x="tenure_grupo",
        y="taxa",
        title="Churn por tempo de casa",
        color_discrete_sequence=[COR_PRINCIPAL],
        text="taxa",
        category_orders={"tenure_grupo": ORDEM_TENURE},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(yaxis_visible=False, xaxis_title="", yaxis_title="")
    return fig


def grafico_pagamento(df):
    agg = (
        df.groupby("PaymentMethod")["churn_num"]
        .agg(total="count", cancelaram="sum")
        .assign(taxa=lambda x: (x["cancelaram"] / x["total"] * 100).round(1))
        .sort_values("taxa", ascending=True)
        .reset_index()
    )
    fig = px.bar(
        agg,
        x="taxa",
        y="PaymentMethod",
        orientation="h",
        title="Churn por método de pagamento",
        color_discrete_sequence=[COR_PRINCIPAL],
        text="taxa",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(xaxis_visible=False, xaxis_title="", yaxis_title="")
    return fig


def grafico_boxplot(df):
    df_plot = df.copy()
    df_plot["Situação"] = df_plot["churn_num"].map({1: "Cancelou", 0: "Ativo"})
    fig = px.box(
        df_plot,
        x="Situação",
        y="MonthlyCharges",
        title="Cobrança mensal — cancelados vs ativos",
        color="Situação",
        color_discrete_map={"Cancelou": COR_PRINCIPAL, "Ativo": COR_ATIVO},
    )
    fig.update_layout(xaxis_title="", yaxis_title="Cobrança mensal (R$)")
    return fig


def grafico_servicos(df):
    servicos = ["TechSupport", "OnlineSecurity", "OnlineBackup"]
    registros = []
    for servico in servicos:
        for valor in df[servico].unique():
            if valor == "Não contratado":
                continue
            sub = df[df[servico] == valor]
            taxa = sub["churn_num"].mean() * 100
            registros.append({"Serviço": f"{servico} = {valor}", "taxa": round(taxa, 1)})
    agg = pd.DataFrame(registros).sort_values("taxa", ascending=True)
    fig = px.bar(
        agg,
        x="taxa",
        y="Serviço",
        orientation="h",
        title="Serviços e impacto na retenção",
        color_discrete_sequence=[COR_PRINCIPAL],
        text="taxa",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(xaxis_visible=False, xaxis_title="", yaxis_title="")
    return fig


def main():
    st.set_page_config(page_title="Churn CS", layout="wide")
    st.title("Análise de Churn — Customer Success")

    df_completo = carregar_dados()

    taxa_geral = calcular_taxa_churn(df_completo)
    st.markdown(
        f"**{len(df_completo):,} clientes analisados** — Taxa de churn geral: **{taxa_geral:.1f}%**"
    )

    # Sidebar
    contratos = sorted(df_completo["Contract"].unique())
    internets = sorted(df_completo["InternetService"].unique())

    with st.sidebar:
        st.header("Filtros")
        sel_contrato = st.multiselect("Tipo de contrato", contratos, default=contratos)
        sel_internet = st.multiselect("Tipo de internet", internets, default=internets)

    df = df_completo[
        df_completo["Contract"].isin(sel_contrato) &
        df_completo["InternetService"].isin(sel_internet)
    ]

    # Métricas
    taxa_filtrada = calcular_taxa_churn(df)
    churned = df[df["churn_num"] == 1]
    tempo_medio_churn = churned["tenure"].mean() if len(churned) > 0 else 0
    receita_risco = churned["MonthlyCharges"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Taxa de churn", f"{taxa_filtrada:.1f}%")
    c2.metric("Tempo médio de casa (cancelados)", f"{tempo_medio_churn:.1f} meses")
    c3.metric("Receita mensal em risco", f"US$ {receita_risco:,.2f}")

    st.divider()

    # Gráficos
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(grafico_contrato(df, taxa_filtrada), use_container_width=True)
    with col2:
        st.plotly_chart(grafico_tenure(df), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(grafico_pagamento(df), use_container_width=True)
    with col4:
        st.plotly_chart(grafico_boxplot(df), use_container_width=True)

    st.plotly_chart(grafico_servicos(df), use_container_width=True)

    # Tabela
    colunas_tabela = ["tenure", "Contract", "MonthlyCharges", "InternetService", "TechSupport", "Churn"]
    st.dataframe(df[colunas_tabela], use_container_width=True)


if __name__ == "__main__":
    main()
