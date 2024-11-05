import requests
import asyncio
import schedule
import time
from telegram import Bot

# Глобальная переменная для счетчика сообщений
msg_counter = 0
telegram_bot = None
chat_id = None
loop = asyncio.get_event_loop()  # Создаем цикл событий один раз

async def send_message(bot: Bot, chat_id: str, message: str) -> None:
    """Асинхронная функция для отправки сообщения в Telegram с использованием Markdown и вывода в консоль"""
    global msg_counter  # Указываем, что используем глобальную переменную
    print(f"Отправленное сообщение:\n{message}")
    await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
    msg_counter += 1  # Увеличиваем счетчик сообщений
    print(f"Общее количество отправленных сообщений: {msg_counter}")  # Выводим текущее значение счетчика

async def send_error(bot: Bot, chat_id: str, error_message: str) -> None:
    """Асинхронная функция для отправки сообщения об ошибке в Telegram"""
    await send_message(bot, chat_id, error_message)

async def get_last_order_price(pair: str, bot: Bot, chat_id: str) -> None:
    """Получает цены ордеров и суточный объём для указанной торговой пары"""
    url = f"https://trade.xrocket.tg/pairs/{pair}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if "data" not in data:
            await send_error(bot, chat_id, "Ответ не содержит данных 'data'.")
            return
        
        # Извлекаем нужные данные
        pair_data = data["data"]
        buy_price = pair_data.get("buyPrice")
        sell_price = pair_data.get("sellPrice")
        last_price = pair_data.get("lastPrice")
        quote_volume_24h = pair_data.get("quoteVolume24h")
        
        # Формируем сообщение
        message = f"PAIR info {pair}:\n\n*price*:\n"
        message += f"*BUY*: {buy_price:.6f}\n" if buy_price is not None else "Нет данных о цене *BUY*\n"
        message += f"*SELL*: {sell_price:.6f}\n" if sell_price is not None else "Нет данных о цене *SELL*\n"
        message += f"last *price*: {last_price:.6f}\n\n" if last_price is not None else "Нет данных о последней цене исполнения\n"
        message += f"*VOL* 24h: {quote_volume_24h:.6f} USDT\n" if quote_volume_24h is not None else "Нет данных о суточном объёме\n"
        
        await send_message(bot, chat_id, message)
    
    except requests.exceptions.RequestException as e:
        await send_error(bot, chat_id, f"Ошибка при запросе к API: {e}")
    except KeyError:
        await send_error(bot, chat_id, "Неверный формат ответа от API")

# Функция для запуска задачи
def job():
    loop.run_until_complete(get_last_order_price("AQUAXP-USDT", telegram_bot, chat_id))

# Пример использования
if __name__ == "__main__":
    # Ваш токен и ID чата
    bot_token = "token"  # Замените на ваш токен
    chat_id = "id"  # Замените на ваш ID чата

    # Создаем экземпляр бота
    telegram_bot = Bot(token=bot_token)

    # Запланировать выполнение задачи каждые 30 секунд
    schedule.every(30).seconds.do(job)

    # Запускаем основной цикл
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)  # Задержка, чтобы избежать избыточного использования CPU
    except KeyboardInterrupt:
        print("Остановка скрипта.")
