import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

bot = telebot.TeleBot('8469760366:AAEFlqoAI1YZXkb3cO7v94xZ6rTV5e5fFTc')


def open_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🟦 Open"))
    return markup


def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💸 Калькулятор заказа", callback_data='order_calculator'),
        types.InlineKeyboardButton("❓ Частые вопросы", callback_data='answer'),
        types.InlineKeyboardButton("🛎 Отзывы", url='https://t.me/feedbackoppa'),
        types.InlineKeyboardButton("👨‍💻 Связаться с менеджером", callback_data='manager'),
        types.InlineKeyboardButton("📦 Отправить посылку", callback_data='cargo')
    )
    return markup


# Меню частых вопросов
def faq_menu():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('Как сделать заказ?', callback_data='order'))
    markup.row(types.InlineKeyboardButton('Что можете доставить?', callback_data='delivery'))
    markup.row(types.InlineKeyboardButton('Какой срок доставки?', callback_data='time'))
    markup.row(types.InlineKeyboardButton('Сколько стоит доставка?', callback_data='Howm'))
    markup.row(types.InlineKeyboardButton('Какой курс валют?', callback_data='curren'))
    markup.row(types.InlineKeyboardButton('Какую комиссию берете?', callback_data='commission'))
    markup.row(types.InlineKeyboardButton('Что если менеджер долго не отвечает?', callback_data='long'))
    markup.row(types.InlineKeyboardButton('Не нашел свой ответ', callback_data='forget'))
    markup.row(types.InlineKeyboardButton('🔙 Назад', callback_data='back_main'))
    return markup


# Кнопка назад в главное меню
def back_button():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('🔙 Назад в меню', callback_data='back_main'))
    return markup


# Кнопка назад в вопросы
def back_to_faq():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('🔙 Назад к вопросам', callback_data='back_faq'))
    return markup


# Состояния для калькулятора и посылок
user_states = {}

# Веса по категориям
category_weights = {
    'shoes': 1.5,
    'hoodie': 1.0,
    'tishka': 0.5,
    'socks': 0.2
}

# Названия категорий
category_names = {
    'shoes': 'Обувь/Верхняя одежда',
    'hoodie': 'Толстовки/Штаны',
    'tishka': 'Футболки/Шорты',
    'socks': 'Носки/Нижнее белье'
}

# Глобальные переменные для курсов валют
currency_rates = {
    'USD': {'name': 'Американский доллар', 'rate': 95.0, 'cbr_code': 'USD'},
    'CNY': {'name': 'Китайский юань', 'rate': 13.0, 'cbr_code': 'CNY'},
    'KRW': {'name': 'Корейская вона', 'rate': 0.07, 'cbr_code': 'KRW'}
}

last_update_time = ""


# Функция для получения курсов валют с сайта Центробанка
def get_cbr_rates():
    try:
        # URL ежедневных курсов ЦБ
        url = 'https://www.cbr.ru/currency_base/daily/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            print(f"❌ Ошибка доступа к сайту ЦБ: {response.status_code}")
            return None

        # Парсим HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Находим таблицу с курсами валют
        table = soup.find('table', {'class': 'data'})
        if not table:
            print("❌ Не найдена таблица с курсами валют")
            return None

        rates = {}

        # Проходим по всем строкам таблицы (пропускаем заголовок)
        for row in table.find_all('tr')[1:]:
            columns = row.find_all('td')
            if len(columns) >= 5:
                currency_code = columns[1].text.strip()
                unit = int(columns[2].text.strip())  # Номинал
                rate_str = columns[4].text.strip().replace(',', '.')  # Курс

                try:
                    rate = float(rate_str) / unit  # Курс за 1 единицу валюты

                    # Сохраняем курсы для нужных валют
                    if currency_code == 'USD':
                        rates['USD'] = rate
                    elif currency_code == 'CNY':
                        rates['CNY'] = rate
                    elif currency_code == 'KRW':
                        rates['KRW'] = rate

                except ValueError as e:
                    print(f"❌ Ошибка парсинга курса для {currency_code}: {e}")
                    continue

        print(f"✅ Найдены курсы: {rates}")
        return rates

    except Exception as e:
        print(f"❌ Ошибка получения курсов ЦБ: {e}")
        return None


