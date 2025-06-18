import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import os

API_TOKEN = "7765881253:AAGeSg759wEnbkrqIINg3gK6xfyCeco3SPw"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

ORDERS_FILE = 'orders.json'
if not os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, 'w') as f:
        json.dump([], f)

# ——— Стан замовлення ———
class OrderStates(StatesGroup):
    device = State()
    problem = State()
    name = State()
    phone = State()

# ——— Меню користувача ———
menu_kb = ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [
    KeyboardButton("📱 Заявка на ремонт"),
    KeyboardButton("🧠 Діагностика"),
    KeyboardButton("💰 Прайс"),
    KeyboardButton("📞 Контакти"),
    KeyboardButton("📦 Статус завдання"),
    KeyboardButton("ℹ️ FAQ"),
]
menu_kb.add(*buttons)

# ——— Команди ———
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(
        "Вітаю! Я – сервис‑бот для ремонту техніки.\nОберіть дію в меню нижче ⤵️",
        reply_markup=menu_kb
    )

# ——— Нова заявка ———
@dp.message_handler(lambda m: m.text == "📱 Заявка на ремонт")
async def cmd_new_order(message: types.Message):
    await OrderStates.device.set()
    await message.answer("🔧 На якому пристрої потрібен ремонт? (смартфон/ноутбук/ПК)")

@dp.message_handler(state=OrderStates.device)
async def state_device(message: types.Message, state: FSMContext):
    await state.update_data(device=message.text)
    await OrderStates.next()
    await message.answer("Опишіть проблему:")

@dp.message_handler(state=OrderStates.problem)
async def state_problem(message: types.Message, state: FSMContext):
    await state.update_data(problem=message.text)
    await OrderStates.next()
    await message.answer("Ваше ім’я:")

@dp.message_handler(state=OrderStates.name)
async def state_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await OrderStates.next()
    await message.answer("Номер телефону:")

@dp.message_handler(state=OrderStates.phone)
async def state_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data['phone'] = message.text

    # збереження
    with open(ORDERS_FILE, 'r+') as f:
        orders = json.load(f)
        order_id = len(orders) + 1
        orders.append({**data, "id": order_id, "status": "очікує діагностики"})
        f.seek(0), f.truncate()
        json.dump(orders, f, ensure_ascii=False, indent=2)

    await message.answer(f"✅ Замовлення #{order_id} прийнято. Наш менеджер зателефонує найближчим часом.")
    await state.finish()

# ——— Діагностика ———
@dp.message_handler(lambda m: m.text == "🧠 Діагностика")
async def cmd_diag(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Так", "Ні")
    await message.answer("📱 Вмикається пристрій?", reply_markup=kb)
    await OrderStates.device.set()

@dp.message_handler(state=OrderStates.device)
async def diag_step_device(message: types.Message, state: FSMContext):
    answer = message.text.lower()
    if answer == 'ні':
        await message.answer("Чи заряджається пристрій?", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("Так","Ні"))
        await OrderStates.next()
    else:
        await message.answer("Сенсор працює? (Так/Ні)")
        await OrderStates.next()

@dp.message_handler(state=OrderStates.problem)
async def diag_step_problem(message: types.Message, state: FSMContext):
    await message.answer("Дякую за відповіді. Ми зорієнтуємо вартість і повідомимо найближчим часом.", reply_markup=menu_kb)
    await state.finish()

# ——— Прайс ———
@dp.message_handler(lambda m: m.text == "💰 Прайс")
async def cmd_price(message: types.Message):
    await message.answer_document(InputFile("price_list.pdf"), caption="Ознайомтеся з нашим прайс‑листом.")

# ——— Контакти ———
@dp.message_handler(lambda m: m.text == "📞 Контакти")
async def cmd_contacts(message: types.Message):
    await message.answer(
        "🏠 Адреса: м. Калинівка, вул. Центральна 10\n"
        "📞 Телефон: +38 (097) 000‑00‑00\n"
        "🕘 Пн–Сб 9:00–18:00\n"
        "🌐 Сайт: https://your‑service.com"
    )

# ——— Статус ———
@dp.message_handler(lambda m: m.text == "📦 Статус завдання")
async def cmd_status(message: types.Message):
    await message.answer("Введіть номер замовлення (напр. 1):")

@dp.message_handler(lambda m: m.text.isdigit())
async def status_lookup(message: types.Message):
    oid = int(message.text)
    with open(ORDERS_FILE) as f:
        orders = json.load(f)
    for o in orders:
        if o["id"] == oid:
            await message.answer(f"📌 Статус замовлення #{oid}: {o['status']}")
            return
    await message.answer("⚠️ Замовлення з таким номером не знайдено.")

# ——— FAQ ———
@dp.message_handler(lambda m: m.text == "ℹ️ FAQ")
async def cmd_faq(message: types.Message):
    await message.answer(
        "ℹ️ *Часті запитання:*\n"
        "1. *Гарантійні умови?* – 3 місяці на роботи.\n"
        "2. *Скільки триває ремонт?* – до 5 робочих днів.\n"
        "3. *Як доставити?* – Принесіть самостійно або домовимося про кур'єра.\n"
        "4. *Бренди?* – Apple, Samsung, Xiaomi, Asus, HP, Dell та інші."
    , parse_mode="Markdown")

# ——— Обробка кнопок /menu ———
@dp.message_handler(lambda m: m.text == "/menu")
async def cmd_menu(message: types.Message):
    await message.answer("Меню:", reply_markup=menu_kb)

# ——— Ловимо інше ———
@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer("Не зрозумів 😕 Спробуйте /menu або оберіть одну з кнопок.")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
