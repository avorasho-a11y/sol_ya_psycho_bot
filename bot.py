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

СКОРО (не рекомендуй, они ещё не готовы): Тело под стрессом, Сон и тревога, Одна и ок, Кризис смысла, Горе и потери

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
