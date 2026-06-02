import asyncio
import logging
import os
from collections import defaultdict
from datetime import datetime, time
from anthropic import AsyncAnthropic

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, BotCommand
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))  # твой Telegram ID

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()
client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

# История диалогов
chat_histories: dict[int, list[dict]] = defaultdict(list)
MAX_HISTORY = 20

# Статистика за день
daily_stats: dict = {
    "users": set(),
    "messages": 0,
    "topics": [],
    "courses_mentioned": defaultdict(int),
    "tests_mentioned": defaultdict(int),
    "new_users": set(),
    "user_info": {}  # user_id -> {name, username, first_seen}
}

SYSTEM_PROMPT = """Ты — психологический помощник проекта SOL & YA (практикующий психолог Шарова Ольга, сайт sol-ya.com).

Твоя роль: тёплый, профессиональный собеседник, который помогает женщинам разобраться в психологических вопросах об отношениях, эмоциях, самооценке и личностном росте. Ты отвечаешь вдумчиво, без осуждения, с заботой.

КУРСЫ И ТЕСТЫ НА САЙТЕ SOL-YA.COM (рекомендуй органично, когда тема подходит):

АКТИВНЫЕ КУРСЫ (PDF, доставляются на email после оплаты):
• «НЕТ тревоге» — https://www.sol-ya.com/courses/net-trevoge
• «Тревожная привязанность» — цепляешься, ревнуешь, боишься потерять. КПТ + EMDR, 12 уроков — https://www.sol-ya.com/courses/trevozhnaya-privyazannost
• «Перестать спасать» — https://www.sol-ya.com/perestat-spasat
• «Токсичные отношения» — когда больно, но уйти невозможно. 12 уроков — https://www.sol-ya.com/courses/toksichnye-otnosheniya
• «Близость без потери себя» — https://www.sol-ya.com/courses/blizost-bez-poteri-sebya
• «Найти опору в себе» — https://www.sol-ya.com/courses/najti-oporu-v-sebe
• «Синдром самозванца» — https://www.sol-ya.com/courses/sindrom-samozvantsa
• «Перфекционизм» — https://www.sol-ya.com/courses/perfektsionizm
• «Мама, отпусти!» — сепарация от родителей — https://www.sol-ya.com/courses/mama-otpusti
• «Антивыгорание» — когда устала от всего — https://www.sol-ya.com/courses/antivigoranie
• «Прокрастинация» — https://www.sol-ya.com/courses/prokrastinatsiya

СКОРО (не рекомендуй): Тело под стрессом, Сон и тревога, Одна и ок, Кризис смысла, Горе и потери

ТЕСТЫ (все бесплатные, на сайте):
• Тест на тревожность (BAI) — https://www.sol-ya.com/tests/beck-anxiety
• Тест на тип привязанности ECR-R — https://www.sol-ya.com/tests/ecr-r
• Шкала осложнённого горя — https://www.sol-ya.com/tests/gore
• Тест на границы в отношениях — https://www.sol-ya.com/tests/granitsy
• Тест качества сна ISI — https://www.sol-ya.com/tests/isi
• Тест треугольник Карпмана — https://www.sol-ya.com/tests/karpman
• Тест на выгорание (MBI Маслач) — https://www.sol-ya.com/tests/maslach
• Тест на перфекционизм FMPS — https://www.sol-ya.com/tests/perfekcionizm
• Тест на прокрастинацию GPS — https://www.sol-ya.com/tests/prokrastinaciya
• Шкала стресса PSS-10 — https://www.sol-ya.com/tests/pss10
• Тест на самооценку Розенберга — https://www.sol-ya.com/tests/rozenberg
• Тест на синдром самозванца — https://www.sol-ya.com/tests/samozvanec
• Тест на сепарацию от родителей — https://www.sol-ya.com/tests/separaciya
• Тест смысложизненных ориентаций — https://www.sol-ya.com/tests/szho
• Шкала одиночества UCLA — https://www.sol-ya.com/tests/ucla
• Тест на газлайтинг VGQ — https://www.sol-ya.com/tests/vgq

БЕСПЛАТНЫЕ СТАТЬИ (рекомендуй когда хочется дать что-то почитать прямо сейчас):
• Тревога: что за ней стоит — https://www.sol-ya.com/articles/trevoga
• Скрытое выгорание — https://www.sol-ya.com/articles/vygoranie
• Тревожная привязанность — https://www.sol-ya.com/articles/trevozhnaya-privyazannost
• Синдром спасателя — https://www.sol-ya.com/articles/spasatelstvo
• Созависимость — https://www.sol-ya.com/articles/sozavisimost
• Прокрастинация — это не лень — https://www.sol-ya.com/articles/prokrastinaciya
• Синдром самозванца — https://www.sol-ya.com/articles/sindrom-samozvanca
• Удобный ребёнок — https://www.sol-ya.com/articles/udobny-rebenok
• Перфекционизм — https://www.sol-ya.com/articles/perfekcionizm
• Дисфункциональная семья — https://www.sol-ya.com/articles/disfunkciya-semi
• Контроль как защита — https://www.sol-ya.com/articles/kontrol
• Тело под стрессом — https://www.sol-ya.com/articles/telo-pod-stressom
• Токсичные отношения — https://www.sol-ya.com/articles/toksichnye-otnosheniya
• Близость без потери себя — https://www.sol-ya.com/articles/blizost-bez-poteri-sebya
• Одна и ок — https://www.sol-ya.com/articles/odna-i-ok

КОНСУЛЬТАЦИИ с Ольгой: https://www.sol-ya.com/consultation

ПРАВИЛА РАБОТЫ:
1. Сначала выслушай и поддержи — не торопись с советами и рекомендациями
2. Рекомендуй курс, тест или статью только когда это реально уместно (не в каждом сообщении)
3. Если человек описывает острый кризис, насилие или суицидальные мысли — мягко направь к живому специалисту и на консультацию к Ольге
4. Отвечай на русском языке, тепло и без канцелярита
5. Ответы не слишком длинные — 3-5 абзацев максимум
6. Не ставь диагнозов, не давай медицинских советов
7. Ты бесплатный помощник — курсы рекомендуй как возможность углубиться, не навязывай"""


