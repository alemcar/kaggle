# Telecom Churn — Análise de Customer Success

Projeto de análise de churn aplicada a Customer Success, usando o dataset público **Telco Customer Churn** (IBM/Kaggle). O objetivo é demonstrar raciocínio analítico orientado a CS: identificar onde e quando clientes cancelam e quais alavancas um time poderia acionar.

---

## Estrutura do projeto

```
telecom-churn-cx/
├── dados/                                      # Dataset (não versionado)
│   ├── WA_Fn-UseC_-Telco-Customer-Churn.csv   # Arquivo original do Kaggle
│   └── churn_processado.csv                    # Gerado pelo 1_processar.py
├── 1_processar.py                              # Limpeza, features e resumo
├── 2_dashboard.py                              # Dashboard interativo (Streamlit)
├── analise_sql.ipynb                           # 8 queries SQL com interpretação de CS
└── requirements.txt
```

---

## Como rodar

### 1. Baixar o dataset

Acesse [kaggle.com/datasets/blastchar/telco-customer-churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) e salve o CSV em `dados/`.

Ou baixe direto via Python:

```python
import kagglehub, shutil
path = kagglehub.dataset_download("blastchar/telco-customer-churn")
shutil.copy(f"{path}/WA_Fn-UseC_-Telco-Customer-Churn.csv", "dados/")
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Processar os dados

```bash
python 1_processar.py
```

Gera `dados/churn_processado.csv` e imprime um resumo no terminal:

```
Total de clientes : 7.043
Taxa de churn geral: 26.5%

Churn por tipo de contrato:
  Month-to-month   42.7%
  One year         11.3%
  Two year          2.8%

Tempo médio de casa:
  Cancelaram :  18.0 meses
  Permaneceram: 37.6 meses
```

### 4. Abrir o dashboard

```bash
streamlit run 2_dashboard.py
```

Acesse `http://localhost:8501` no navegador.

---

## Dashboard

O dashboard é filtrado por **tipo de contrato** e **tipo de internet** via sidebar. Todos os elementos reagem aos filtros em tempo real.

**Métricas no topo**
- Taxa de churn (% de cancelamentos)
- Tempo médio de casa dos clientes que cancelaram
- Receita mensal em risco (soma do `MonthlyCharges` dos churned)

**Gráficos**

| # | Título | Tipo |
|---|--------|------|
| 1 | Taxa de churn por tipo de contrato | Barras verticais |
| 2 | Churn por tempo de casa | Barras verticais (ordem cronológica) |
| 3 | Churn por método de pagamento | Barras horizontais |
| 4 | Churn por tipo de internet | Barras verticais |
| 5a | Cobrança média — cancelados vs ativos | Barras verticais |
| 5b | Cobrança mensal — cancelados vs ativos | Box plot |
| 6 | Impacto dos serviços na retenção | Barras horizontais agrupadas |

Paleta de cores sequencial: do amarelo claro (melhor resultado) ao vermelho escuro (pior resultado). A última cor representa sempre o maior churn.

---

## Análise SQL

O notebook `analise_sql.ipynb` carrega os dados em SQLite em memória e responde 8 perguntas de negócio:

| Query | Pergunta |
|-------|---------|
| 1 | Qual é a taxa de churn geral? |
| 2 | Como o churn varia por tipo de contrato? |
| 3 | Qual o perfil de tempo de casa e cobrança entre quem cancela e quem fica? |
| 4 | Quantos clientes ativos estão em situação de alto risco? |
| 5 | Qual a receita em risco por tipo de contrato? |
| 6 | O TechSupport reduz o churn? |
| 7 | Como o churn varia conforme o tempo de casa? |
| 8 | Qual é o perfil completo de quem cancela vs quem permanece? |

Cada query é seguida de uma interpretação em linguagem de CS.

---

## Principais insights

- **Contrato mensal** tem taxa de churn de **42,7%** — 15× maior que contratos bianuais (2,8%)
- **Primeiros 12 meses** são o período crítico: taxa de churn de ~47%, contra ~6% após 4 anos
- **Cheque eletrônico** concentra os maiores cancelamentos entre os métodos de pagamento
- **Fibra óptica** apresenta churn significativamente maior que DSL, mesmo sendo o plano mais premium
- Clientes **sem TechSupport, OnlineSecurity ou OnlineBackup** cancelam em proporção muito maior
- Clientes churned pagam **mais por mês** e ficam **menos tempo** — perda de LTV potencial alta

---

## Stack

| Ferramenta | Uso |
|---|---|
| `pandas` | Limpeza e engenharia de features |
| `streamlit` | Dashboard interativo |
| `plotly express` | Todos os gráficos |
| `sqlite3` | Análise SQL em memória no notebook |
| `kagglehub` | Download automatizado do dataset |

---

## Dataset

**Telco Customer Churn** — IBM Sample Data  
Fonte: [kaggle.com/datasets/blastchar/telco-customer-churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)  
7.043 clientes · 21 colunas · Taxa de churn: 26,5%
