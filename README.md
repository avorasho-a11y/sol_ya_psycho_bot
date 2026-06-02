# SOL & YA — Telegram Bot

Психологический помощник проекта SOL & YA на базе Claude AI.

## Что делает бот

- Отвечает на психологические вопросы (отношения, тревога, самооценка, выгорание)
- Помнит историю разговора в рамках сессии
- Органично рекомендует курсы и тесты с sol-ya.com
- Команды: /start, /reset, /courses, /tests, /help

---

## Деплой на Railway — пошаговая инструкция

### Шаг 1 — Создать Telegram-бота

1. Открой Telegram, найди **@BotFather**
2. Напиши `/newbot`
3. Придумай имя и username (например `solya_psychology_bot`)
4. Скопируй **BOT_TOKEN** — он выглядит как `123456789:AAF...`

### Шаг 2 — Получить Anthropic API Key

1. Зайди на [console.anthropic.com](https://console.anthropic.com)
2. Settings → API Keys → Create Key
3. Скопируй ключ (начинается с `sk-ant-...`)
4. Пополни баланс — минимум $5, хватит надолго

### Шаг 3 — Загрузить код на GitHub

```bash
cd solya-bot
git init
git add .
git commit -m "initial"
git branch -M main
git remote add origin https://github.com/ВАШ_АККАУНТ/solya-bot.git
git push -u origin main
```

### Шаг 4 — Деплой на Railway

1. Зайди на [railway.app](https://railway.app) и войди через GitHub
2. Нажми **New Project → Deploy from GitHub repo**
3. Выбери репозиторий `solya-bot`
4. Railway сам найдёт Dockerfile и начнёт сборку

### Шаг 5 — Добавить переменные окружения

В Railway: открой проект → вкладка **Variables** → добавь:

| Переменная | Значение |
|---|---|
| `BOT_TOKEN` | токен от BotFather |
| `ANTHROPIC_API_KEY` | ключ от Anthropic |

После добавления Railway автоматически перезапустит бота.

### Шаг 6 — Проверить

Открой бота в Telegram, напиши `/start` — он должен ответить 🎉

---

## Мониторинг

- Логи: Railway → проект → вкладка **Deployments → View Logs**
- Если бот не отвечает — проверь логи на ошибки

## Обновление бота

```bash
git add .
git commit -m "обновление"
git push
```
Railway задеплоит автоматически.

---

## Стоимость

- **Railway**: ~$0-5/месяц (бесплатные кредиты)
- **Claude API**: ~$0.003 за 1000 токенов (≈ 750 слов). При 100 пользователях в день — около $3-10/месяц
