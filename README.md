## Projeto: GRAPHFY - Gráficos com IA
**Integrante**: Caue Fernandes

---

### Visão Geral
O **GRAPHFY** é uma aplicação web inteligente que permite a leitura e análise de planilhas para geração automatizada de gráficos, com auxílio de IA (LLaMA 3). A arquitetura do sistema segue o modelo cliente-servidor:

- O **front-end** é desenvolvido com **Next.js 14**.
- O **back-end** é implementado em **Python** com **FastAPI**, usando o modelo LLaMA 3 como LLM.
- O banco de dados principal é **PostgreSQL**, garantindo a persistência de dados.
- A autenticação é feita via **JWT**, proporcionando segurança nas operações de login e controle de acesso.

---

### Escopo
A aplicação web permitirá:

- Upload e leitura de planilhas
- Geração de gráficos com auxílio da IA
- Autenticação de usuários

---

### Arquitetura
**API RESTful** baseada em uma **Arquitetura em Camadas**:

- **Monolítica**, por baixo custo e tempo para desenvolvimento.
- Divisão em camadas:
  - **Front-end:** Interface interativa para usuários.
  - **Back-end:** Processamento de lógica de negócios.
  - **Banco de Dados:** Persistência das informações.

![image](https://github.com/user-attachments/assets/ea1bc5d0-935e-421a-86e9-3a4034f7ce4a)



- **Front-end (Next.js 14)**  
  Interface web interativa para os usuários.

- **Back-end (FastAPI + Python + LLaMA 3)**  
  Processamento da lógica de negócio, leitura de planilhas e comunicação com o modelo de linguagem.

- **Banco de Dados (PostgreSQL)**  
  Armazenamento de usuários, planilhas e resultados processados.

---

### Tecnologias Utilizadas

#### Front-end
- Next.js 14 (App Router)
- React Query ou SWR
- Tailwind CSS
- Axios
- NextAuth.js

#### Back-end
- Python com FastAPI
- LLaMA 3 (llm)
- JWT
- Pydantic (validação de dados)
- TortoiseORM
- PostgreSQL

#### Banco de Dados
- PostgreSQL

---

### Infraestrutura
- **Front-end**: Vercel
- **Back-end**: Railway
- **Banco de Dados**: Railway

### Repositório

  Github - graphfy v1.3

