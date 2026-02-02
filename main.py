import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from token import TOKEN
from leetcode_services import is_solve_today, get_count_solved_problems

BOT_TOKEN = TOKEN
DB_NAME = "users.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler()

# ================== FSM STATE ==================

class Form(StatesGroup):
    waiting_for_username = State()


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            username TEXT
        )
        """)
        await db.commit()

# ================== BUTTONS ==================

def main_keyboard():
    kb = [
        [types.KeyboardButton(text="📊 Stats")],
        [types.KeyboardButton(text="👤 Username o‘rnatish")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# ================== HANDLERS ==================

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Botga xush kelibsiz 👋", reply_markup=main_keyboard())

@dp.message(F.text == "👤 Username o‘rnatish")
async def set_username_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.waiting_for_username)
    await message.answer("LeetCode username yuboring:")

@dp.message(Form.waiting_for_username)
async def save_username(message: types.Message, state: FSMContext):
    username = message.text.strip()

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO users (tg_id, username) VALUES (?, ?)",
            (message.from_user.id, username)
        )
        await db.commit()

    await state.clear()
    await message.answer(f"✅ Username saqlandi: {username}", reply_markup=main_keyboard())

@dp.message(F.text == "📊 Stats")
async def stats_cmd(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT username FROM users WHERE tg_id=?", (message.from_user.id,)) as cur:
            row = await cur.fetchone()

    if not row:
        return await message.answer("Avval username o‘rnating.")

    username = row[0]
    data = get_count_solved_problems(username)
    stats = data["data"]["matchedUser"]["submitStats"]["acSubmissionNum"]

    text = "📊 LeetCode Statistika:\n\n"
    for item in stats:
        text += f"{item['difficulty']}: {item['count']}\n"

    await message.answer(text)

# ================== SCHEDULER ==================

async def check_users():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT tg_id, username FROM users") as cur:
            users = await cur.fetchall()

    for tg_id, username in users:
        try:
            if not is_solve_today(username):
                await bot.send_message(
                    tg_id,
                    f"⏰ {username}, bugun hali masala ishlamading.\nKamida 1 ta yechib qo‘y 💪"
                )
        except Exception as e:
            print(f"Xatolik {username}: {e}")

# ================== MAIN ==================

async def main():
    await init_db()
    scheduler.add_job(check_users, "interval", hours=1)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