# Функция для обновления курсов валют
def update_currency_rates():
    global currency_rates, last_update_time
    try:
        # Получаем курсы с сайта ЦБ
        cbr_rates = get_cbr_rates()

        if cbr_rates:
            # Обновляем курсы с учетом +5% комиссии
            for currency_code in currency_rates.keys():
                if currency_code in cbr_rates:
                    # Берем курс ЦБ и добавляем 5% комиссии
                    cbr_rate = cbr_rates[currency_code]
                    currency_rates[currency_code]['rate'] = round(cbr_rate * 1.05, 4)
                    print(f"✅ {currency_code}: {cbr_rate} → {currency_rates[currency_code]['rate']} (+5%)")
                else:
                    print(f"⚠️ Курс для {currency_code} не найден на сайте ЦБ")

        # Получаем текущее время по Москве
        moscow_tz = pytz.timezone('Europe/Moscow')
        current_time = datetime.now(moscow_tz).strftime("%d.%m.%Y %H:%M")
        last_update_time = current_time

        print(f"✅ Курсы ЦБ обновлены: {current_time}")
        for currency_code, currency_info in currency_rates.items():
            print(f"{currency_code}: {currency_info['rate']} RUB")

    except Exception as e:
        print(f"❌ Ошибка обновления курсов: {e}")


# Запускаем обновление курсов при старте
update_currency_rates()


@bot.message_handler(commands=['start'])
def start(message):
    name = message.from_user.first_name

    welcome_text = (
        f"✨ Привет, {name}!\n\n"
        "Я — твой личный помощник **OppaBot** 😋\n"
        "Помогу рассчитать стоимость, оформить заказ и быстро связаться с менеджером.\n\n"
        "👇 Выбери, что хочешь сделать:"
    )

    # Отправляем кнопку Open
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=open_keyboard(),
        parse_mode="Markdown"
    )

    # Отправляем главное меню
    bot.send_message(
        message.chat.id,
        "Меню:",
        reply_markup=main_menu()
    )


# Обработчики навигации
@bot.callback_query_handler(func=lambda call: call.data == 'back_main')
def back_to_main(call):
    welcome_text = (
        f"✨ Привет, {call.from_user.first_name}!\n\n"
        "Я — твой личный помощник **OppaBot** 😋\n"
        "Помогу рассчитать стоимость, оформить заказ и быстро связаться с менеджером.\n\n"
        "👇 Выбери, что хочешь сделать:"
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=welcome_text,
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )
#добавляем этой командой кнопку open
@bot.message_handler(func=lambda msg: msg.text == "🟦 Open")
def handle_open(msg):
    bot.send_message(
        msg.chat.id,
        "✨ Главное меню:",
        reply_markup=main_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data == 'back_faq')
def back_to_faq_handler(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='Самые частые вопросы которые могут возникнуть:',
        reply_markup=faq_menu()
    )


# Калькулятор заказа
@bot.callback_query_handler(func=lambda call: call.data == 'order_calculator')
def start_order_calculator(call):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('👟 Обувь/Верхняя одежда', callback_data='calc_shoes'))
    markup.row(types.InlineKeyboardButton('🧥 Толстовки/Штаны', callback_data='calc_hoodie'))
    markup.row(types.InlineKeyboardButton('👕 Футболки/Шорты', callback_data='calc_tishka'))
    markup.row(types.InlineKeyboardButton('🧦 Носки/Нижнее белье', callback_data='calc_socks'))
    markup.row(types.InlineKeyboardButton('🔙 Назад', callback_data='back_main'))

    info_text = f"""
🧮 *Калькулятор заказа*

Выберите категорию товара для расчета стоимости.

*Примерные веса:*
• 👟 Обувь/Верхняя одежда: 1.5 кг
• 🧥 Толстовки/Штаны: 1.0 кг  
• 👕 Футболки/Шорты: 0.5 кг
• 🧦 Носки/Нижнее белье: 0.2 кг

*Курсы ЦБ обновлены:* {last_update_time} МСК
"""

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=info_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


# Обработчики выбора категории для калькулятора
@bot.callback_query_handler(func=lambda call: call.data.startswith('calc_'))
def handle_calc_category(call):
    category = call.data.replace('calc_', '')
    user_states[call.from_user.id] = {'state': 'waiting_currency_selection', 'category': category}

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('🇺🇸 Доллары (USD)', callback_data=f'currency_USD_{category}'))
    markup.row(types.InlineKeyboardButton('🇨🇳 Юани (CNY)', callback_data=f'currency_CNY_{category}'))
    markup.row(types.InlineKeyboardButton('🇰🇷 Воны (KRW)', callback_data=f'currency_KRW_{category}'))
    markup.row(types.InlineKeyboardButton('🔙 Назад к категориям', callback_data='order_calculator'))

    help_text = f"""
💰 *Выберите валюту*

Категория: *{category_names[category]}*
Примерный вес: *{category_weights[category]} кг*

Выберите валюту для расчета:

*Курсы ЦБ обновлены:* {last_update_time} МСК
"""

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=help_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


# Обработчик выбора валюты
@bot.callback_query_handler(func=lambda call: call.data.startswith('currency_'))
def handle_currency_selection(call):
    parts = call.data.split('_')
    currency_code = parts[1]
    category = parts[2]

    user_states[call.from_user.id] = {
        'state': 'waiting_price_input',
        'category': category,
        'currency': currency_code
    }

    currency_info = currency_rates[currency_code]

    help_text = f"""
💰 *Введите стоимость товара*

Категория: *{category_names[category]}*
Валюта: *{currency_info['name']} ({currency_code})*
Курс: *{currency_info['rate']:.2f} руб.* (ЦБ + 5%)

Введите стоимость товара в цифрах:
• Например: `100` или `150000`

*Курс обновлен:* {last_update_time} МСК
"""

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('🔙 Выбрать другую валюту', callback_data=f'calc_{category}'))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=help_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


