import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from config import get_config

async def main():
    # Config'den token al
    config = get_config()
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    
    # Basit handler test
    @dp.message()
    async def test_handler(message: Message):
        print(f"MESAJ ALINDI: {message.text}")
        await message.answer(f"Aldığım mesaj: {message.text}")
    
    print("Test bot başlıyor...")
    print(f"Token: {config.BOT_TOKEN[:20]}...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 