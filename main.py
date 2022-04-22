# author: nathan ranchin

import openai
from time import time
from telegram import Bot
from json import load, dump
from requests import get, post, delete, put
from telethon import TelegramClient, events
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters


fix_tp = 4
fix_sl = 3
positions = []
lot_size = 0.02
login = "YOUR_LOGIN_HERE"
reality = "LIVE"
password = "YOUR_PASSWORD_TO_DELETE_CHANNELS_HERE"
free_margin = None
api_id = "YOUR_API_ID_HERE"
user_id = "YOUR_USER_ID_HERE"
api_hash = "YOUR_API_HASH_HERE"
endpoint = "https://rest.simplefx.com/api/v3"
client = TelegramClient("forex", api_id, api_hash)
bot_token = "YOUR_BOT_TOKEN_HERE"
openai.api_key = "YOUR_OPENAI_API_KEY_HERE"
token = "YOUR_TOKEN_HERE"

with open("channels.json", "r") as cj:
    channels_json = load(cj)

SIZE, CLOSE, DELETE, PASSWORD, CHANNEL, TP, SL, CHANNEL_TEST, SYMBOL = range(9)

def refresh_free_margin():
    global free_margin
    btc_price = get("https://api.binance.com/api/v3/avgPrice?symbol=BTCUSDT").json()["price"]
    for i in get(f"{endpoint}/accounts", headers={"Authorization": token}).json()["data"]:
        if i["reality"] == reality:
            free_margin = ((i["balance"] + i["bonus"])/10**6)*float(btc_price)

def start(update, context):
    update.message.reply_text("Je me réveille tranquillement")
    global positions
    positions_all = post(f"{endpoint}/trading/orders/active", json={"login": login, "reality": reality}, headers={"Authorization": token}).json()["data"]["marketOrders"]
    positions.clear()
    for i in positions_all:
        positions.extend([i])
    refresh_free_margin()
    update.message.reply_text("Salut ma couille 🍒")


def stop(update, context):
    update.message.reply_text("J'ai tout arrêté")


def start_close(update, context):
    if len(positions) > 0:
        update.message.reply_text("Les positons ouvertes sont: \n")
        positions_all = post(f"{endpoint}/trading/orders/active", json={"login": login, "reality": reality}, headers={"Authorization": token}).json()["data"]["marketOrders"]
        for i in range(len(positions_all)):
            update.message.reply_text(f"number: {i}\nopenPrice: {positions_all[i]['openPrice']}\nprofit: {positions_all[i]['profit']}\nsymbol: {positions_all[i]['symbol']}\nside: {positions_all[i]['side']}\nvolume: {positions_all[i]['volume']}")
        update.message.reply_text("Laquelle que veux-tu fermer ?")
    else:
        update.message.reply_text("Il n'y a pas de positions ouvertes")
    return CLOSE


def close(update, context):
    positon_number = int(update.message.text)
    obj = {
        "Id": positions[positon_number]["id"],
        "Volume": positions[positon_number]["volume"],
        "RequestId": "string",
        "Login": login,
        "Reality": reality
    }
    if delete(f"{endpoint}/trading/orders/market", json=obj , headers={"Authorization": token}).status_code != 200:
        update.message.reply_text("La position n'a pas été fermée, il y a eu un problème")
        close(update, context)
    positions.pop(positon_number)
    refresh_free_margin()
    update.message.reply_text(f"La position {positon_number} a été fermée")
    return ConversationHandler.END


def close_all(update, context):
    if len(positions) > 0:
        for i in range(len(positions)):
            obj = {
                "Symbol": positions[i]["symbol"],
                "Id": positions[i]["id"],
                "RequestId": "string",
                "Login": login,
                "Reality": reality
            }
            if delete(f"{endpoint}/trading/orders/market/bysymbol", json=obj, headers={"Authorization": token}).status_code != 200:
                update.message.reply_text(f"Les positions de {positions[i]['symbol']} n'ont pas été fermées, il y a eu un problème")
                close_all(update, context)
            update.message.reply_text(f"Les positions de {positions[i]['symbol']} ont été fermées")
        positions.clear()
        refresh_free_margin()
        update.message.reply_text("Toutes les positions ont été fermées")
    else:
        update.message.reply_text("Il n'y a pas de positions ouvertes")


