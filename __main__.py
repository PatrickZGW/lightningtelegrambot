import telegram
import telegram.bot
from telegram.ext import messagequeue as mq, Updater, CommandHandler, ConversationHandler, Filters, MessageHandler, JobQueue
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)
import sqlite3
import logging
import time
import datetime

import lnd
import cryptoprices
import config
from _sqlite3 import IntegrityError

config = config.Config()

token = config.TOKEN #bot token for your bot (obtained from botfather)

connection = lnd.gRPC_Connection()
price_puller = cryptoprices.CoinbasePricePuller()

db_connection = lnd.LND_Database(connection, 300)
db_connection.start()

bot = telegram.bot.Bot(token=token)
updater = Updater(bot=bot)
dispatcher = updater.dispatcher

job_queue = JobQueue(bot)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

def start(bot, update):
    start_text = 'This bot will provide you with information about the LTC lightning network as observer from the LiteStrike node.\n\nPress /help for a list of commands'
    keyboard = telegram.ReplyKeyboardRemove(remove_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id, text=start_text, reply_markup=keyboard)
    
def help(bot, update):
    help_text = '''
/start - Start the bot and show welcome message
/help - Show this help message
/getinfo - Show information about the node
/networkinfo - Get Network statistics
/nodes - Show number of nodes currently online
/capacity - Show total network capacity in LTC
/listpeers - List peers of the LiteStrike node

/subscribe - Get a daily summary of the network statistics
/unsubscribe - Unsubscribe from daily updates
'''
    update.message.reply_text(help_text)
    
def get_your_chat_id(bot, update):
    update.message.reply_text('Your chat_id is: ' + str(update.message.chat_id))
    
def walletbalance(bot, update):
    balance = connection.WalletBalance() 
    balance = str(balance)    
    update.message.reply_text(balance)
    
def networkinfo(bot, update):
    network = connection.NetworkInfo()
    network = str(network)
    update.message.reply_text(network)
    
def getinfo(bot, update):
    info = connection.GetInfo()
    info = str(info)
    update.message.reply_text(info)
    
def listpeers(bot, update):
    peers = connection.ListPeers()
    peers = str(peers)
    update.message.reply_text(peers)
    
def peeraliases(bot, update):
    aliases = connection.ListPeerAliases()
    aliases = '\n'.join(aliases)
    update.message.reply_text(aliases)
    
def networkcapacity(bot, update):
    capacity = connection.NetworkCapacity()
    capacity = float(capacity) * 1e-8
    ltc_price = price_puller.get_price('LTC', 'USD')
    
    capacity = str(capacity) + ' LTC' + ' (' + str("{:,}".format(round(float(ltc_price) * capacity,2))) + ' USD)'
    update.message.reply_text(capacity)
    
def num_nodes(bot, update):
    info = connection.NetworkInfo()
    nodes = info.num_nodes
    update.message.reply_text(nodes)
    
def subscribe(bot, update):    
    try:
        db_connection.add_subscriber(update.message.chat_id)
        update.message.reply_text('You are now getting daily updates on network statistics')
    except IntegrityError:
        update.message.reply_text('You are already subscribed!')
    
def unsubscribe(bot, update):
    try:
        db_connection.remove_subscriber(update.message.chat_id)
        update.message.reply_text('You have successfully unsubscribed')
        
    except IntegrityError:
        update.message.reply_text('You were already not a subscriber')
        
    
    
   
start_handler = CommandHandler('start', start)
help_handler = CommandHandler('help', help)
chat_id_handler = CommandHandler('chatid', get_your_chat_id)
walletbalance_handler = CommandHandler('walletbalance', walletbalance)
networkinfo_handler = CommandHandler('networkinfo', networkinfo)
getinfo_handler = CommandHandler('getinfo', getinfo)
listpeers_handler = CommandHandler('listpeers', listpeers)
peeraliases_handler = CommandHandler('peeraliases', peeraliases)
networkcapacity_handler = CommandHandler('capacity', networkcapacity)
num_nodes_handler = CommandHandler('nodes', num_nodes)
subscribe_handler = CommandHandler('subscribe', subscribe)
unsubscribe_handler = CommandHandler('unsubscribe', unsubscribe)
    
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(chat_id_handler)
dispatcher.add_handler(walletbalance_handler)
dispatcher.add_handler(networkinfo_handler)
dispatcher.add_handler(getinfo_handler)
dispatcher.add_handler(listpeers_handler)
dispatcher.add_handler(peeraliases_handler)
dispatcher.add_handler(networkcapacity_handler)
dispatcher.add_handler(num_nodes_handler)
dispatcher.add_handler(subscribe_handler)
dispatcher.add_handler(unsubscribe_handler)

job_queue.run_daily(db_connection.send_update, datetime.time(hour=18, minute=5, second=0))
job_queue.start()

updater.start_polling()