from telebot import TeleBot, types

from logger import Logger
import os, json

class MyError(Exception): pass
class AdminNotConfigured(MyError): pass

GOODS = [
        {
            "name": "Создание несложного Telegram бота на заказ",
            "price": None,
            "params": "название, описание и задачи бота, подробное разъяснение с текстами и картинками (если должны быть в боте)"
        },
        {
            "name": "Печать любой модели на 3D принтере (чёрный пластик)",
            "price": None,
            "params": "внешний вид модели, детали. Если хотите напечатать готовую модель, так и напишите. Также укажите ваш адрес с точностью до квартиры включительно."
        }
    ]
    
user_promos = {}
users_settings = {}
tmp = {"reqwests": {}}
admin_filename = "admin.id"
logger = Logger("server")

ButtGroup = types.InlineKeyboardMarkup
Button = types.InlineKeyboardButton

with open("params.json") as file:
    bot = TeleBot(json.load(file)["token"])
    
def print_message(message: types.Message, text, butt_group=ButtGroup()):
    bot.send_message(message.chat.id if not isinstance(message, int) else message, text, parse_mode="HTML",
reply_markup=butt_group)
    logger.log("info", f"Отправленно сообщение пользователю {f"с username {message.from_user.username}" if isinstance(message, types.Message) else f"с id {message}"}и со следующим текстом: /n{text}")
    
@bot.message_handler(commands=["setAdmin"])
def setup_admin1(message):
    print_message(message, "Введите пароль")
    bot.register_next_step_handler(message, setup_admin2)

def setup_admin2(message):
    true_admin_pass = False
    with open("params.json") as file:
        if message.text == json.load(file)["adminPass"]:
            true_admin_pass = True
            
    if true_admin_pass:
        try:
            with open(admin_filename, "x") as file:
                file.write(str(message.chat.id))
            
            logger.log("info", "Админ установлен.")
            print_message(message, "Успех!")
        except FileExistsError:
            logger.log("warning", f"Попытка повторной установки админа с username {message.from_user.username}!")
            print_message(message, "Админ уже выбран!")
    else:
        logger.log("user_error", "Введён неверный пароль для установки админисратора со стороны {message.from_user.username}!")
        print_message(message, "Неверный пароль!")

@bot.message_handler(commands=["start"])
def start(message):
    if not isinstance(message, types.Message): 
        message = message.message
    
    butts_group = ButtGroup(row_width = 1)
    butts_group.add(Button("Заказать", callback_data = "purch"))
    butts_group.add(Button("Аккаунт (в разработке)", callback_data="acc"))
    butts_group.add(Button("У меня есть промокод", callback_data = "promo"))
    butts_group.add(Button("Помощь", callback_data="help"))
    
    print_message(message, "<b>Добро пожалаловать в BurrbyBot! </b> \nЗдесь вы сможете заказать услуги Burrbedy по самым низким ценам, сохраняя удовотворительное качество услуг!", butt_group=butts_group)
    
