# FORGE — Personal Trainer IA 🔱

Plataforma completa de personal trainer com Inteligência Artificial.

---

## ▶️ Como Usar

### Opção 1 — Abrir direto no navegador (sem instalar nada)
Abra o arquivo `static/index.html` no seu navegador.

### Opção 2 — Servidor Python (recomendado)
```bash
pip install flask
python forge_server.py
```
O app abre automaticamente em http://localhost:5050

### Opção 3 — Gerar .exe para Windows
```
1. Instale Python 3.10+ em https://python.org
2. Execute build_windows.bat (duplo clique)
3. O .exe estará em dist/forge/forge.exe
```

---

## 🔐 Acesso Administrativo
- **Usuário:** admin  
- **Senha:** forge123

O painel admin permite ver todos os alunos, status online, último acesso, progresso e gerenciar acessos.

---

## 🔑 API Key (opcional)
Para usar a IA da Anthropic, defina a variável de ambiente:
```
ANTHROPIC_API_KEY=sua_chave_aqui
```
Sem ela, o app usa dados inteligentes pré-gerados que funcionam perfeitamente.

---

## 📱 Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| 📋 Cadastro em 5 etapas | Dados pessoais, objetivo, avaliação muscular, equipamentos e medidas |
| 💪 Treino personalizado | Plano semanal completo com exercícios, séries e pausas |
| ▶️ Sessão ao vivo | Timer, registro de peso/reps por set, histórico |
| 📈 Gráficos | Evolução de carga, medidas e peso ao longo do tempo |
| 🥗 Dieta completa | 6 refeições com macros detalhados |
| 📷 Fotos antes/depois | Upload e galeria de progresso |
| 📏 Medidas | 8 medidas corporais com comparativo de evolução |
| 🗺️ Estratégia | Periodização e linha do tempo até o objetivo |
| 🔐 Admin | Gestão de alunos, status online, último acesso |
| 🌙☀️ Tema | Modo claro e escuro |

---

## 🛠️ Tecnologias
- **Frontend:** HTML5 + CSS3 + JavaScript (vanilla)
- **Gráficos:** Chart.js 4.4
- **Backend:** Python 3 + Flask
- **IA:** Claude API (Anthropic)
- **Build:** PyInstaller