@bot.message_handler(
    func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_price_input')
def calculate_order(message):
    try:
        user_data = user_states[message.from_user.id]
        category = user_data['category']
        currency_code = user_data['currency']

        # Получаем сумму и проверяем ее
        amount_text = message.text.strip().replace(',', '.').replace(' ', '')
        amount = float(amount_text)

        if amount <= 0:
            bot.send_message(message.chat.id, "❌ Стоимость должна быть больше 0")
            return

        # Получаем данные о валюте
        currency_info = currency_rates[currency_code]
        rate = currency_info['rate']

        # Рассчитываем стоимость в рублях
        product_cost_rub = amount * rate

        # Рассчитываем комиссию
        if product_cost_rub <= 5000:
            commission = 1000
            commission_text = "1 000₽ (заказы до 5 000₽)"
        elif product_cost_rub <= 10000:
            commission = 1500
            commission_text = "1 500₽ (заказы до 10 000₽)"
        else:
            commission = product_cost_rub * 0.10
            commission_text = "10% от стоимости (заказы свыше 10 000₽)"

        # Получаем примерный вес товара
        weight = category_weights[category]

        # Рассчитываем стоимость доставки из Кореи (22 000 вон за кг)
        usd_to_krw = 1300
        krw_rate = rate / usd_to_krw
        delivery_cost_krw = 22000 * weight
        delivery_cost_rub = delivery_cost_krw * krw_rate

        # Итоговая стоимость (товар + комиссия + доставка)
        total_cost = product_cost_rub + commission + delivery_cost_rub

        # Форматируем числа без .0 в конце
        def format_number(num):
            if num == int(num):
                return f"{int(num):,}".replace(',', ' ')
            else:
                # Убираем .0 в конце и форматируем
                formatted = f"{num:,.1f}".replace(',', ' ')
                return formatted.replace('.0', '')

        response = f"""
🧮 *Итоговый расчет*

*Выкуп:* в течение 1-2 дня
*Категория:* {category_names[category]}
*Примерный вес товара:* {weight} кг
*Валюта:* {currency_info['name']}
*Стоимость товара:* {format_number(amount)}
*Курс валюты:* {rate:.2f} руб. (ЦБ + 5%)

*Расчет:*
• Стоимость товара: {format_number(product_cost_rub)} руб.
• Наша комиссия ({commission_text}): {format_number(commission)} руб.
• Доставка из Кореи ({weight} кг): ~{format_number(delivery_cost_rub)} руб.

*Итоговая цена:* {format_number(total_cost)} руб

*Курс ЦБ обновлен:* {last_update_time} МСК

📝 *Точный расчет вам поможет произвести менеджер*
"""

        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton('👨‍💻 Связаться с Manager_1', url='https://t.me/askingnothingleavemebe'))
        markup.row(types.InlineKeyboardButton('👨‍💻 Связаться с Manager_2', url='https://t.me/Arxamyn'))
        markup.row(types.InlineKeyboardButton('🔄 Новый расчет', callback_data='order_calculator'))
        markup.row(types.InlineKeyboardButton('🔙 В главное меню', callback_data='back_main'))

        bot.send_message(
            message.chat.id,
            response,
            parse_mode='Markdown',
            reply_markup=markup
        )

        # Сбрасываем состояние
        user_states[message.from_user.id] = None

    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат. Введите число, например: `100` или `150000`",
                         parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}. Проверьте данные и попробуйте снова.",
                         parse_mode='Markdown')


# Обработчик для отправки посылки
@bot.callback_query_handler(func=lambda call: call.data == 'cargo')
def handle_cargo(call):
    cargo_text = """
🚚 *РАСЧЕТ ДОСТАВКИ ПОСЫЛКИ*

📦 *Выберите тип расчета:*

• Для вещей (одежда, обувь) - расчет за КГ
• Для электроники - расчет за ШТУКУ
• Для крупногабаритных товаров - индивидуальный расчет

💡 *Важно:* 
• Вещи: 22 000 вон за кг
• Электроника: от 90 000 вон за штуку
• Крупногабаритные: рассчитывается отдельно
"""

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('👕 Вещи (расчет за кг)', callback_data='cargo_weight'))
    markup.row(types.InlineKeyboardButton('📱 Электроника (расчет за штуку)', callback_data='cargo_electronics_count'))
    markup.row(types.InlineKeyboardButton('📦 Крупногабаритный товар', callback_data='cargo_large'))
    markup.row(types.InlineKeyboardButton('🔙 Назад', callback_data='back_main'))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=cargo_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