def balance(update, context):
    global free_margin
    btc_price = get("https://api.binance.com/api/v3/avgPrice?symbol=BTCUSDT").json()["price"]
    for i in get(f"{endpoint}/accounts", headers={"Authorization": token}).json()["data"]:
        if i["reality"] == reality:
            balance = (i["balance"] + i["bonus"])/10**6
    free_margin = balance*float(btc_price)
    update.message.reply_text(f"Balance: {round(balance, 4)} BTC\nValeur: {round(balance*float(btc_price), 2)} USD")


def get_positions(update, context):
    positions = post(f"{endpoint}/trading/orders/active", json={"login": login, "reality": reality}, headers={"Authorization": token}).json()["data"]["marketOrders"]
    if len(positions) == 0:
        update.message.reply_text("Il n'y a pas de positions")
    else:
        btc_price = get("https://api.binance.com/api/v3/avgPrice?symbol=BTCUSDT").json()["price"]
        for i in positions:
            profit = round((float(i["profit"])*10**-6)*float(btc_price), 2)
            update.message.reply_text(f"reality: {i['reality']}\nopenPrice: {i['openPrice']}\nprofit: {profit} USD\nsymbol: {i['symbol']}\nside: {i['side']}\nvolume: {i['volume']}")
    refresh_free_margin()


def help(update, context):
    update.message.reply_text(
        """/stop - j'arrête bg
/help - tu vois ca bg
/start - tu me réveilles bg
/infos - j'envoie toutes les infos
/positions - get the current position
/get_channels - tu veux voir les channels
/change_type - changer le type de reality
/balance - tu check combien il te reste bg
/close_all - tu fermes toute les positions
/get_price - je te donne le prix d'un symbol
/lot_size - combien tu mets à chaque fois bg
/set_fix_tp_sl - tu veux fixer un SL et un TP
/set_lot_size - tu mets ton lot_size et je change en bg
/close - oula ici ca sent pas bon mais je ferme tout tqt
/get_template_channels - tu veux voir les modèles channels
/change_channel_status - tu veux changer le status d'une channel
/change_test_channel_status - tu veux changer le status d'une channel test"""
    )
    refresh_free_margin()


def infos(update, context):
    global channels_json
    with open("channels.json", "r") as cj:
        channels_json = load(cj)
    update.message.reply_text(f"J'écoute {len(channels_json)} channels, on a {len(positions)} positions, on a {round(free_margin, 4)} USD de free margin, le fix_sl est de -{fix_sl} USD et le fix_tp est de +{fix_tp} USD. Le lot_size est de {lot_size} et le reality est: {reality}")
    for i in range(len(channels_json)):
        update.message.reply_text(f"channel {i}:\nname: {channels_json[i]['name']}\nstatus: {channels_json[i]['is_active']}\ntest: {channels_json[i]['is_test']}")
    refresh_free_margin()


def get_lot_size(update, context):
    update.message.reply_text(f"Lot size: {lot_size}")
    refresh_free_margin()


def set_lot_size(update, context):
    update.message.reply_text("Vasy alors donne ton nouveau lot_size et me fait pas chier")
    return SIZE


def set_lot_size_end(update, context):
    global lot_size
    lot_size = float(update.message.text)
    update.message.reply_text(f"C'est bon j'ai compris ca va, je change en {lot_size}")
    return ConversationHandler.END


def get_channels(update, context):
    bot.send_document(user_id, open("channels.json", "rb"))
    refresh_free_margin()


def get_template_channels(update, context):
    bot.send_document(user_id, open("channels_t.json", "rb"))
    refresh_free_margin()


def change_type(update, context):
    global reality
    if reality == "LIVE": reality = "DEMO"
    else: reality = "LIVE"
    update.message.reply_text(f"J'ai changé le type de reality pour: {reality}")


def set_fix_tp_sl(update, context):
    update.message.reply_text("Tu veux fixer un SL et un TP ? Tu peux me donner ton nouveau TP")
    return TP


def set_fix_tp(update, context):
    global fix_tp
    fix_tp = update.message.text
    update.message.reply_text("Tu peux me donner ton nouveau SL ?")
    return SL


def set_fix_sl(update, context):
    global fix_sl
    fix_sl = update.message.text
    update.message.reply_text(f"C'est bon j'ai compris ca va, je change en {fix_sl} et {fix_tp}")
    return ConversationHandler.END