@bot.callback_query_handler(lambda call: call.data == "purch")
def purch(call):
    butts_group = ButtGroup(row_width=1)
    
    for index, item in enumerate(GOODS):
        butts_group.add(Button(f"{item["name"]}", 
        callback_data=str(index)))
        
        
        @bot.callback_query_handler(
        eval(f"""lambda call: call.data.isnumeric() and GOODS[int(call.data)]["name"] == "{item["name"]}" """, globals=globals(), locals=locals())
        )
        def callButtonReturn(call):
            users_settings[call.message.chat.id] = {}
            users_settings[call.message.chat.id]["id"] = int(call.data)
            id = users_settings[call.message.chat.id]["id"]
            users_settings[call.message.chat.id]["price"] = GOODS[id]["price"]
            item = GOODS[id]
            if item["params"]:
                print_message(call.message, f"Вы выбрали {item["name"].lower()}  по цене {item["price"] if item["price"] != None else ", которая зависит от того, что вы сейчас введёте"}. Пожалуйста, введите {item["params"]}")
                bot.register_next_step_handler(call.message, getParams)
                
        def getParams(message):
            params = message.text
            users_settings[message.chat.id]["params"] = params
            print_message(message, "Спасибо. Осталось только написать желаемое количество товара (то, что вы ввели на предыдующем шаге, продублируется во все копии вашего заказа)")
            bot.register_next_step_handler(message, getCount)
            
        def getCount(message):
            try:
                count = int(message.text)
                users_settings[message.chat.id]["count"] = count
                user_good_id = users_settings[message.chat.id]["id"]
            except ValueError:
                print_message(message, "Это не число! Введите ТОЛЬКО количество!")
                bot.register_next_step_handler(message, getCount)
                return
            
            butts_group = ButtGroup()
            try: user_promos[message.chat.id] 
            except: pass
            else: butts_group.add(Button("Применить промокод", callback_data="apply_promo"))
            butts_group.add(Button(f"Потвердить", callback_data= "ok"))
            
            @bot.callback_query_handler(lambda call: call.data == "apply_promo")
            def apply_promo(call):
                try:
                    users_settings[call.message.chat.id]["price"] /= user_promos[call.message.chat.id]["/"]
                except: users_settings[message.chat.id]["params"] += f". Бот промо: / на {user_promos[call.message.chat.id]["/"]}"
                
                print_message("Промокод применён!")
                getCount(call.message)
                
            
            @bot.callback_query_handler(lambda call: call.data == "ok")
            def post(call):
                try:
                	post_purch(call.message)
                except AdminNotConfigured: return
                
                counter = 0
                while os.path.exists(f"purch_{counter}.log"):
                    counter += 1
                counter -= 1 # Т. к. на этот момент заказ будет уже сохранён!
                print_message(call.message, f"<b>Успех! </b>Ожидайте сообщения о вашем новом заказе <b>№{counter}</b>")
            if len(users_settings[call.message.chat.id]["params"].split(" Бот промо: / на ")) == 2:
                visual_params = users_settings[call.message.chat.id]["params"].split(" Бот промо: / на ")[0]
            else: visual_params = users_settings[call.message.chat.id]["params"]
            
            print_message(message, f"Снова спасибо. Вот <b>итоговые данные вашего заказа: \nНазвание товара: </b>{GOODS[user_good_id]["name"]} \n<b>Цена товара:</b> {GOODS[user_good_id]["price"] if GOODS[user_good_id]["price"] != None else "зависит от заказа"} \n<b>Пожелания и параметры: </b> {visual_params} \n<b>Количество: {users_settings[message.chat.id]["count"]} </b> \n<b>Итоговая стоимость: </b> {users_settings[message.chat.id]["price"] * users_settings[message.chat.id]["count"] if GOODS[user_good_id]["price"] != None else "зависит от заказа"}", butt_group=butts_group)
    
    butts_group.add(Button("Назад",  callback_data="retStart"))
    @bot.callback_query_handler(lambda call: call.data == "retStart")
    def returnButton(call):
        start(call.message)
    
    print_message(call.message, "Вот доступный ассортимент:", butt_group=butts_group)
    
def post_purch(message):
    name, price = GOODS[users_settings[message.chat.id]["id"]]["name"], users_settings[message.chat.id]["price"]
    try:
        with open(admin_filename) as file:
            admin = int(file.read())
            counter = 0
            while os.path.exists(f"purch_{counter}.log"):
                counter += 1
            with open(f"purch_{counter}.log", "w") as file:
                file.write(str(message.chat.id))
            
            @bot.callback_query_handler(lambda call: call.data == "reqwest")
            def reqwest(call):
                bot.reply_to(call.message, "Пожалуйста, введите текст ответа")
                bot.register_next_step_handler(call.message, getReqwest)
                
            def getReqwest(admin):
                print_message(message, admin.text)
                print_message(admin, "Успех!")
            
            butt_group = ButtGroup(row_width=1)
            butt_group.add(Button("Ответить на заказ", callback_data="reqwest"))
            count = users_settings[message.chat.id]["count"]
            price = users_settings[message.chat.id]["price"]
            admin_message_text = f"""<b>Новый заказ! </b>

<b>Номер заказа:</b> {counter};
<b>Что заказали: </b>{name};
<b>Цена этого: </b>{price if price != None else "зависит от заказа"};
<b>Параметры: </b>{users_settings[message.chat.id]["params"]};
<b>Количество:</b> {count};
<b>Итоговая стоимость: </b>{price * count if price != None else "зависит от заказа"}"""
            logger.log("info", admin_message_text)
            print_message(admin, 
												admin_message_text,
												butt_group=butt_group)
    except FileNotFoundError:
        print_message(message, "Кажется, бот ещё не настроен. Напишите в сообщения каналу @Burrbedy, что бы узнать причину проблемы и способы её решения.")
        raise AdminNotConfigured
        