# Обработчик для крупногабаритных товаров
@bot.callback_query_handler(func=lambda call: call.data == 'cargo_large')
def handle_cargo_large(call):
    # Получаем курсы из ЦБ РФ
    usd_rate = currency_rates['USD']['rate']
    usd_to_krw = 1300
    krw_rate = usd_rate / usd_to_krw

    cargo_text = f"""
📦 *КРУПНОГАБАРИТНЫЕ ТОВАРЫ - РАСЧЕТ ОТДЕЛЬНО*

⚠️ *Данный тип товаров рассчитывается индивидуально!*

*Что относится к крупногабаритным:*
• Мебель (стулья, столы, полки, шкафы)
• Крупная бытовая техника (холодильники, стиральные машины)
• Спортивное оборудование (беговые дорожки, тренажеры)
• Большие партии товаров
• Товары нестандартных размеров
• Автозапчасти и детали

💰 *Почему расчет отдельный:*
• Требуется специальная упаковка
• Занимает много места в контейнере
• Может требовать особых условий перевозки
• Часто требует разборки/сборки
• Рассчитывается по объему, а не по весу

💼 *Особенности доставки:*
• Рассчитывается индивидуально для каждого случая
• Может быть расчет за ШТУКУ или за ОБЪЕМ
• Зависит от веса, габаритов и типа товара
• Возможна сборная доставка с другими товарами

*Курсы ЦБ РФ:*
• 1 USD = {usd_rate:.2f} RUB (+5%)
• 1 KRW ≈ {krw_rate:.4f} RUB

📞 *Для расчета стоимости свяжитесь с менеджером и предоставьте:*
• Фото товара
• Размеры (длина × ширина × высота в см)
• Вес (если известен)
• Количество штук
• Подробное описание товара
• Ссылку на товар (если есть)

⏰ *Срок расчета:* 1-2 рабочих дня

💡 *Окончательная стоимость рассчитывается по курсу ЦБ РФ на день оплаты!*

*Курс обновлен:* {last_update_time} МСК
"""

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('👨‍💻 Рассчитать стоимость', url='https://t.me/askingnothingleavemebe'))
    markup.row(types.InlineKeyboardButton('👨‍💻 Консультация', url='https://t.me/Arxamyn'))
    markup.row(types.InlineKeyboardButton('🔄 Новый расчет', callback_data='cargo'))
    markup.row(types.InlineKeyboardButton('🔙 В главное меню', callback_data='back_main'))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=cargo_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


# Обработчик для ввода веса вещей
@bot.callback_query_handler(func=lambda call: call.data == 'cargo_weight')
def handle_cargo_weight_input(call):
    user_states[call.from_user.id] = {'state': 'waiting_cargo_weight_clothes'}

    cargo_text = """
👕 *РАСЧЕТ ДОСТАВКИ ВЕЩЕЙ*

📦 *Введите вес вашей посылки в килограммах:*

Например:
• `1.5` - для посылки 1.5 кг
• `3` - для посылки 3 кг
• `0.8` - для посылки 800 грамм

*Расчет для вещей идет за КИЛОГРАММ*
"""

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('🔙 Назад', callback_data='cargo'))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=cargo_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


# Обработчик для ввода количества электроники
@bot.callback_query_handler(func=lambda call: call.data == 'cargo_electronics_count')
def handle_cargo_electronics_count(call):
    user_states[call.from_user.id] = {'state': 'waiting_electronics_count'}

    cargo_text = """
📱 *РАСЧЕТ ДОСТАВКИ ЭЛЕКТРОНИКИ*

🔢 *Введите количество штук:*

Например:
• `1` - для 1 телефона/наушников
• `2` - для 2 телефонов
• `3` - для 3 единиц техники

*Расчет для электроники идет за ШТУКУ*
"""

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('🔙 Назад', callback_data='cargo'))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=cargo_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