def update_stats(user: any, text: str, is_new: bool):
    """Обновляем статистику"""
    uid = user.id
    daily_stats["users"].add(uid)
    daily_stats["messages"] += 1
    if is_new:
        daily_stats["new_users"].add(uid)

    # Сохраняем инфо о пользователе
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Без имени"
    username = f"@{user.username}" if user.username else "нет username"
    if uid not in daily_stats["user_info"]:
        daily_stats["user_info"][uid] = {
            "name": name,
            "username": username,
            "first_seen": datetime.now().strftime("%H:%M")
        }

    # Топ тем — первые слова сообщения
    if len(text) > 10:
        daily_stats["topics"].append(text[:80])

    # Упоминания курсов
    courses = {
        "тревог": "НЕТ тревоге",
        "привязанност": "Тревожная привязанность",
        "токсич": "Токсичные отношения",
        "выгоран": "Антивыгорание",
        "мама": "Мама, отпусти",
        "прокрастин": "Прокрастинация",
        "самозванц": "Синдром самозванца",
        "перфекцион": "Перфекционизм",
        "спасат": "Перестать спасать",
        "близост": "Близость без потери себя",
        "опор": "Найти опору в себе",
    }
    text_lower = text.lower()
    for keyword, course in courses.items():
        if keyword in text_lower:
            daily_stats["courses_mentioned"][course] += 1