def set_new_channel(update, context):
    global channels_json
    if update.message.document.mime_type == "application/json" or update.message.document.mime_type == "application/binary":
        context.bot.get_file(update.message.document).download(custom_path="new_channels.json")
        with open("new_channels.json", "r") as new_channel_json:
            new_channel_json = load(new_channel_json)
        with open("channels.json", "r") as cj:
            channels_json = load(cj)
        channels_json.extend([new_channel_json])
        with open("channels.json", "w") as ci:
            dump(channels_json, ci, indent=4)
        update.message.reply_text("C'est bon j'ai mis une nouvelle channel")
    else:
        update.message.reply_text("Tu dois envoyer un fichier json")
    refresh_free_margin()


def delete_channels_start(update, context):
    update.message.reply_text("Entre le mot de passe: ")
    return PASSWORD


def delete_channels(update, context):
    if update.message.text == password:
        update.message.reply_text("Les channels sont: \n")
        with open("channels.json", "r") as cj:
            channels_json = load(cj)
        for i in range(len(channels_json)):
            update.message.reply_text(f"number: {i}\nname: {channels_json[i]['name']}")
        update.message.reply_text("Laquelle que veux-tu fermer ?")
        return DELETE
    else:
        update.message.reply_text("Mot de passe incorrect")
        return ConversationHandler.END


def delete_channels_end(update, context):
    global channels_json
    with open("channels.json", "r") as cj:
        channels_json = load(cj)
    channels_json.pop(int(update.message.text))
    with open("channels.json", "w") as ci:
        dump(channels_json, ci, indent=4)
    update.message.reply_text("C'est bon, je la supprime")
    return ConversationHandler.END


def change_channel_status(update, context):
    update.message.reply_text("Les channels sont:\n")
    for i in range(len(channels_json)):
        update.message.reply_text(f"number: {i}\nname: {channels_json[i]['name']}\nstatus: {channels_json[i]['is_active']}")
    update.message.reply_text("Laquelle que je change ? (tu peux en changer plusieurs en utilisant ;)")
    return CHANNEL


def change_channel_status_end(update, context):
    global channels_json
    with open("channels.json", "r") as cj:
        channels_json = load(cj)
    channels_json[int(update.message.text)]["is_active"] = not channels_json[int(update.message.text)]["is_active"]
    if channels_json[int(update.message.text)]["is_test"] == True:
        channels_json[int(update.message.text)]["is_test"] = False
    with open("channels.json", "w") as ci:
        dump(channels_json, ci, indent=4)
    update.message.reply_text("C'est bon, je change")
    return ConversationHandler.END


def change_multiple_channel_status_end(update, context):
    global channels_json
    with open("channels.json", "r") as cj:
        channels_json = load(cj)
    for i in range(len(update.message.text)):
        if update.message.text[i] != ";":
            channels_json[int(update.message.text[i])]["is_active"] = not channels_json[int(update.message.text[i])]["is_active"]
            if channels_json[int(update.message.text[i])]["is_test"] == True:
                channels_json[int(update.message.text[i])]["is_test"] = False
    with open("channels.json", "w") as ci:
        dump(channels_json, ci, indent=4)
    update.message.reply_text("C'est bon, je change")
    return ConversationHandler.END


def change_test_channel_status(update, context):
    update.message.reply_text("Les channels sont:\n")
    for i in range(len(channels_json)):
        update.message.reply_text(f"number: {i}\nname: {channels_json[i]['name']}\nstatus: {channels_json[i]['is_test']}")
    update.message.reply_text("Laquelle que je change en test ? (tu peux en changer plusieurs en utilisant ;)")
    return CHANNEL_TEST


def change_test_channel_status_end(update, context):
    global channels_json
    with open("channels.json", "r") as cj:
        channels_json = load(cj)
    channels_json[int(update.message.text)]["is_test"] = not channels_json[int(update.message.text)]["is_test"]
    if channels_json[int(update.message.text)]["is_active"]:
        channels_json[int(update.message.text)]["is_active"] = not channels_json[int(update.message.text)]["is_test"]
    with open("channels.json", "w") as ci:
        dump(channels_json, ci, indent=4)
    update.message.reply_text("C'est bon, je change")
    return ConversationHandler.END


def change_multiple_test_channel_status_end(update, context):
    global channels_json
    with open("channels.json", "r") as cj:
        channels_json = load(cj)
    for i in range(len(update.message.text)):
        if update.message.text[i] != ";":
            channels_json[int(update.message.text[i])]["is_test"] = not channels_json[int(update.message.text[i])]["is_test"]
            if channels_json[int(update.message.text[i])]["is_active"]:
                channels_json[int(update.message.text[i])]["is_active"] = not channels_json[int(update.message.text[i])]["is_test"]
    with open("channels.json", "w") as ci:
        dump(channels_json, ci, indent=4)
    update.message.reply_text("C'est bon, je change")
    return ConversationHandler.END