# Обработчик для ввода веса вещей
@bot.message_handler(
    func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_cargo_weight_clothes')
def handle_cargo_weight_clothes(message):
    try:
        weight = float(message.text.strip())
        if weight <= 0:
            bot.send_message(message.chat.id, "❌ Вес должен быть больше 0")
            return

        # Сохраняем вес и переходим к расчету вещей
        user_states[message.from_user.id] = {
            'state': 'waiting_cargo_type',
            'cargo_weight': weight,
            'cargo_type': 'clothes'
        }

        # Показываем расчет вещей сразу
        usd_rate = currency_rates['USD']['rate']
        usd_to_krw = 1300
        krw_rate = usd_rate / usd_to_krw

        clothes_price_krw = 22000
        clothes_price_rub = clothes_price_krw * krw_rate
        total_cost = clothes_price_rub * weight

        cargo_text = f"""
👕 *РАСЧЕТ ДОСТАВКИ ВЕЩЕЙ*

*Вес посылки:* {weight} кг
*Стоимость за кг:* 22 000 вон (~{clothes_price_rub:,.0f} руб.)
*Общая стоимость:* ~{total_cost:,.0f} руб.

💰 *Расчет:* ЗА КИЛОГРАММ
*Пример:* {weight} кг × 22 000 вон = {weight * 22000:,.0f} вон

*Курсы ЦБ РФ:*
• 1 USD = {usd_rate:.2f} RUB (+5%)
• 1 KRW ≈ {krw_rate:.4f} RUB

*Что относится к вещам:*
• Одежда (футболки, джинсы, куртки)
• Обувь (кроссовки, туфли, ботинки)
• Аксессуары (сумки, ремни, очки)
• Косметика и уход
• Книги и канцелярия

📦 *Упаковка:* Стандартная коробка/пакет
⏰ *Срок:* 7-10 дней до Владивостока

💡 *Окончательная стоимость рассчитывается по курсу ЦБ РФ на день оплаты!*

*Курс обновлен:* {last_update_time} МСК
"""

        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton('👨‍💻 Рассчитать точную стоимость', url='https://t.me/askingnothingleavemebe'))
        markup.row(types.InlineKeyboardButton('👨‍💻 Уточнить детали', url='https://t.me/Arxamyn'))
        markup.row(types.InlineKeyboardButton('🔄 Новый расчет', callback_data='cargo'))
        markup.row(types.InlineKeyboardButton('🔙 В главное меню', callback_data='back_main'))

        bot.send_message(
            message.chat.id,
            cargo_text,
            parse_mode='Markdown',
            reply_markup=markup
        )

    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат. Введите число, например: `1.5` или `3`",
                         parse_mode='Markdown')



@bot.message_handler(
    func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_electronics_count')
def handle_electronics_count(message):
    try:
        count = int(message.text.strip())
        if count <= 0:
            bot.send_message(message.chat.id, "❌ Количество должно быть больше 0")
            return

        # Сохраняем количество
        user_states[message.from_user.id] = {
            'state': 'waiting_electronics_type',
            'electronics_count': count
        }

        # Показываем меню выбора типа электроники
        usd_rate = currency_rates['USD']['rate']
        usd_to_krw = 1300
        krw_rate = usd_rate / usd_to_krw

        cargo_text = f"""
📱 *ВЫБЕРИТЕ ТИП ЭЛЕКТРОНИКИ*

Количество штук: *{count} шт*

💰 *Актуальные курсы:*
• 1 USD = {usd_rate:.2f} RUB (ЦБ РФ + 5%)
• 1 KRW ≈ {krw_rate:.4f} RUB
"""

        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton('📱 Мелкая техника', callback_data='cargo_electronics_small'))
        markup.row(types.InlineKeyboardButton('💻 Крупная техника', callback_data='cargo_electronics_large'))
        markup.row(types.InlineKeyboardButton('🔙 Назад', callback_data='cargo'))

        bot.send_message(
            message.chat.id,
            cargo_text,
            parse_mode='Markdown',
            reply_markup=markup
        )

    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат. Введите целое число, например: `1` или `2`",
                         parse_mode='Markdown')


# Обработчик для мелкой техники
@bot.callback_query_handler(func=lambda call: call.data == 'cargo_electronics_small')
def handle_cargo_electronics_small(call):
    user_data = user_states.get(call.from_user.id, {})
    count = user_data.get('electronics_count', 1)  # По умолчанию 1 штука

    # Получаем курсы из ЦБ РФ
    usd_rate = currency_rates['USD']['rate']
    usd_to_krw = 1300
    krw_rate = usd_rate / usd_to_krw

    small_tech_price_krw = 90000  # 90 000 вон за штуку
    small_tech_price_rub = small_tech_price_krw * krw_rate
    total_cost = small_tech_price_rub * count

    cargo_text = f"""
📱 *ДОСТАВКА МЕЛКОЙ ТЕХНИКИ*

*Количество:* {count} шт
*Стоимость за шт:* 90 000 вон (~{small_tech_price_rub:,.0f} руб.)
*Общая стоимость:* ~{total_cost:,.0f} руб.

💰 *Расчет:* ЗА ШТУКУ
*Пример:* {count} шт × 90 000 вон = {count * 90000:,} вон

*Курсы ЦБ РФ:*
• 1 USD = {usd_rate:.2f} RUB (+5%)
• 1 KRW ≈ {krw_rate:.4f} RUB

*Мелкая техника (90 000 вон/ШТУКА):*
• Телефоны и смартфоны
• Наушники и гарнитуры
• Умные часы и фитнес-браслеты
• Планшеты
• Фотоаппараты
• Powerbank
• Кабели и зарядные устройства

⚠️ *Важно:* 
• Для электроники расчет идет ЗА ШТУКУ
• Цена фиксированная за каждую единицу товара
• Окончательная стоимость - по курсу ЦБ РФ на день оплаты

*Курс обновлен:* {last_update_time} МСК
"""

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('👨‍💻 Рассчитать точную стоимость', url='https://t.me/askingnothingleavemebe'))
    markup.row(types.InlineKeyboardButton('👨‍💻 Уточнить детали', url='https://t.me/Arxamyn'))
    markup.row(types.InlineKeyboardButton('🔄 Новый расчет', callback_data='cargo'))
    markup.row(types.InlineKeyboardButton('🔙 В главное меню', callback_data='back_main'))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=cargo_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


