

# 🧠 Documentação do Protótipo - ExamForge

Este documento descreve o processo de configuração, execução e funcionamento do **protótipo ExamForge**, apresentado em **17/10**.

---

## 1. Passo a Passo para Rodar o Projeto

### 🧩 1.1. Clonar o Repositório

```bash
git clone https://github.com/Gabriel-marques-araujo/ExamForge.git
```

Em seguida, mude para a **branch do protótipo**:

```bash
git checkout prototipo
```

---

### 📁 1.2. Acessar o Diretório do Backend

```bash
cd backend
```

---

### ⚙️ 1.3. Instalar as Dependências

```bash
pip install -r requirements.txt
```

---

### 🔑 1.4. Criar o Arquivo `.env`

Na raiz da pasta **backend**, crie um arquivo chamado `.env` e adicione sua chave da API do Gemini:

```
GEMINI_API_KEY=coloque_sua_chave_aqui
```

---

### 🚀 1.5. Rodar o Servidor FastAPI

Certifique-se de estar dentro da pasta **backend** e execute:

```bash
uvicorn main:app --reload
```

O servidor será iniciado em:

```
http://127.0.0.1:8000/
```

---

## 2. Testando o Projeto

### 🌐 Interface Inicial

Acesse:

```
http://127.0.0.1:8000/
```

Você verá a mensagem:

```
“Projeto ExamForge”
```

---

### 🧭 Swagger (Documentação Interativa)

Para testar as rotas do backend, acesse:

```
http://127.0.0.1:8000/docs
```

Isso abrirá a interface **Swagger**, permitindo executar requisições diretamente.

---

### 📤 Upload de Documentos

Inicialmente, o projeto não contém a pasta `documentos/`.
Envie um arquivo via endpoint:

```
POST /base/upload/
```

O sistema criará automaticamente a pasta e armazenará o arquivo enviado.

> 💡 **Exemplo usado no protótipo:**
> O documento utilizado para teste foi sobre Programação Orientada a Objetos (POO) — o arquivo está armazenado na pasta `./documentos/.`
---

### 🧩 Criação do Banco Vetorial

Depois de enviar o documento, crie o banco vetorial via:

```
POST /base/create/
```

Clique em **“Try it out”** → **“Execute”** no Swagger.
A resposta confirmará a indexação, por exemplo:

```json
{"message": "Banco de dados criado com 18 chunks."}
```

---

### 🧠 Geração de Perguntas

Com o banco criado, gere perguntas com:

```
POST /rag/generate_mcq/
```

Envie um tópico relacionado ao conteúdo do documento.
Exemplo:

```json
{"topic": "Pilares da Programação Orientada a Objetos"}
```

A API retornará algo como:

```json
{
  "question": "Qual dos seguintes é considerado um dos quatro pilares da Programação Orientada a Objetos?",
  "options": ["Funções", "Encapsulamento", "Recursão", "Compilação"],
  "correct_option": "Encapsulamento"
}
```

---

### ✅ Verificação de Resposta

Para validar uma resposta e obter explicação:

```
POST /rag/check_answer/
```

Exemplo de corpo:

```json
{
  "topic": "POO",
  "question": "Qual dos seguintes é um dos pilares da Programação Orientada a Objetos?",
  "chosen_option": "Recursão",
  "correct_option": "Encapsulamento"
}
```

Retorno:

```json
{
  "is_correct": false,
  "explanation": "Encapsulamento é um dos quatro pilares da POO. Ele agrupa dados e métodos dentro de uma classe, protegendo informações internas do objeto."
}
```

---

## 3. Estrutura Técnica do Projeto

### ⚙️ Backend

* **Framework:** FastAPI
* **Servidor:** Uvicorn
* **IA (RAG):**

  * **Modelo de Geração:** Google Gemini (`gemini-2.5-flash`)
  * **Orquestração:** LangChain
  * **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2`
  * **Banco Vetorial:** ChromaDB

#### Processo de Ingestão (Chunking)

| Parâmetro        | Valor                          |
| ---------------- | ------------------------------ |
| Método           | RecursiveCharacterTextSplitter |
| Tamanho do Chunk | 1000 caracteres                |
| Sobreposição     | 0 caracteres                   |

#### Estrutura de Pastas

| Pasta          | Função                                        |
| -------------- | --------------------------------------------- |
| `./documentos` | Armazena os arquivos enviados pelo usuário    |
| `./chroma`     | Banco vetorial criado a partir dos embeddings |
| `.env`         | Contém a chave da API do Gemini               |

---

### 📡 Endpoints Principais

| Módulo              | Prefixo | Função                            |
| ------------------- | ------- | --------------------------------- |
| **Raiz**            | `/`     | Verificação da API                |
| **Base**            | `/base` | Upload e criação da base vetorial |
| **RAG (Perguntas)** | `/rag`  | Geração e correção de perguntas   |

---

## 4. Frontend

### 🔍 Visão Geral

* **Tecnologias:** HTML5, CSS3, JavaScript
* **Interface:** Chat com balões de perguntas e respostas
* **Backend:** `http://127.0.0.1:8000`

### Fluxo do Usuário

1. Usuário digita um **tópico** → clica em **Gerar Questão**.
2. O frontend envia para `/rag/generate_mcq/`.
3. A pergunta e opções são exibidas no chat.
4. Ao escolher uma resposta, o frontend chama `/rag/check_answer/`.
5. O sistema retorna se acertou e exibe a explicação.

---

## 5. 📘 Documento Utilizado na Apresentação do Protótipo

Nesta etapa, foi utilizado o **documento de apoio** intitulado:

> **“Introdução à Programação Orientada a Objetos (POO)”**

Esse material serviu como **base de conhecimento** para o sistema **RAG (Retrieval-Augmented Generation)**, sendo o **conteúdo oficial empregado na apresentação do protótipo**.

Durante a demonstração prática do **ExamForge**, o documento foi utilizado para **gerar perguntas, respostas e explicações automáticas**, evidenciando a capacidade do sistema de compreender e explorar conteúdos técnicos.

📂 **Localização do arquivo:**  
`cd backend/documentos/Introdução à Programação Orientad.txt`

## 6. 🎥 Vídeo do Protótipo

Este vídeo apresenta a **demonstração prática do ExamForge**, mostrando o funcionamento integrado entre o **frontend** e o **backend**.

Durante o teste, foi utilizado o documento de apoio **“Introdução à Programação Orientada a Objetos (POO)”**, presente na pasta `./documentos/`.

No vídeo, o usuário digita tópicos relacionados ao conteúdo do documento — como **Herança** e **Polimorfismo** — e o sistema:

1. Gera automaticamente **questões de múltipla escolha (MCQ)** com base na base de conhecimento criada.  
2. Permite que o usuário escolha uma alternativa diretamente no frontend.  
3. Retorna o **veredito da resposta** (correta ou incorreta) e uma **explicação contextual** baseada no documento original.  

🎬 **O vídeo está disponível no YouTube:**  
[🔗 Assista à apresentação do protótipo ExamForge](https://youtu.be/Jjl6ILS0heg)

> Este vídeo foi utilizado como parte da apresentação do protótipo em 17/10, ilustrando o funcionamento completo do sistema ExamForge.










