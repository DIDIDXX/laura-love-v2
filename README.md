<p align="center">
  <img src="https://placehold.co/1200x350/1f2937/ffffff/png?text=Laura+Love" alt="Capa do Projeto" />
</p>

<h1 align="center">💗 Laura Love</h1>

<p align="center">
  <img alt="version" src="https://img.shields.io/badge/version-v2.0-blue?style=for-the-badge" />
  <img alt="license" src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" />
  <img alt="status" src="https://img.shields.io/badge/status-active-success?style=for-the-badge" />
  <img alt="python" src="https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
</p>

<p align="center">
  Bot de mensagens carinhosas e divertidas para Laura no X (Twitter) 💬✨
  <br/>
  Orquestração segura com `DRY_RUN`, rotação de 10 tons configurável, e agendamento automático.
</p>

---

## ✨ Recursos
- 🎨 Rotação de tom inteligente: evita repetição usando janela configurável (`TONE_ROTATION_WINDOW`).
- 🧠 Classificação de tom dos tweets anteriores para auditoria de estilo.
- 🛡️ Modo seguro (`DRY_RUN`) para não publicar enquanto testa.
- ⏱️ Agendador integrado (cron) replicando rotinas de bom dia/boa noite.
- 🧾 Persistência em SQLite (`tweets.db`) com `type=function:tone_key`.
- 🔑 Configuração via `.env` com exemplos em `.env-example`.

---

## 🚀 Começando

### Pré-requisitos
- `Python 3.10+`
- `pip`

### Instalação
1. Clone o repositório:
   ```bash
   git clone https://github.com/DIDIDXX/laura-love-v2.git
   cd laura-love-v2
   ```
2. Instale dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure o ambiente:
   - Copie `.env-example` para `.env` e ajuste valores.
   - Mantenha `.env` fora do versionamento (já incluído no `.gitignore`).

### Variáveis de ambiente

| Variável | Descrição | Exemplo |
|---------|-----------|---------|
| `DRY_RUN` | Evita envio real no Twitter | `true` |
| `OPENROUTER_API_KEY` | API key do OpenRouter | `sk-...` |
| `TONE_ROTATION_WINDOW` | Janela de rotação de tom | `5` |
| `TWITTER_CONSUMER_KEY` | Credencial cliente | `...` |
| `TWITTER_CONSUMER_SECRET` | Segredo cliente | `...` |
| `TWITTER_ACCESS_KEY` | Token de acesso | `...` |
| `TWITTER_ACCESS_SECRET` | Segredo do token | `...` |

> Dica: mantenha `DRY_RUN=true` enquanto valida.

---

## 🧩 Como usar

### Ação única (CLI)
```bash
python3 main.py --acao boa_noite --dry-run
```

Outras ações disponíveis: `bom_dia`, `boa_tarde`, `sextou_bom_dia`, `sextou_boa_tarde`.

### Agendar rotinas
```bash
python3 main.py --schedule
```
- `bom_dia` 10:00 em `mon, tue, wed, thu`
- `sextou_bom_dia` 10:00 em `fri`
- `bom_dia` 13:00 em `sat, sun`
- `boa_noite` diariamente às `01:30`

### Exemplo de publicação real
```bash
# Ajuste .env com credenciais do Twitter e DRY_RUN=false
python3 main.py --acao boa_noite
```

---

## 🤝 Contribuição
- Faça um fork e crie um branch descritivo: `feature/tone-rotation-10`.
- Siga o padrão de mensagens de commit claras.
- Abra PR com contexto, screenshots/logs quando relevante.
- Não versionar `.env` (use `.env-example`).

Checklist de PR
- [ ] Mantém estilo e simplicidade do código.
- [ ] Não quebra rotinas do scheduler.
- [ ] Atualiza documentação quando necessário.

---

## 📄 Licença
Este projeto usa licença MIT. Verifique/adicione o arquivo `LICENSE` no repositório conforme sua necessidade.

---

## 📚 Links úteis
- Repositório v2: https://github.com/DIDIDXX/laura-love-v2
- OpenRouter: https://openrouter.ai/
- Tweepy: https://www.tweepy.org/
- APScheduler: https://apscheduler.readthedocs.io/

---

## 👋 Boas-vindas
Seja bem-vindo(a)! Este projeto nasceu para espalhar mensagens carinhosas e leves, com um toque de inteligência e cuidado no estilo. Fique à vontade para explorar, deixar sua estrela ⭐️ e contribuir!.

### Chamada para ação
- ⭐️ Dê uma star
- 🍴 Faça um fork
- 🧑‍💻 Abra uma issue ou PR

---

## 📬 Contato dos mantenedores
- GitHub: `@DIDIDXX`
- GitHub: `@ALRCRUZ`