# Обработчик для крупной техники
@bot.callback_query_handler(func=lambda call: call.data == 'cargo_electronics_large')
def handle_cargo_electronics_large(call):
    user_data = user_states.get(call.from_user.id, {})
    count = user_data.get('electronics_count', 1)  # По умолчанию 1 штука

    # Получаем курсы из ЦБ РФ
    usd_rate = currency_rates['USD']['rate']
    usd_to_krw = 1300
    krw_rate = usd_rate / usd_to_krw

    large_tech_price_krw = 135000  # 135 000 вон за штуку
    large_tech_price_rub = large_tech_price_krw * krw_rate
    total_cost = large_tech_price_rub * count

    cargo_text = f"""
💻 *ДОСТАВКА КРУПНОЙ ТЕХНИКИ*

*Количество:* {count} шт
*Стоимость за шт:* 135 000 вон (~{large_tech_price_rub:,.0f} руб.)
*Общая стоимость:* ~{total_cost:,.0f} руб.

💰 *Расчет:* ЗА ШТУКУ
*Пример:* {count} шт × 135 000 вон = {count * 135000:,} вон

*Курсы ЦБ РФ:*
• 1 USD = {usd_rate:.2f} RUB (+5%)
• 1 KRW ≈ {krw_rate:.4f} RUB

*Крупная техника (135 000 вон/ШТУКА):*
• Ноутбуки и ультрабуки
• Игровые приставки (PlayStation, Xbox)
• Техника Dyson (фены, пылесосы)
• Мониторы
• Колонки и аудиосистемы
• Принтеры и МФУ
• Игровые клавиатуры и мыши

⚠️ *Важно:* 
• Для электроники расчет идет ЗА ШТУКУ
• Цена фиксированная за каждую единицу товара
• Окончательная стоимость - по курсу ЦБ РФ на день оплаты

*Курс обновлен:* {last_update_time} МСК
"""

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('👨‍💻 Рассчитать точную стоимость', url='https://t.me/askingnothingleavemebe'))
    markup.row(types.InlineKeyboardButton('👨‍💻 Уточнить детали', url='https://t.me/Arxamyn'))
    markup.row(types.InlineKeyboardButton('🔄 Новый расчет', callback_data='cargo'))
    markup.row(types.InlineKeyboardButton('🔙 В главное меню', callback_data='back_main'))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=cargo_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == 'cargo_electronics')
def handle_cargo_electronics(call):
    user_data = user_states.get(call.from_user.id, {})

    # Получаем курсы из ЦБ РФ
    usd_rate = currency_rates['USD']['rate']
    usd_to_krw = 1300
    krw_rate = usd_rate / usd_to_krw

    small_tech_price_krw = 90000
    large_tech_price_krw = 135000
    small_tech_price_rub = small_tech_price_krw * krw_rate
    large_tech_price_rub = large_tech_price_krw * krw_rate

    cargo_text = f"""
📱 *ДОСТАВКА ЭЛЕКТРОНИКИ*

💰 *Стоимость доставки:*

*Мелкая техника:* 90 000 вон/ШТУКА
*В рублях:* ~{small_tech_price_rub:,.0f} руб./шт

*Крупная техника:* 135 000 вон/ШТУКА  
*В рублях:* ~{large_tech_price_rub:,.0f} руб./шт

*Курсы ЦБ РФ:*
• 1 USD = {usd_rate:.2f} RUB (+5%)
• 1 KRW ≈ {krw_rate:.4f} RUB

*Мелкая техника (90 000 вон/ШТУКА):*
• Телефоны и смартфоны
• Наушники и гарнитуры
• Умные часы и фитнес-браслеты
• Планшеты
• Фотоаппараты

*Крупная техника (135 000 вон/ШТУКА):*
• Ноутбуки и ультрабуки
• Игровые приставки (PlayStation, Xbox)
• Техника Dyson (фены, пылесосы)
• Мониторы
• Колонки и аудиосистемы

⚠️ *Важно:* 
• Для электроники расчет идет ЗА ШТУКУ
• Цена фиксированная за каждую единицу товара
• Не зависит от веса или размеров (кроме очень больших товаров)
• Окончательная стоимость - по курсу ЦБ РФ на день оплаты

*Курс обновлен:* {last_update_time} МСК
"""

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('👨‍💻 Рассчитать мелкую технику', url='https://t.me/askingnothingleavemebe'))
    markup.row(types.InlineKeyboardButton('👨‍💻 Рассчитать крупную технику', url='https://t.me/Arxamyn'))
    markup.row(types.InlineKeyboardButton('🔄 Новый расчет', callback_data='cargo'))
    markup.row(types.InlineKeyboardButton('🔙 В главное меню', callback_data='back_main'))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=cargo_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == 'cargo_large')
