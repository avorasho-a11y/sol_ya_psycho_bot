import asyncio
import logging
import os
from collections import defaultdict
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

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()
client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

# История диалогов: user_id -> список сообщений
chat_histories: dict[int, list[dict]] = defaultdict(list)
MAX_HISTORY = 20  # максимум сообщений в истории (10 обменов)

SYSTEM_PROMPT = """Ты — психологический помощник проекта SOL & YA (практикующий психолог Шарова Ольга, сайт sol-ya.com).

Твоя роль: тёплый, профессиональный собеседник, который помогает женщинам разобраться в психологических вопросах об отношениях, эмоциях, самооценке и личностном росте. Ты отвечаешь вдумчиво, без осуждения, с заботой.

КУРСЫ И ТЕСТЫ НА САЙТЕ SOL-YA.COM (рекомендуй органично, когда тема подходит):

КУРСЫ (PDF, доставляются на email после оплаты):
• «Токсичные отношения» — когда больно, но уйти невозможно. 12 уроков: газлайтинг, манипуляции, созависимость, выход. sol-ya.com/courses/toxic
• «Тревожная привязанность» — цепляешься, ревнуешь, боишься потерять. КПТ + EMDR-элементы, 12 уроков. sol-ya.com/courses/anxious
• «Антивыгорание» — когда устала от всего. sol-ya.com/courses/burnout
• «Мама, отпусти!» — сепарация от родителей. sol-ya.com/courses/separation
• «Прокрастинация» — почему откладываем и как перестать. sol-ya.com/courses/procrastination
• «Самооценка» — восстановление отношений с собой. sol-ya.com/courses/self-esteem
• «Границы» — как выстраивать и защищать. sol-ya.com/courses/boundaries
• «Тревога» — работа с тревожными состояниями. sol-ya.com/courses/anxiety

ТЕСТЫ (бесплатные, на сайте):
• Тест на тип привязанности — sol-ya.com/tests/attachment
• Тест на уровень выгорания — sol-ya.com/tests/burnout
• Тест на токсичность отношений — sol-ya.com/tests/toxic
• Тест на уровень тревоги — sol-ya.com/tests/anxiety
• Тест на самооценку — sol-ya.com/tests/self-esteem

КОНСУЛЬТАЦИИ с Ольгой: sol-ya.com/consultation

ПРАВИЛА РАБОТЫ:
1. Сначала выслушай и поддержи — не торопись с советами и рекомендациями
2. Рекомендуй курс или тест только когда это реально уместно (не в каждом сообщении)
3. Если человек описывает острый кризис, насилие или суицидальные мысли — мягко направь к живому специалисту и на консультацию к Ольге
4. Отвечай на русском языке, тепло и без канцелярита
5. Ответы не слишком длинные — 3-5 абзацев максимум
6. Не ставь диагнозов, не давай медицинских советов
7. Ты бесплатный помощник — курсы рекомендуй как возможность углубиться, не навязывай

Начни разговор с тёплого приветствия, если это первое сообщение."""


@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    chat_histories[user_id].clear()  # сбрасываем историю при /start

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
        "📚 Порекомендую курс или тест если это будет уместно\n\n"
        "*Команды:*\n"
        "/start — начать\n"
        "/reset — очистить историю разговора\n"
        "/courses — список курсов\n"
        "/tests — бесплатные тесты\n\n"
        "Сайт: [sol-ya.com](https://sol-ya.com)"
    )
    await message.answer(help_text)


@dp.message(Command("courses"))
async def cmd_courses(message: Message):
    courses_text = (
        "*Курсы SOL & YA* 📚\n\n"
        "🔸 [Токсичные отношения](https://sol-ya.com/courses/toxic) — когда больно, но уйти невозможно\n"
        "🔸 [Тревожная привязанность](https://sol-ya.com/courses/anxious) — ревность, страх потери, цепляние\n"
        "🔸 [Антивыгорание](https://sol-ya.com/courses/burnout) — когда устала от всего\n"
        "🔸 [Мама, отпусти!](https://sol-ya.com/courses/separation) — сепарация от родителей\n"
        "🔸 [Прокрастинация](https://sol-ya.com/courses/procrastination) — почему откладываем\n"
        "🔸 [Самооценка](https://sol-ya.com/courses/self-esteem) — восстановление отношений с собой\n"
        "🔸 [Границы](https://sol-ya.com/courses/boundaries) — как выстраивать и защищать\n"
        "🔸 [Тревога](https://sol-ya.com/courses/anxiety) — работа с тревожными состояниями\n\n"
        "Все курсы — PDF с теорией, практиками и заданиями. Доставляются на email.\n"
        "Полный список: [sol-ya.com/courses](https://sol-ya.com/courses)"
    )
    await message.answer(courses_text)


@dp.message(Command("tests"))
async def cmd_tests(message: Message):
    tests_text = (
        "*Бесплатные тесты* 🔍\n\n"
        "✅ [Тип привязанности](https://sol-ya.com/tests/attachment)\n"
        "✅ [Уровень выгорания](https://sol-ya.com/tests/burnout)\n"
        "✅ [Токсичность отношений](https://sol-ya.com/tests/toxic)\n"
        "✅ [Уровень тревоги](https://sol-ya.com/tests/anxiety)\n"
        "✅ [Самооценка](https://sol-ya.com/tests/self-esteem)\n\n"
        "Все тесты бесплатны, результат приходит на email 📧"
    )
    await message.answer(tests_text)


@dp.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    user_text = message.text.strip()

    if not user_text:
        return

    # Добавляем сообщение пользователя в историю
    chat_histories[user_id].append({
        "role": "user",
        "content": user_text
    })

    # Обрезаем историю если слишком длинная
    if len(chat_histories[user_id]) > MAX_HISTORY:
        chat_histories[user_id] = chat_histories[user_id][-MAX_HISTORY:]

    # Показываем "печатает..."
    await bot.send_chat_action(message.chat.id, "typing")

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=chat_histories[user_id]
        )

        assistant_reply = response.content[0].text

        # Добавляем ответ ассистента в историю
        chat_histories[user_id].append({
            "role": "assistant",
            "content": assistant_reply
        })

        await message.answer(assistant_reply)

    except Exception as e:
        logger.error(f"Ошибка API: {e}")
        await message.answer(
            "Что-то пошло не так 😔 Попробуй написать ещё раз — я здесь."
        )


async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать разговор"),
        BotCommand(command="reset", description="Очистить историю"),
        BotCommand(command="courses", description="Все курсы"),
        BotCommand(command="tests", description="Бесплатные тесты"),
        BotCommand(command="help", description="Помощь"),
    ])

    logger.info("Бот запущен ✅")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
