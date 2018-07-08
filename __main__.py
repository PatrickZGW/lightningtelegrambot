import telegram
import telegram.bot
from telegram.ext import messagequeue as mq, Updater, CommandHandler, ConversationHandler, Filters, MessageHandler
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)
import sqlite3
import logging
import time

import lnd

token = '' #bot token

connection = lnd.gRPC_Connection()

bot = telegram.bot.Bot(token=token)
updater = Updater(bot=bot)
dispatcher = updater.dispatcher

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

def start(bot, update):
    update.message.reply_text('This bot will provide you with information about the LTC lightning network as observer from the LiteStrike node.\n\nPress /help for a list of commands')
    
def help(bot, update):
    help_text = '''
/start - Start the bot and show welcome message
/help - Show this help message
/getinfo - Show information about the node
/networkinfo - Get Network statistics
/listpeers - List peers of the LiteStrike node
/peeraliases - Show aliases of connected peers
/capacity - Show total network capacity in LTC'''
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
    capacity = str(float(capacity)*1e-8) + ' LTC'
    update.message.reply_text(capacity)
 
   
start_handler = CommandHandler('start', start)
help_handler = CommandHandler('help', help)
chat_id_handler = CommandHandler('chatid', get_your_chat_id)
walletbalance_handler = CommandHandler('walletbalance', walletbalance)
networkinfo_handler = CommandHandler('networkinfo', networkinfo)
getinfo_handler = CommandHandler('getinfo', getinfo)
listpeers_handler = CommandHandler('listpeers', listpeers)
peeraliases_handler = CommandHandler('peeraliases', peeraliases)
networkcapacity_handler = CommandHandler('capacity', networkcapacity)
    
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(chat_id_handler)
dispatcher.add_handler(walletbalance_handler)
dispatcher.add_handler(networkinfo_handler)
dispatcher.add_handler(getinfo_handler)
dispatcher.add_handler(listpeers_handler)
dispatcher.add_handler(peeraliases_handler)
dispatcher.add_handler(networkcapacity_handler)


updater.start_polling()