def handle_cargo_large(call):
    user_data = user_states.get(call.from_user.id, {})
    weight = user_data.get('cargo_weight', 1)  # По умолчанию 1 кг если вес не указан

    # Получаем курсы из ЦБ РФ
    usd_rate = currency_rates['USD']['rate']
    usd_to_krw = 1300
    krw_rate = usd_rate / usd_to_krw

    cargo_text = f"""
📦 *КРУПНОГАБАРИТНЫЕ ПОСЫЛКИ*

*Вес посылки:* {weight} кг

*Что относится к крупногабаритным:*
• Мебель (стулья, столы, полки)
• Крупная бытовая техника
• Спортивное оборудование
• Большие партии товаров
• Товары нестандартных размеров

💼 *Особенности доставки:*
• Рассчитывается индивидуально
• Может быть расчет за ШТУКУ или за ОБЪЕМ
• Зависит от веса и габаритов
• Требуется специальная упаковка
• Возможна сборная доставка

💰 *Курсы ЦБ РФ:*
• 1 USD = {usd_rate:.2f} RUB (+5%)
• 1 KRW ≈ {krw_rate:.4f} RUB

📞 *Для расчета стоимости свяжитесь с менеджером и предоставьте:*
• Фото товара
• Размеры (длина × ширина × высота)
• Вес ({weight} кг)
• Количество штук
• Описание товара

⏰ *Срок расчета:* 1-2 рабочих дня

💡 *Окончательная стоимость рассчитывается по курсу ЦБ РФ на день оплаты!*

*Курс обновлен:* {last_update_time} МСК
"""

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('👨‍💻 Рассчитать крупный товар', url='https://t.me/askingnothingleavemebe'))
    markup.row(types.InlineKeyboardButton('👨‍💻 Консультация по габаритам', url='https://t.me/Arxamyn'))
    markup.row(types.InlineKeyboardButton('🔄 Новый расчет', callback_data='cargo'))
    markup.row(types.InlineKeyboardButton('🔙 В главное меню', callback_data='back_main'))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=cargo_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


# Команда для принудительного обновления курсов
@bot.message_handler(commands=['update_rates'])
def update_rates_command(message):
    update_currency_rates()
    bot.send_message(message.chat.id, f"✅ Курсы ЦБ обновлены!\n{last_update_time} МСК")


@bot.callback_query_handler(func=lambda call: call.data == 'calculate_price')
def handle_calculate(call):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('Обувь/Верхняя одежда', callback_data='shoes'))
    markup.row(types.InlineKeyboardButton('Толстовки/Штаны', callback_data='hoodie'))
    markup.row(types.InlineKeyboardButton('Футболки/Шорты', callback_data='tishka'))
    markup.row(types.InlineKeyboardButton('Носки/Нижнее белье', callback_data='socks'))
    markup.row(types.InlineKeyboardButton('🔙 Назад', callback_data='back_main'))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Выберите категорию товара:",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == 'manager')
def handle_manager(call):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('Manager_1', url='https://t.me/askingnothingleavemebe'))
    markup.row(types.InlineKeyboardButton('Manager_2', url='https://t.me/Arxamyn'))
    markup.row(types.InlineKeyboardButton('🔙 Назад', callback_data='back_main'))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='Можете связаться с любым менеджером для оформления заказа',
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == 'answer')
def handle_answer(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='Самые частые вопросы которые могут возникнуть:',
        reply_markup=faq_menu()
    )


# Обработчики вопросов
@bot.callback_query_handler(func=lambda call: call.data == 'order')
def handle_order(call):
    order_text = """*Оформить заказ через OppaStore очень просто*

Давайте разберемся как это сделать:

📍 *ШАГ 1*
Находите товар на сайте, копируете ссылку, указываете размер и отправляете менеджеру

📍 *ШАГ 2* 
Менеджер рассчитывает заказ с доставкой до РФ и сообщает итоговую сумму

📍 *ШАГ 3*
Вы оплачиваете заказ и после оплаты ваш заказ будет выкуплен

📍 *ШАГ 4*
Ваш заказ оформлен! ✅"""

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=order_text,
        parse_mode='Markdown',
        reply_markup=back_to_faq()
    )


