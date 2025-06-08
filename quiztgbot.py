import asyncio
import json
import random
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = "7338909037:AAED7iP52s5ErSe0bFlhX3JIeNHWAdIrBqk"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ========== ФУНКЦИИ ========== #

# Список вопросов
def load_questions(filename="questions.json"):
    with open(filename, encoding="utf-8") as f:
        return json.load(f)
    
QUESTIONS = load_questions("C:/Users/helpz/Desktop/project/questions.json")

user_sessions = {}

async def send_question(user_id: int):
    session = user_sessions.get(user_id)
    if session is None:
        return
    # Отправка следующего вопроса если они есть
    if session["current"] < len(session["questions"]):
        current_q = session["questions"][session["current"]]
        text = f"Вопрос {session['current']+1}/{len(session['questions'])}: {current_q['question']}"
        
        # Создание списка кнопок | Каждая кнопка находится в своем ряду
        buttons = [
            [InlineKeyboardButton(text=option, callback_data=f"quiz:{idx}")]
            for idx, option in enumerate(current_q["options"])
        ]
        # Передача сформированного списка в inline_keyboard
        kb = InlineKeyboardMarkup(inline_keyboard=buttons, row_width=1)
        await bot.send_message(user_id, text, reply_markup=kb)
    else:
        # Викторина завершена | Отправка результата и очистка сессии
        score = session["score"]
        total = len(session["questions"])
        await bot.send_message(user_id, f"🎊 Поздравляю, викторина завершена!\n✅ Ваш результат: {score}/{total}\n📊 Посмотреть свою статистику: /stats")
        user_sessions.pop(user_id)

#lambda c: c.data and c.data.startswith
@dp.callback_query(F.data.startswith("quiz:"))
async def process_answer(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    session = user_sessions.get(user_id)
    if session is None:
        await callback_query.answer("Сначала начните викторину командой /quiz 😅")
        return
    try:
        # Извлечение выбранного варианта из callback_data
        answer_idx = int(callback_query.data.split(":")[1])
    except (IndexError, ValueError):
        await callback_query.answer("Неверные данные 🥲")
        return

    current_q = session["questions"][session["current"]]
    correct = current_q["correct"]

    # Проверка на правильный ответ
    if answer_idx == correct:
        session["score"] += 1
        await callback_query.answer("😇 Верно! Продолжай в том же духе.", show_alert=True)
    else:
        # Неверный ответ
        correct_option = current_q["options"][correct]
        await callback_query.answer(f"❌ Неверно! Правильный ответ: {correct_option}", show_alert=True)

    # Переход к следующему вопросу
    session["current"] += 1
    await send_question(user_id)

# ========== ВЫБОР КОЛ-ВА ВОПРОСОВ ========== #

@dp.callback_query(F.data.startswith("quiz_amount:"))
async def choose_quiz_amount(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    try:
        amount = int(callback_query.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await callback_query.answer("Неверные данные! 🐽", show_alert=True)
        return

    if len(QUESTIONS) >= amount:
        selected = random.sample(QUESTIONS, amount)
    else:
        selected = QUESTIONS.copy()

    user_sessions[user_id] = {
        "questions": selected,
        "current": 0,
        "score": 0
    }

    await callback_query.message.edit_text(
        f"✅ Вы выбрали квиз из {len(selected)} вопросов. Поехали!"
    )
    await callback_query.answer()

    await send_question(user_id)

# ========== КОМАНДЫ ========== #

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я quiz-бот и могу устроить небольшую викторину. 🎉\nПо очередности, я буду выдавать вопросы и варианты ответа для них, а твоя задача - выбрать правильный вариант ответа. 📌\nЕсли хочешь попробовать, пропиши команду /quiz 🎁\n\nДля дополнительной помощи обращайся через команду /help 😉")

# Команда /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Подробная информация о викторинах:\n\n1. Викторина начинается с помощью команды /quiz\n2. После старта, будет всего 10 случайных вопросов на которые будут даваться по 3 варианта ответа и только 1 из них правильный.\n3. После завершения викторины, тебе начисляться очки рейтинга а также количество правильных ответов в твоей личной статистике пополнится.\n\nКстати, про статистику, её можно посмотреть используя команду /stats")

# Команда /quiz 
@dp.message(Command("quiz"))
async def start_quiz(message: Message):
    # Формируем три кнопки с вариантами: 10, 25, 40 вопросов
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="10 вопросов", callback_data="quiz_amount:10")],
            [InlineKeyboardButton(text="25 вопросов", callback_data="quiz_amount:25")],
            [InlineKeyboardButton(text="40 вопросов", callback_data="quiz_amount:40")]
        ]
    )
    await message.answer("♻️ Выберите, сколько вопросов вы хотите пройти", reply_markup=kb)

# Команда /stats (soon)

# Команда /leaderboard (soon)

# ========== ЗАПУСК ========== #

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) # Логи
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен...")
