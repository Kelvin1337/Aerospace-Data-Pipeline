# Pipeline de Dados Aeroespaciais

![GitHub repo size](https://img.shields.io/github/repo-size/Kelvin1337/Aerospace-Data-Pipeline?style=for-the-badge)
![GitHub language count](https://img.shields.io/github/languages/count/Kelvin1337/Aerospace-Data-Pipeline?style=for-the-badge)

<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" alt="Python Logo" width="80" height="80" align="right" />

> Projeto de ponta a ponta que implementa um pipeline ETL (Extração, Transformação e Carga) e Análise Exploratória de Dados (EDA) de missões espaciais históricas. Os dados são limpos, enriquecidos e persistidos em um banco de dados relacional SQLite para gerar insights financeiros e corporativos.

### 🔄 Ajustes e melhorias

O projeto ainda está em desenvolvimento e as próximas atualizações serão voltadas para as seguintes tarefas:

- [x] Estruturação da arquitetura de caminhos locais (*Single Source of Truth*)
- [x] Implementação de regras estritas de *Data Quality* e limpeza de strings para `snake_case`
- [x] Enriquecimento geográfico de bases e tradução geopolítica para PT-BR
- [x] Persistência idempotente e relacional com SQLite
- [x] Análise exploratória básica do status das missões com Seaborn e Matplotlib
- [x] Construção de um Dashboard interativo (Streamlit ou PowerBI) ligado à base SQLite

## 💻 Pré-requisitos

Antes de começar, verifique se você atendeu aos seguintes requisitos:

- Você tem o Python 3.10 ou superior instalado na sua máquina.
- Você instalou as bibliotecas necessárias listadas no projeto (`pandas`, `numpy`, `matplotlib`, `seaborn`).
- Você possui um visualizador de banco de dados SQLite (como o DBeaver ou a extensão do VS Code) para auditar a base.
