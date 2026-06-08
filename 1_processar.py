import pandas as pd

ARQUIVO_ENTRADA = "dados/WA_Fn-UseC_-Telco-Customer-Churn.csv"
ARQUIVO_SAIDA = "dados/churn_processado.csv"

# Colunas de servicos com valores a padronizar
COLUNAS_SERVICOS = [
    "MultipleLines",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
]

MAPA_TENURE = [
    (0, 12, "0-12 meses"),
    (13, 24, "13-24 meses"),
    (25, 48, "25-48 meses"),
    (49, float("inf"), "49+ meses"),
]


def classificar_tenure(meses):
    for inicio, fim, grupo in MAPA_TENURE:
        if inicio <= meses <= fim:
            return grupo
    return "49+ meses"


def processar():
    df = pd.read_csv(ARQUIVO_ENTRADA)

    # TotalCharges: converter para numerico e preencher nulos com 0
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0)

    # churn_num: Yes -> 1, No -> 0
    df["churn_num"] = df["Churn"].map({"Yes": 1, "No": 0})

    # Padronizar valores de servicos
    for col in COLUNAS_SERVICOS:
        if col in df.columns:
            df[col] = df[col].replace(
                {"No internet service": "Não contratado", "No phone service": "Não contratado"}
            )

    # tenure_grupo
    df["tenure_grupo"] = df["tenure"].apply(classificar_tenure)

    df.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8-sig")

    # Resumo
    total = len(df)
    taxa_churn = df["churn_num"].mean() * 100

    print("=" * 50)
    print("RESUMO DO PROCESSAMENTO")
    print("=" * 50)
    print(f"Total de clientes : {total:,}")
    print(f"Taxa de churn geral: {taxa_churn:.1f}%")

    print("\nChurn por tipo de contrato:")
    churn_contrato = (
        df.groupby("Contract")["churn_num"]
        .agg(total="count", cancelaram="sum")
        .assign(taxa=lambda x: (x["cancelaram"] / x["total"] * 100).round(1))
    )
    print(churn_contrato.to_string())

    print("\nTempo médio de casa:")
    tempo_medio = df.groupby("Churn")["tenure"].mean().round(1)
    print(f"  Cancelaram : {tempo_medio.get('Yes', 0):.1f} meses")
    print(f"  Permaneceram: {tempo_medio.get('No', 0):.1f} meses")

    print(f"\nArquivo salvo em: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    processar()