def get_price(update, context):
    update.message.reply_text("Entre le nom d'un symbol: ")
    return SYMBOL


def get_price_end(update, context):
    symbol = update.message.text
    symbol_price_data = get(f"https://candles.simplefx.com/api/v3/candles/daily/withPreviousClose?symbols={symbol}&timeFrom={int(time())}").json()["data"]
    if len(symbol_price_data) > 0:
        update.message.reply_text(f"Le prix de {symbol} est de {symbol_price_data[symbol]['close']} USD")
    else:
        update.message.reply_text(f"Ce symbole n'existe pas ou n'est pas disponible pour le moment: {symbol}")
    return ConversationHandler.END


def fail(update, context):
    update.message.reply_text("Ca marche pas ton truc la. Tu peux recommencer stp")
    return ConversationHandler.END


def cancel(update, context):
    update.message.reply_text("J'arrête tranquille minot")
    return ConversationHandler.END


def ping(update, context):
    update.message.reply_text("feur")



def change_TP_SL(tp, sl, channel_name):
    if sl == 0:
        for i in range(len(positions)):
            if positions[i]["reality"] == channel_name:
                obj = {
                    "Login": login,
                    "Reality": reality,
                    "Id": positions[i]["id"],
                    "TakeProfit": tp,
                    "StopLoss": positions[i]["stopLoss"]
                }
                if put(f"{endpoint}/trading/orders/market", json=obj, headers={"Authorization": token}).status_code != 200:
                    bot.send_message(user_id, f"Le TP n'a pas été changé, il y a eu un problème")
                    change_TP_SL(tp, sl, channel_name)
        bot.send_message(user_id, f"Nouveau TP à: {tp}")
        refresh_free_margin()
    if tp == 0:
        for i in range(len(positions)):
            if positions[i]["reality"] == channel_name:
                obj = {
                    "Login": login,
                    "Reality": reality,
                    "Id": positions[i]["id"],
                    "TakeProfit": positions[i]["takeProfit"],
                    "StopLoss": sl
                }
                if put(f"{endpoint}/trading/orders/market", json=obj, headers={"Authorization": token}).status_code != 200:
                    bot.send_message(user_id, f"Le SL n'a pas été changé, il y a eu un problème")
                    change_TP_SL(tp, sl, channel_name)
        bot.send_message(user_id, f"Nouveau SL à: {sl}")
        refresh_free_margin()


def close_order(channel_name):
    for i in range(len(positions)):
        if positions[i]["reality"] == channel_name:
            obj = {
                "Id": positions[i]["id"],
                "Volume": positions[i]["volume"],
                "RequestId": "string",
                "Login": login,
                "Reality": reality
            }
            if delete(f"{endpoint}/trading/orders/market", json=obj , headers={"Authorization": token}).status_code != 200:
                bot.send_message(user_id, "La position n'a pas été fermée, il y a eu un problème")
                close_order(channel_name)
            positions.pop(i)
    bot.send_message(user_id, f"La position du channel: {channel_name['name']} a été fermée")
    refresh_free_margin()


def order(side, sl, tp, symbol, channel_name, price, market):
    if (price*lot_size) <= (free_margin*0.9):
        if (tp == 0.0 or sl == 0.0) and price == None:
            bot.send_message(user_id, f"Il parle chinois ton pote la, j'ai pas pris la position")
        else:
            if tp == 0.0: tp = price + fix_tp
            if sl == 0.0: sl = price - fix_sl
            if market == "MARKET":
                pass
                obj = {
                    "Reality": reality,
                    "Login": login,
                    "Symbol": symbol,
                    "Side": side,
                    "Volume": lot_size,
                    "IsFIFO": True, 
                    "TakeProfit": tp,
                    "StopLoss": sl,
                    "RequestId": "string"
                }
                res = post(f"{endpoint}/trading/orders/market", json=obj, headers={"Authorization": token}).json()["data"]["marketOrders"][0]["order"]
            elif market == "LIMIT" and price != 1.00:
                obj = {
                    "ActivationPrice": price,
                    "ExpiryTime": 1893456000000,
                    "Symbol": symbol,
                    "Volume": lot_size,
                    "TakeProfit": tp,
                    "StopLoss": sl,
                    "Side": side,
                    "RequestId": "string",
                    "Login": login,
                    "Reality": reality
                }
                res = post(f"{endpoint}/trading/orders/pending", json=obj, headers={"Authorization": token}).json()["data"]["marketOrders"][0]["order"]
            else:
                bot.send_message(user_id, f"Il parle chinois ton pote la, j'ai pas pris la position")
            price = res["openPrice"]
            res["reality"] == channel_name
            positions.append(res)
            if price == "":
                bot.send_message(user_id, f"Nouvelle position {side} de TP à {tp} et SL à {sl}")
            else:
                bot.send_message(user_id, f"Nouvelle position {side} de TP à {tp} et SL à {sl}. Le prix d'ouverture est de {float(price)}")
            refresh_free_margin()
    else:
        bot.send_message(user_id, "Tu n'as pas assez de fonds pour ouvrir une position")
        refresh_free_margin()


