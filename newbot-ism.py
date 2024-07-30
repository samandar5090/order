import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, URLInputFile)
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramNetworkError

API_TOKEN = '5757529329:AAE2k4xGH7GD5_aVY_Z3kO2O0NK4HslLj1w'  # Replace with your API token
CHANNEL_ID = '@testuchunbuyurtma'  # Replace with your channel ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Define keyboard layouts
main_btn = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🍔Burgerlar')],
        [KeyboardButton(text='🌯Lavash')],
        [KeyboardButton(text='🌭Hotdog')]
    ],
    resize_keyboard=True
)

cancel_btn = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='❌Bekor qilish')]],
    resize_keyboard=True
)

class Order(StatesGroup):
    name = State()
    number = State()

# Initialize product data
products = {
    '🍔Burger': {'price': 35000, 'count': 0, 'narx': 0, 'image': 'https://images.squarespace-cdn.com/content/v1/5ec1febb58a4890157c8fbeb/19ebb9ed-4862-46e1-9f7c-4e5876730227/Beetroot-Burger.jpg'},
    '🌯Lavash': {'price': 25000, 'count': 0, 'narx': 0, 'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6jxROdyeSVi9_20268zvZ8GoiZtDTnFohMw&s'},
    '🌭Hotdog': {'price': 15000, 'count': 0, 'narx': 0, 'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQgPx4djwHCusM_yZ0BhPNe0jqlXovLZ-2LfQ&s'}
}

def get_menu(product):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='➖', callback_data=f'minus_{product}'),
         InlineKeyboardButton(text=str(products[product]['count']), callback_data=f'narx_{product}'),
         InlineKeyboardButton(text='➕', callback_data=f'plus_{product}')],
        [InlineKeyboardButton(text=f'{products[product]["narx"]} sum', callback_data=f'umumiy_{product}')],
        [InlineKeyboardButton(text='✅Zakaz berish', callback_data=f'zakaz_{product}')]
    ])

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer('🔽O\'zingizga kerakli bo\'limni tanlang:', reply_markup=main_btn)

@dp.message(F.text.in_(['🍔Burgerlar', '🌯Lavash', '🌭Hotdog']))
async def product_menu(message: Message):
    product = message.text
    product_key = product
    if product == '🍔Burgerlar':
        product_key = '🍔Burger'
    elif product == '🌯Lavash':
        product_key = '🌯Lavash'
    elif product == '🌭Hotdog':
        product_key = '🌭Hotdog'
    
    await message.answer_photo(
        photo=URLInputFile(products[product_key]['image']),
        caption=f'{product}\n\n💸Narxi: {products[product_key]["price"]} sum',
        reply_markup=get_menu(product_key)
    )

@dp.callback_query(F.data.startswith('minus_') | F.data.startswith('plus_') | F.data.startswith('zakaz_'))
async def handle_callback(callback: CallbackQuery, state: FSMContext):
    global products

    data = callback.data
    action, product = data.split('_', 1)

    if action == 'minus' and products[product]['narx'] > 0 and products[product]['count'] > 0:
        products[product]['narx'] -= products[product]['price']
        products[product]['count'] -= 1
    elif action == 'plus':
        products[product]['narx'] += products[product]['price']
        products[product]['count'] += 1
    elif action == 'zakaz':
        # Check if any product has been selected with a quantity greater than 0
        if all(data['count'] == 0 for data in products.values()):
            await callback.answer("❌ Siz hech qanday mahsulot tanlamadingiz!")
            await callback.message.answer("Siz hech qanday mahsulot tanlamadingiz. Iltimos, mahsulot tanlang va qayta urinib ko'ring.", reply_markup=main_btn)
            return

        await callback.answer("✅Buyurtmangiz qabul qilindi!")
        await callback.message.answer("Iltimos, ismingizni kiriting:", reply_markup=cancel_btn)
        await state.set_state(Order.name)
        return

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=get_menu(product))

@dp.message(Order.name)
async def ask_phone(message: Message, state: FSMContext):
    if message.text == '❌Bekor qilish':
        await message.answer('Menyu', reply_markup=main_btn)
        await state.clear()
    else:
        await state.update_data(name=message.text)
        await message.answer("📞Siz bilan bog'lanishimiz uchun telefon raqamingizni yozib yuboring! \n\n💢Masalan: 91 123 45 67", reply_markup=cancel_btn)
        await state.set_state(Order.number)

@dp.message(Order.number)
async def cmd_number(message: Message, state: FSMContext):
    global products

    if message.text == '❌Bekor qilish':
        await message.answer('Menyu', reply_markup=main_btn)
    else:
        user_data = await state.get_data()
        name = user_data.get('name')
        phone_number = message.text

        order_summary = ""
        total_amount = 0
        for product, data in products.items():
            if data['count'] > 0:
                order_summary += f"{product}: {data['count']} ta\n"
                total_amount += data['narx']

        # Format phone number as a clickable link
        phone_link = f"tel:{phone_number}"

        await message.answer('Rahmat, operator siz bilan tez orada bog\'lanadi', reply_markup=main_btn)
        await bot.send_message(
            CHANNEL_ID,
            f'✅Zakaz qabul qilindi\n\n👤Ism: {name}\n{order_summary}💸Jami: {total_amount} sum\n📞[{phone_number}]({phone_link})',
            parse_mode='Markdown'
        )
    # Reset product data
    for product in products:
        products[product]['count'] = 0
        products[product]['narx'] = 0

    await state.clear()

async def main():
    while True:
        try:
            await dp.start_polling(bot)
        except TelegramNetworkError as e:
            print(f'Network error: {e}. Retrying in 5 seconds...')
            await asyncio.sleep(5)
        except Exception as e:
            print(f'Bot encountered an error: {e}')
            await asyncio.sleep(5)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot stopped')
