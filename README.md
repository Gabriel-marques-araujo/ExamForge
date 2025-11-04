# Documentação do Protótipo - ExamForge

Este documento explica o que foi utilizado para a construção do protótipo apresentado em **17/10**.

---

## 1. Informações Gerais

- **Nome do Projeto:** ExamForge
- **Versão do Protótipo:** 1.0
- **Objetivo Principal:** Validar um sistema de **RAG (Retrieval-Augmented Generation)** para criar e avaliar questões de múltipla escolha (MCQ) sobre uma base de conhecimento personalizada.
- **Proprietário/Equipe Responsável:** Equipe ExamForge

---

## 2. Detalhes Técnicos e de Design (Backend)

- **Framework:** FastAPI
- **Servidor:** Uvicorn

### Stack de IA (RAG)

- **Modelo de Geração:** Google Gemini (`gemini-2.5-flash`)
- **Orquestração:** LangChain
- **Modelo de Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` ( Hugging Face)
- **Banco de Dados Vetorial:** ChromaDB

### Processo de Ingestão (Chunking)

- **Método:** RecursiveCharacterTextSplitter
- **Tamanho do Chunk:** 1000 caracteres
- **Sobreposição:** 0 caracteres

### Nomes Padrão (Paths)

- **Pasta de Documentos:** `./documentos`
- **Pasta do Banco Vetorial:** `./chroma`
- **Nome da Coleção (Chroma):** `examforge_docs`

### Chaves de API (Requerida)

- `GEMINI_API_KEY` (definida no arquivo `.env`)

---

## 3. Endpoints da API Backend (Fluxos de Uso)

A API do **ExamForge** está organizada em três módulos principais, cada um com responsabilidades distintas: 

| Módulo | Prefixo | Função Principal |
| --- | --- | --- |
| **Raiz** | `/` | Verificação e informações básicas do sistema |
| **Base de Conhecimento** | `/base` | Upload e criação do banco vetorial com documentos de estudo |
| **Criação de Questões** | `/create` | Geração e avaliação de questões de múltipla escolha (MCQ) |

Cada módulo expõe endpoints REST que podem ser acessados via ferramentas como Swagger, Postman, Insomnia, ou pelo frontend web.

---

### 3.1. Endpoint Raiz

**Função:** Verificar a disponibilidade da API

| Método | Endpoint | Descrição | Resposta (JSON) |
| --- | --- | --- | --- |
| GET | `/` | Retorna uma mensagem de boas-vindas | `{"message": "Bem-vindo ao ExamForg!"}` |

---

### 3.2. Módulo `/base` (Criação da Base de Conhecimento)

Endpoints para alimentar o banco de dados vetorial. *(Não utilizado pelo frontend do usuário).*

| Método | Endpoint | Descrição | Corpo (Input) | Resposta (JSON) |
| --- | --- | --- | --- | --- |
| POST | `/base/upload/` | Envia arquivos para a pasta `./documentos` | `form-data (com file)` | `{"message": "Arquivo [nome] enviado..."}` |
| POST | `/base/create/` | Processa os arquivos da pasta `./documentos` e insere no banco vetorial | Nenhum | `{"message": "Banco de dados criado com [N] chunks."}` |
| GET | `/base/status/` | Verifica o status da pasta de documentos | Nenhum | `{"status": "ok", "docs": N, "collection": "..."}` |

---

### 3.3. Módulo `/rag` (Geração e Verificação de Perguntas)

Endpoints utilizados pelo frontend para interação com o usuário.

| Método | Endpoint | Descrição | Corpo (Input JSON) | Resposta (JSON) |
| --- | --- | --- | --- | --- |
| POST | `/rag/generate_mcq/` | Gera uma questão de múltipla escolha (MCQ) com 4 opções baseadas em um tópico | `{"topic": "Seu tópico"}` | `{"question": "...", "options": [...]}` |
| POST | `/rag/check_answer/` | Verifica a resposta do usuário e retorna uma explicação baseada nos documentos | `{"topic": "...", "question": "...", "chosen_option": "...", "correct_option": "..."}` | `{"is_correct": true/false, "explanation": "..."}` |
| GET | `/rag/status/` | Verifica o status do módulo RAG e o modelo em uso | Nenhum | `{"status": "ok", "docs": N, "model": "gemini-2.5-flash"}` |

---

## 4. Arquitetura do Frontend

### 4.1. Visão Geral

- **Tecnologias:** HTML5, CSS3 e JavaScript .
- **Interface:** Simula um chat, onde perguntas e respostas aparecem em balões de mensagem.
- **Endereço do Backend :** `http://127.0.0.1:8000` (definido em `script.js`)

---

### 4.2. Endpoints Consumidos

O frontend utiliza apenas os endpoints principais do módulo `/create`:

```
http://127.0.0.1:8000/create/generate_mcq/
http://127.0.0.1:8000/create/check_answer/

```

---

### 4.3. Fluxo de Interação do Usuário (Frontend)

O fluxo de uso do chat pelo usuário é simples e direto, dividido em duas etapas:

**Etapa 1: Gerar a Pergunta**

1. O usuário inicia o processo digitando um tópico (como "História do Brasil" ou "Ciclo da Água") no campo de texto e clica em "Gerar Questão".
2. O frontend envia esse tópico para o backend (especificamente para a rota `/create/generate_mcq/`).
3. O backend usa esse tópico para pesquisar nos documentos, gera uma pergunta de múltipla escolha com o Gemini e a envia de volta para o frontend.
4. A interface exibe a pergunta no chat (como uma mensagem do "ExameForg") e, logo abaixo, mostra os quatro botões de alternativas para o usuário escolher.

**Etapa 2: Verificar a Resposta**

1. O usuário lê a pergunta e clica na alternativa que considera correta.
2. No momento do clique, o frontend envia as informações da jogada para o backend (para a rota `/create/check_answer/`). Isso inclui:
    - O tópico original.
    - O texto da pergunta.
    - A alternativa que o usuário escolheu.
    - A alternativa que era a correta (o frontend sabe disso desde que recebeu a pergunta).
3. O backend recebe esses dados, busca nos documentos a *justificativa* para aquela resposta (usando os 5 vetores mais próximos) e retorna a explicação.
4. O frontend exibe essa explicação final no chat (dizendo se o usuário acertou ou errou e o porquê).
5. Automaticamente, os botões de alternativa desaparecem da tela, encerrando a rodada daquela pergunta e deixando o chat pronto para uma nova.