bot = Bot(token=bot_token)
updater = Updater(bot_token, use_context=True)

# help - si t'as besoin d'aide
# stop - j'arrête bg
# close_all - tu fermes tout
# start - tu me réveilles bg
# close - tu fermes une position
# infos - si tu veux voir les infos
# set_lot_size - régler ton lot_size
# positions - get the current position
# balance - tu check combien il te reste
# get_channels - tu veux voir les channels
# change_type - changer le type de reality
# lot_size - combien tu mets à chaque fois bg
# get_price - je te donne le prix d'un symbol
# set_fix_tp_sl - tu veux fixer un SL et un TP
# delete_channels - tu veux supprimer des channels
# get_template_channels - tu veux voir les modèles channels
# change_channel_status - tu veux changer le status d'une channel
# change_test_channel_status - tu veux changer le status d'une channel test

updater.dispatcher.add_handler(CommandHandler("help", help))
updater.dispatcher.add_handler(CommandHandler("stop", stop))
updater.dispatcher.add_handler(CommandHandler("infos", infos))
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("balance", balance))
updater.dispatcher.add_handler(CommandHandler("close_all", close_all))
updater.dispatcher.add_handler(CommandHandler("lot_size", get_lot_size))
updater.dispatcher.add_handler(CommandHandler("change_type", change_type))
updater.dispatcher.add_handler(CommandHandler("positions", get_positions))
updater.dispatcher.add_handler(CommandHandler("get_channels", get_channels))
updater.dispatcher.add_handler(CommandHandler("get_template_channels", get_template_channels))
updater.dispatcher.add_handler(MessageHandler(Filters.document, set_new_channel))
updater.dispatcher.add_handler(MessageHandler(Filters.regex("quoi"), ping))

updater.dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler("set_lot_size", set_lot_size)],
    states={
        SIZE: [MessageHandler(Filters.regex("[+-]?([0-9]*[.])?[0-9]+"), set_lot_size_end), MessageHandler(None, fail)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
))

updater.dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler("close", start_close)],
    states={
        CLOSE: [MessageHandler(Filters.regex("^[0-9]*$"), close), MessageHandler(None, fail)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
))

updater.dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler("delete_channels", delete_channels_start)],
    states={
        PASSWORD: [MessageHandler(Filters.regex("^[0-9]*$"), delete_channels), MessageHandler(None, fail)],
        DELETE: [MessageHandler(None, delete_channels_end)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
))

updater.dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler("change_channel_status", change_channel_status)],
    states={
        CHANNEL: [MessageHandler(Filters.regex("^[0-9]*$"), change_channel_status_end), MessageHandler(Filters.regex(";"), change_multiple_channel_status_end), MessageHandler(None, fail)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
))

updater.dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler("change_test_channel_status", change_test_channel_status)],
    states={
        CHANNEL_TEST: [MessageHandler(Filters.regex("^[0-9]*$"), change_test_channel_status_end), MessageHandler(Filters.regex(";"), change_multiple_test_channel_status_end), MessageHandler(None, fail)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
))

updater.dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler("set_fix_tp_sl", set_fix_tp_sl)],
    states={
        TP: [MessageHandler(Filters.regex("^[0-9]*$"), set_fix_tp), MessageHandler(None, fail)],
        SL: [MessageHandler(Filters.regex("^[0-9]*$"), set_fix_sl), MessageHandler(None, fail)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
))

updater.dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler("get_price", get_price)],
    states={
        SYMBOL: [MessageHandler(None, get_price_end), MessageHandler(None, fail)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
))