async def send_daily_report():
    """Отправляем ежедневный отчёт"""
    if not ADMIN_ID:
        return

    stats = daily_stats
    total_users = len(stats["users"])
    new_users = len(stats["new_users"])
    total_messages = stats["messages"]

    if total_users == 0:
        report = "📊 *Отчёт за сегодня*\n\nСегодня никто не писал боту."
    else:
        report = f"📊 *Отчёт SOL & YA бот — {datetime.now().strftime('%d.%m.%Y')}*\n\n"
        report += f"👥 Всего пользователей: {total_users}\n"
        report += f"🆕 Новых сегодня: {new_users}\n"
        report += f"💬 Сообщений: {total_messages}\n\n"

        # Список пользователей
        if stats["user_info"]:
            report += "👤 *Кто писал:*\n"
            for uid, info in stats["user_info"].items():
                report += f"• {info['name']} ({info['username']}) — с {info['first_seen']}\n"
            report += "\n"

        # Топ тем
        if stats["topics"]:
            report += "🗣 *Темы разговоров:*\n"
            for topic in stats["topics"][:10]:
                report += f"• {topic}\n"
            report += "\n"

        # Упомянутые курсы
        if stats["courses_mentioned"]:
            report += "📚 *Упомянутые курсы:*\n"
            for course, count in sorted(stats["courses_mentioned"].items(),
                                        key=lambda x: x[1], reverse=True):
                report += f"• {course}: {count} раз\n"

    try:
        await bot.send_message(ADMIN_ID, report)
    except Exception as e:
        logger.error(f"Ошибка отправки отчёта: {e}")

    # Сбрасываем статистику
    daily_stats["users"] = set()
    daily_stats["new_users"] = set()
    daily_stats["messages"] = 0
    daily_stats["topics"] = []
    daily_stats["courses_mentioned"] = defaultdict(int)
    daily_stats["tests_mentioned"] = defaultdict(int)
    daily_stats["user_info"] = {}


async def daily_report_scheduler():
    """Планировщик — отправляет отчёт каждый день в 22:00"""
    while True:
        now = datetime.now()
        # Следующая отправка в 22:00
        target = now.replace(hour=19, minute=0, second=0, microsecond=0)
        if now >= target:
            target = target.replace(day=target.day + 1)
        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        await send_daily_report()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    is_new = user_id not in chat_histories or len(chat_histories[user_id]) == 0
    chat_histories[user_id].clear()
    update_stats(message.from_user, "/start", is_new)

    welcome = (
        "Привет 🌿 Я психологический помощник проекта *SOL & YA*.\n\n"
        "Я здесь, чтобы выслушать и помочь разобраться — в отношениях, эмоциях, тревоге, "
        "выгорании или просто в том, что тяжело.\n\n"
        "Расскажи, что сейчас происходит или что тебя беспокоит. "
        "Я отвечу вдумчиво и без осуждения 💙\n\n"
        "_Если хочешь начать заново — напиши /reset_"
    )
    await message.answer(welcome)


@dp.message(Command("reset"))
async def cmd_reset(message: Message):
    user_id = message.from_user.id
    chat_histories[user_id].clear()
    await message.answer(
        "История нашего разговора очищена. Можем начать с чистого листа 🌿\n"
        "Расскажи, что тебя сейчас волнует?"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "*Как я могу помочь:*\n\n"
        "💬 Просто напиши мне — я выслушаю и отвечу\n"
        "🔍 Помогу разобраться в ситуации с отношениями, тревогой, самооценкой\n"
        "📚 Порекомендую курс, тест или статью если это будет уместно\n\n"
        "*Команды:*\n"
        "/start — начать\n"
        "/reset — очистить историю разговора\n"
        "/courses — список курсов\n"
        "/tests — бесплатные тесты\n\n"
        "Сайт: [sol-ya.com](https://www.sol-ya.com)"
    )
    await message.answer(help_text)


@dp.message(Command("courses"))
async def cmd_courses(message: Message):
    courses_text = (
        "*Курсы SOL & YA* 📚\n\n"
        "🔸 [НЕТ тревоге](https://www.sol-ya.com/courses/net-trevoge)\n"
        "🔸 [Тревожная привязанность](https://www.sol-ya.com/courses/trevozhnaya-privyazannost)\n"
        "🔸 [Токсичные отношения](https://www.sol-ya.com/courses/toksichnye-otnosheniya)\n"
        "🔸 [Близость без потери себя](https://www.sol-ya.com/courses/blizost-bez-poteri-sebya)\n"
        "🔸 [Перестать спасать](https://www.sol-ya.com/perestat-spasat)\n"
        "🔸 [Найти опору в себе](https://www.sol-ya.com/courses/najti-oporu-v-sebe)\n"
        "🔸 [Синдром самозванца](https://www.sol-ya.com/courses/sindrom-samozvantsa)\n"
        "🔸 [Перфекционизм](https://www.sol-ya.com/courses/perfektsionizm)\n"
        "🔸 [Мама, отпусти!](https://www.sol-ya.com/courses/mama-otpusti)\n"
        "🔸 [Антивыгорание](https://www.sol-ya.com/courses/antivigoranie)\n"
        "🔸 [Прокрастинация](https://www.sol-ya.com/courses/prokrastinatsiya)\n\n"
        "Все курсы — PDF с теорией, практиками и заданиями. Доставляются на email 📧"
    )
    await message.answer(courses_text)


