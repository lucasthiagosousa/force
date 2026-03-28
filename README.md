# FORGE — Personal Trainer IA 🔱
**Plataforma completa de personal trainer com inteligência artificial**

---

## 📋 Índice
1. [Como Abrir (Sem Instalar Nada)](#1-como-abrir-sem-instalar-nada)
2. [Como Rodar com Python](#2-como-rodar-com-python)
3. [Como Gerar o .exe para Windows](#3-como-gerar-o-exe-para-windows)
4. [Como Colocar Online (Render.com — Grátis)](#4-como-colocar-online-rendercom--grátis)
5. [Configurações de E-mail e IA](#5-configurações-de-e-mail-e-ia)
6. [Acesso de Admin](#6-acesso-de-admin)
7. [O que o App Faz](#7-o-que-o-app-faz)

---

## 1. Como Abrir (Sem Instalar Nada)

Abra o arquivo `static/index.html` diretamente no navegador Chrome, Edge ou Firefox.  
Todos os dados ficam salvos no seu navegador (localStorage).

---

## 2. Como Rodar com Python

```bash
# No terminal (dentro da pasta forge/)
pip install flask PyJWT
python forge_server.py
```
O app abre automaticamente em **http://localhost:5050**

---

## 3. Como Gerar o .exe para Windows

1. Instale Python em https://python.org (**marque "Add Python to PATH"**)
2. Dê duplo clique em `build_windows.bat`
3. Aguarde 2-3 minutos
4. O .exe estará em `dist/forge/forge.exe`
5. Copie **toda a pasta** `dist/forge/` para qualquer computador Windows

---

## 4. Como Colocar Online (Render.com — Grátis)

### Passo 1 — Criar conta no GitHub
- Acesse https://github.com e crie uma conta gratuita
- Crie um repositório chamado **forge**
- Suba os arquivos com os comandos:
  ```
  git init
  git add .
  git commit -m "FORGE v3"
  git remote add origin https://github.com/SEU_USUARIO/forge.git
  git push -u origin main
  ```

### Passo 2 — Criar conta no Render
- Acesse https://render.com → "Get Started for Free"
- Cadastre-se com sua conta GitHub

### Passo 3 — Criar o Web Service
Clique em **New → Web Service** e configure os campos exatamente assim:

| Campo | Valor |
|---|---|
| **Name** | `forge-app` (ou qualquer nome único) |
| **Language** | `Python 3` |
| **Branch** | `main` |
| **Region** | `Frankfurt (EU Central)` ou mais próxima |
| **Root Directory** | *(deixe em branco)* |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn forge_server:app --bind 0.0.0.0:$PORT --workers 2` |
| **Instance Type** | `Free` |

### Passo 4 — Criar Banco de Dados (opcional, para dados persistentes)
- No Render: **New → PostgreSQL**
- Name: `forge-db`, Plan: `Free`
- Após criar, copie a **Internal Database URL**
- Vá no Web Service → **Environment** → adicione:
  - `DATABASE_URL` = *(cole a URL copiada)*

### Passo 5 — Deploy
- Clique em **Create Web Service**
- Aguarde 3-5 minutos para o primeiro deploy
- Seu app estará em: `https://forge-app.onrender.com`

> ⚠️ **Atenção:** No plano gratuito do Render, o app "dorme" após 15 min sem uso e leva ~30 segundos para acordar na próxima visita. Isso é normal.

---

## 5. Configurações de E-mail e IA

No Render, vá em **Environment Variables** e adicione:

| Variável | Obrigatório | Descrição |
|---|---|---|
| `SECRET_KEY` | ✅ | Chave de segurança. Gere com: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_PASS` | ⭐ Recomendado | Mude a senha padrão do admin |
| `DATABASE_URL` | Para persistência | URL do PostgreSQL (Render ou Supabase) |
| `SMTP_USER` | Para e-mails | Seu e-mail Gmail |
| `SMTP_PASS` | Para e-mails | Senha de app Gmail (16 dígitos sem espaços) |
| `ANTHROPIC_API_KEY` | Para IA real | Chave da API da Anthropic |

### Como criar senha de app Gmail:
1. Acesse myaccount.google.com
2. Segurança → Verificação em duas etapas (ative)
3. Pesquise "Senhas de app" → Criar → Nome: FORGE
4. Copie os 16 dígitos (sem espaços)

---

## 6. Acesso de Admin

**Login padrão:**
- E-mail: `admin@forge.com`
- Senha: `forge123`

O admin usa o **mesmo formulário de login** dos outros usuários — não há campo separado.  
Após login, o menu de admin aparece automaticamente.

**No painel admin você vê:**
- Todos os usuários cadastrados em tempo real
- Data de criação e último acesso
- Status ativo/suspenso
- Botões para suspender ou remover usuários

---

## 7. O que o App Faz

| Funcionalidade | Descrição |
|---|---|
| 🔐 **Auth unificada** | Login, cadastro e recuperação de senha em uma única tela |
| 📧 **Código por e-mail** | Recuperação de senha via código de 6 dígitos |
| 💪 **Treino com IA** | Plano semanal completo com exercícios, séries e pausas |
| 📹 **Vídeos dos exercícios** | YouTube embed para cada exercício na sessão ao vivo |
| ▶️ **Sessão ao vivo** | Timer, registro de peso/reps por set, histórico |
| 🥗 **Dieta por dia** | 7 dias com refeições adaptadas ao treino + dia de refeição livre |
| 🧍 **Silhueta dinâmica** | Corpo SVG que muda cor conforme nível de cada músculo |
| 📊 **Gráficos avançados** | Selecione quais medidas ver no gráfico de evolução |
| 📷 **Antes & Depois** | Upload de fotos e galeria de progresso |
| 📏 **Medidas corporais** | 8 medidas com comparativo de evolução |
| 🔐 **Admin** | Gestão completa de usuários com dados em tempo real |
| 🌙☀️ **Tema** | Claro e escuro com um clique |
| 💾 **Dados salvos** | Tudo no localStorage (offline) ou banco de dados (online) |

---

## Estrutura de Arquivos

```
forge/
├── forge_server.py       ← Servidor Flask com auth e banco
├── forge.spec            ← Config para gerar .exe
├── build_windows.bat     ← Gera o .exe automaticamente
├── requirements.txt      ← Dependências Python
├── Procfile              ← Config para Render/Heroku
├── .gitignore            ← Arquivos ignorados pelo Git
├── README.md             ← Este arquivo
└── static/
    └── index.html        ← App completo (HTML + JS + CSS)
```

---

*FORGE v3.0 — Desenvolvido com Flask + Chart.js + Claude AI*