@bot.callback_query_handler(func=lambda call: call.data == 'delivery')
def handle_delivery(call):
    order_text = """✅ *Что доставляем:*
• Всё, что не запрещено для ввоза в РФ
• Товары из санкционных списков США и ЕС
• Любые бренды и категории
• Можем доставить ваш товар оптом (карго доставка тоже есть)"""

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=order_text,
        parse_mode='Markdown',
        reply_markup=back_to_faq()
    )


@bot.callback_query_handler(func=lambda call: call.data == 'time')
def handle_time(call):
    delivery_text = """🚢 *Сроки доставки из разных стран:*

🇰🇷 *ИЗ КОРЕИ*
• 7-10 дней
• Судно ходит каждую субботу
• Приходит в понедельник во Владивосток

🇨🇳 *ИЗ КИТАЯ*
• До Москвы: 20-25 дней
• До Владивостока: 14-20 дней
• *При условии отсутствия задержек на таможне*

🇺🇸 *ИЗ США*
• На данный момент нет возможности осуществлять доставку напрямую
• *Скоро наладим поставки!*
• Можем доставлять ваши заказы через Корея 🛳️"""

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=delivery_text,
        parse_mode='Markdown',
        reply_markup=back_to_faq()
    )


@bot.callback_query_handler(func=lambda call: call.data == 'Howm')
def handle_howm(call):
    delivery_text = """🚢 *Стоимость и сроки доставки:*

🇰🇷 *ИЗ КОРЕИ*
• Одежда/обычные товары: 20 000 вон за кг (~15$)
• Техника/электроника: 90 000 вон за кг (~62$)
• 7-10 дней
• Судно ходит каждую субботу
• Приходит в понедельник во Владивосток

🇨🇳 *ИЗ КИТАЯ*
• 9$ за кг
• 20-25 дней
• *При условии отсутствия задержек на таможне*

🇺🇸 *ИЗ США*
• 20 000 вон + 10-15$ за кг (~25-30$ итого)
• *Скоро наладим прямые поставки!*
• Доставляем через Корею: США → Корея → РФ
• *Оплата за 2 этапа доставки*"""

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=delivery_text,
        parse_mode='Markdown',
        reply_markup=back_to_faq()
    )


@bot.callback_query_handler(func=lambda call: call.data == 'curren')
def handle_currency_question(call):
    currency_text = f"""💱 *Актуальные курсы валют:*

🇺🇸 *USD (доллар):* {currency_rates['USD']['rate']:.2f} руб.
🇨🇳 *CNY (юань):* {currency_rates['CNY']['rate']:.2f} руб.
🇰🇷 *KRW (вона):* {currency_rates['KRW']['rate']:.4f} руб.

⚡ *Курс Центробанка + 5%*

*Обновлено:* {last_update_time} МСК
"""

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('💸 Рассчитать стоимость', callback_data='order_calculator'))
    markup.row(types.InlineKeyboardButton('🔙 Назад к вопросам', callback_data='back_faq'))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=currency_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == 'commission')
def handle_commission(call):
    commission_text = """💼 *Наша комиссия за услуги:*

• 1 000₽ - для заказов до 5 000₽
• 1 500₽ - для заказов до 10 000₽  
• 10% от стоимости - для заказов свыше 15 000₽"""

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('💸 Рассчитать стоимость', callback_data='order_calculator'))
    markup.row(types.InlineKeyboardButton('🔙 Назад к вопросам', callback_data='back_faq'))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=commission_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == 'long')
def handle_long(call):
    long_text = """⏰ *Что если менеджер долго не отвечает?*

💤 *Наши менеджеры иногда спят, но они всегда стараются ответить как можно раньше.*

🌍 *Для быстрого ответа:*
• Если вы живете по московскому времени - пишите *Manager_1*
• Если по приморскому времени - пишите *Manager_2*

📞 *Так вы сможете получить ответ как можно раньше!*"""

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('👨‍💻 Связаться с Manager_1', url='https://t.me/askingnothingleavemebe'))
    markup.row(types.InlineKeyboardButton('👨‍💻 Связаться с Manager_2', url='https://t.me/Arxamyn'))
    markup.row(types.InlineKeyboardButton('🔙 Назад к вопросам', callback_data='back_faq'))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=long_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == 'forget')
def handle_forget(call):
    other_text = """🤔 *Не нашли ответ на свой вопрос?*

📞 *Свяжитесь с любым менеджером - мы обязательно поможем!*

💬 *Опишите вашу ситуацию подробнее и мы найдем решение*"""

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('👨‍💻 Связаться с Manager_1', url='https://t.me/askingnothingleavemebe'))
    markup.row(types.InlineKeyboardButton('👨‍💻 Связаться с Manager_2', url='https://t.me/Arxamyn'))
    markup.row(types.InlineKeyboardButton('🔙 Назад к вопросам', callback_data='back_faq'))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=other_text,
        parse_mode='Markdown',
        reply_markup=markup
    )


print("🤖 Бот запущен!")
print("💱 Курсы ЦБ обновлены при старте")

bot.polling(none_stop=True)