@bot.message_handler(commands=["request"])
def any_request(message):
    def get_any_request_number(message):
        try: int(message.text)
        except:
        	print_message(message, "Это не номер заказа! Введите другой.")
        	bot.register_next_step_handler(message, get_any_request_number)
        	return
        if os.path.exists(admin_filename):
        	with open(admin_filename) as file:
        	   admin = int(file.read())
        	   if message.chat.id != admin:
        	       print_message(message, "Вы не админ, что бы отвечать на заказы!")
        	       return
        if os.path.exists(f"purch_{int(message.text)}.log"):
            print_message(message, "Введите текст ответа, пожалуйста")
            tmp["reqwests"][message.chat.id] = int(message.text)
            bot.register_next_step_handler(message, get_any_request_message)
        else: 
            print_message(message, "Такого заказа не существует. Введите номер другого")
            bot.register_next_step_handler(message, get_any_request_number)
    
    def get_any_request_message(message):
        with open(f"purch_{tmp["reqwests"][message.chat.id]}.log", "rb") as file:
            user = int(file.read())
            print_message(user, message.text)
            print_message(message, "Успешно отправлено.")
            del tmp["reqwests"][message.chat.id]
    
    try:
        with open(admin_filename) as file:
            admin = int(file.read())
        if message.chat.id == admin:
            print_message(message, "Пожалуйста, введите номер заказа, на который хотите ответить")
            bot.register_next_step_handler(message, get_any_request_number)
    except FileNotFoundError:
        print_message("Бот ещё не настроен. За подробной информацией обращайтесь в сообщения каналу @Burrbedy")
        
        

@bot.callback_query_handler(lambda call: call.data == "promo")
def promocode(call):
    print_message(call.message, "Пожалуйста, введите ваш промокод")
    bot.register_next_step_handler(call.message, get_promocode)  
    
def get_promocode(message):
    global user_promos
    
    if message.text == "/start":
        start(message)

    try:
        with open("promocodes.json", "r") as file:
            parse_file = json.load(file)
            for i in parse_file:
                if message.text.strip() == i:
                    user_promos[message.chat.id] = {"limit": parse_file[message.text.strip()]["limit"], "/": parse_file[message.text.strip()]["/"]}
                    break
                    
            try: user_promos[message.chat.id]
            except KeyError: print_message(message, "Такого промокода не существует. Проверьте правильность написания и актуальность и введите другой промокод или  /start для появления главного меню. Мы всегда пишем в @Burrbedy о появлении новых и завершениях действия старых промокодов!")
            else: 
                    if parse_file[user_promos[message.chat.id]]["limit"] > 0:
                        user_promos[message.chat.id]["/"] = parse_file[user_promos[message.chat.id]["/"]]
                        print_message(message, "Промокод активирован!")
                    elif parse_file[user_promos[message.chat.id]]["limit"] == -1:
                        user_promos[message.chat.id]["/"] = parse_file[user_promos[message.chat.id]["/"]]
                        print_message(message, "Промокод активирован!")
                    else:
                        print_message(message, "Этот промокод уже активирован кем то другим!")
    except: 
        print_message(message, "Пока что нет доступных промокодов!")
        
@bot.callback_query_handler(lambda call: call.data == "help")
def help(call):
    print_message(call.message, "Отправьте сообщение, которое нужно передать админам")
    bot.register_next_step_handler(call.message, get_help_text)
    
def get_help_text(message):
    try:
        with open(admin_filename) as file:
            admin = int(file.read())
        butt_group = ButtGroup(row_width=1)
        butt_group.add(Button("Ответить", callback_data=str({"type": "helpReqwest", "message": message})))
        print_message(admin, f"Новый запрос о помощи! \nСообщение: {message.text}", butt_group=butt_group)
    except: print_message(message, "Бот ещё не настроен. За подробной информацией обращайтесь в сообщения каналу @Burrbedy")
    
@bot.callback_query_handler(lambda call: call.data.startswith("{") and eval(call.data)["type"] == "helpReqwest")
def get_help_reqwest1(call):
    print_message(call.message, "Введите текст ответа")
    call.message.myItem = call.data
    bot.register_next_step_handler(call.message, get_help_reqwest2)
    
def get_help_reqwest2(admin_message):
    print_message(admin_message.myItem["message"], admin_message.text)
    print_message(admin_message, "Успех!")
        
print("Go!")        
bot.polling(none_stop=True)
print("Stop!")