@dp.message(Command("tests"))
async def cmd_tests(message: Message):
    tests_text = (
        "*Бесплатные тесты* 🔍\n\n"
        "✅ [Тревожность BAI](https://www.sol-ya.com/tests/beck-anxiety)\n"
        "✅ [Тип привязанности ECR-R](https://www.sol-ya.com/tests/ecr-r)\n"
        "✅ [Границы в отношениях](https://www.sol-ya.com/tests/granitsy)\n"
        "✅ [Газлайтинг VGQ](https://www.sol-ya.com/tests/vgq)\n"
        "✅ [Выгорание Маслач](https://www.sol-ya.com/tests/maslach)\n"
        "✅ [Самооценка Розенберга](https://www.sol-ya.com/tests/rozenberg)\n"
        "✅ [Синдром самозванца](https://www.sol-ya.com/tests/samozvanec)\n"
        "✅ [Сепарация от родителей](https://www.sol-ya.com/tests/separaciya)\n"
        "✅ [Перфекционизм FMPS](https://www.sol-ya.com/tests/perfekcionizm)\n"
        "✅ [Прокрастинация GPS](https://www.sol-ya.com/tests/prokrastinaciya)\n"
        "✅ [Стресс PSS-10](https://www.sol-ya.com/tests/pss10)\n"
        "✅ [Треугольник Карпмана](https://www.sol-ya.com/tests/karpman)\n"
        "✅ [Качество сна ISI](https://www.sol-ya.com/tests/isi)\n"
        "✅ [Одиночество UCLA](https://www.sol-ya.com/tests/ucla)\n"
        "✅ [Смысл жизни СЖО](https://www.sol-ya.com/tests/szho)\n"
        "✅ [Осложнённое горе ICG](https://www.sol-ya.com/tests/gore)\n\n"
        "Все тесты бесплатны, результат приходит на email 📧"
    )
    await message.answer(tests_text)


@dp.message(Command("report"))
async def cmd_report(message: Message):
    """Команда для немедленного отчёта (только для админа)"""
    if message.from_user.id != ADMIN_ID:
        return
    await send_daily_report()


@dp.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    user_text = message.text.strip()

    if not user_text:
        return

    is_new = user_id not in chat_histories or len(chat_histories[user_id]) == 0
    update_stats(message.from_user, user_text, is_new)

    chat_histories[user_id].append({"role": "user", "content": user_text})

    if len(chat_histories[user_id]) > MAX_HISTORY:
        chat_histories[user_id] = chat_histories[user_id][-MAX_HISTORY:]

    await bot.send_chat_action(message.chat.id, "typing")

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=chat_histories[user_id]
        )
        assistant_reply = response.content[0].text
        chat_histories[user_id].append({"role": "assistant", "content": assistant_reply})
        await message.answer(assistant_reply)

    except Exception as e:
        logger.error(f"Ошибка API: {e}")
        await message.answer("Что-то пошло не так 😔 Попробуй написать ещё раз — я здесь.")


async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать разговор"),
        BotCommand(command="reset", description="Очистить историю"),
        BotCommand(command="courses", description="Все курсы"),
        BotCommand(command="tests", description="Бесплатные тесты"),
        BotCommand(command="help", description="Помощь"),
    ])

    asyncio.create_task(daily_report_scheduler())
    logger.info("Бот запущен ✅")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