@client.on(events.NewMessage(chats=[channels_json[i]["id"] for i in range(len(channels_json))]))
async def eventHandler(event):
    global channels_json
    with open("channels.json", "r") as cj:
        channels_json = load(cj)

    if (str(event.chat_id).find("-100") != -1):
        channel_id = event.peer_id.channel_id
    else:
        channel_id = event.peer_id.chat_id

    for i in range(len(channels_json)):
        if (channels_json[i]["id"] == channel_id):
            channel = channels_json[i]
    if event.media == None and event.raw_text.find("https") == -1:
        if channel["is_active"] or channel["is_test"]:
            message = openai.Completion.create(engine="text-davinci-002", prompt=f"If it is not a trade order, if it is a comment or advertising for other channels, if it is a trade follow-up (for example a goal reached or to be reached), if it is a performance summary (for example: XAUUSD TP 2 reached +100pips), answer: NOTHING\n\nIf it is a trade order, a trading instruction, extracts the following information from the message: the price (if there are several prices separated, take only the first one), the symbol (if there is Solidus in the symbol remove it in the response), the side of the trade (BUY or SELL), the type of market (by default it is MARKET and for market the indicator is: now), the stop loss (SL) and the possible several take profit (TP) (make an array in the response with the several take profit). The answer should be in the following form: Price: 1.00\nSymbol: EURUSD\nSide: BUY\nMarket: MARKET\nSL: 1.00\nTP: 1.00 (if several TP: [1.00,2.00])\n\nThe message is:\n\n{event.raw_text}", temperature=0.0, max_tokens=100, top_p=0.1, n=1, frequency_penalty=-0.5, presence_penalty=-0.5)["choices"][0]["text"]
            if message.find("NOTHING") == -1:
                if message.find("Price") != -1:
                    price = message[message.find("Price:"):].partition("\n")[0].partition(":")[2].strip()
                if message.find("Symbol"):
                    symbol = message[message.find("Symbol:"):].partition("\n")[0].partition(":")[2].strip()
                    if symbol.upper() == "GOLD": symbol = "XAUUSD"

                symbol_price_data = get(f"https://candles.simplefx.com/api/v3/candles/daily/withPreviousClose?symbols={symbol}&timeFrom={int(time())}").json()["data"]

                if len(symbol_price_data) > 0:
                    symbol_price = float(symbol_price_data[symbol]["close"])

                    if message.find("Side"):
                        side = message[message.find("Side:"):].partition("\n")[0].partition(":")[2].strip()
                    if message.find("Market"):
                        market = message[message.find("Market:"):].partition("\n")[0].partition(":")[2].strip()
                    if message.find("SL"):
                        sl = message[message.find("SL:"):].partition("\n")[0].partition(":")[2].strip()
                    if message.find("TP"):
                        tp = message[message.find("TP:"):].partition("\n")[0].partition(":")[2].strip()
                        if tp.find("[") != -1:
                            tp = tp[tp.find("[")+1:tp.find("]")].split(",")
                            for i in range(len(tp)):
                                if ((float(tp[i]) > symbol_price and side == "BUY") or (float(tp[i]) < symbol_price and side == "SELL")) and abs(float(tp[i]) - symbol_price) >= symbol_price*0.0007:
                                    tp = tp[i]
                                    break
                                if ((float(tp[i]) <= symbol_price and side == "BUY") or (float(tp[i]) >= symbol_price and side == "SELL")) and i > 1 and abs(float(tp[i]) - symbol_price) >= symbol_price*0.0007:
                                    tp = tp[i+1]
                                    break

                    if float(tp) != 1.0 and float(sl) != 1.0 and ((side == "BUY" and float(tp) > symbol_price) or (side == "SELL" and float(tp) < symbol_price)) and ((side == "BUY" and float(sl) < symbol_price) or (side == "SELL" and float(sl) > symbol_price)):
                        bot.send_message(user_id, f"Nouveau message de {channel['name']}:\n{event.raw_text}")
                        if channel["is_active"]:
                            order(side, float(sl), float(tp), symbol, channel["name"], float(price), market)
                        if channel["is_test"]:
                            bot.send_message(user_id, f"{side}, SL: {sl}, TP: {tp}, {symbol}, {price}, {market}, {channel['name']}")
                else:
                    bot.send_message(user_id, f"Nouveau message de {channel['name']}:\n{event.raw_text}")
                    bot.send_message(user_id, f"Ce symbole n'existe pas ou n'est pas disponible pour le moment: {symbol}")

client.start()
updater.start_polling()
client.run_until_disconnected()
