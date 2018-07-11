import rpc_pb2 as ln
import rpc_pb2_grpc as lnrpc
import grpc
import os
import codecs
import sqlite3
import time
import threading

import cryptoprices
import config

config = config.Config()

ip = config.GRPC_IP #ip of the server where lnd is running
port = config.GRPC_PORT #grpc port
admin_macaroon_path = config.GRPC_ADMIN_MACAROON_PATH #path to the downloaded admin.macaroon
tls_cert_path = config.GRPC_TLS_CERT_PATH #path to the downloaded tls certificate

def metadata_callback(context, callback):
    # for more info see grpc docs
    callback([('macaroon', macaroon)], None)
    
# Lnd admin macaroon is at ~/.lnd/admin.macaroon on Linux and
# ~/Library/Application Support/Lnd/admin.macaroon on Mac
with open(os.path.expanduser(admin_macaroon_path), 'rb') as f:
    macaroon_bytes = f.read()
    macaroon = codecs.encode(macaroon_bytes, 'hex')

cert = open(os.path.expanduser(tls_cert_path), 'rb').read()

# build ssl credentials using the cert the same as before
cert_creds = grpc.ssl_channel_credentials(cert)

# now build meta data credentials
auth_creds = grpc.metadata_call_credentials(metadata_callback)

# combine the cert credentials and the macaroon auth credentials
# such that every call is properly encrypted and authenticated
combined_creds = grpc.composite_channel_credentials(cert_creds, auth_creds)

# finally pass in the combined credentials when creating a channel
channel = grpc.secure_channel(ip + ':' + port, combined_creds)
stub = lnrpc.LightningStub(channel)

# Due to updated ECDSA generated tls.cert we need to let gprc know that
# we need to use that cipher suite otherwise there will be a handhsake
# error when we communicate with the lnd rpc server.
os.environ["GRPC_SSL_CIPHER_SUITES"] = 'HIGH+ECDSA'

class gRPC_Connection:
    
    def WalletBalance(self):
        # Retrieve and display the wallet balance
        response = stub.WalletBalance(ln.WalletBalanceRequest())
        return response
    
    def NetworkInfo(self):
        response = stub.GetNetworkInfo(ln.NetworkInfoRequest())
        return response
    
    def GetInfo(self):
        response = stub.GetInfo(ln.GetInfoRequest())
        return response
    
    def ListPeers(self):
        response = stub.ListPeers(ln.ListPeersRequest())
        return response
    
    def GetNodeInfo(self, pubkey):
        response = stub.GetNodeInfo(ln.NodeInfoRequest(pub_key=pubkey))
        return response
    
    def ListPeerAliases(self):
        peers = self.ListPeers().peers
        aliases = []
        for peer in peers:
            aliases.append(self.GetNodeInfo(peer.pub_key).node.alias)
        return aliases
    
    def NetworkCapacity(self):
        capacity = stub.GetNetworkInfo(ln.NetworkInfoRequest()).total_network_capacity
        return capacity

class LND_Database(threading.Thread):
    
    def __init__(self, connection, sleep):
        super(LND_Database, self).__init__()  
        self.connection = connection
        self.sleep = sleep
        
    def run(self):
        self.start_saving(self.sleep)    
        
    def get_subscribers(self):
        conn = sqlite3.connect(config.SQLITEDB_PATH)   
        c = conn.cursor()
        c.execute('SELECT chat_id FROM subscribers')
        subscribers_db = c.fetchall()
        c.close()
        
        subscribers = []
        for subscriber in subscribers_db:
           subscribers.append(subscriber[0]) 
        
        return subscribers
    
    def add_subscriber(self, chat_id):
        conn = sqlite3.connect(config.SQLITEDB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO subscribers (chat_id) VALUES(?)', (chat_id,))
        c.close()
        conn.commit()
        
    def remove_subscriber(self, chat_id):
        conn = sqlite3.connect(config.SQLITEDB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM subscribers WHERE chat_id = ?', (chat_id,))
        c.close()
        conn.commit()
        
    def insert_statistics(self, num_nodes, capacity_ltc, capacity_usd, price, num_channels):  
        conn = sqlite3.connect(config.SQLITEDB_PATH)             
        c = conn.cursor()
        c.execute('INSERT INTO statistics (num_nodes, capacity_ltc, capacity_usd, price, num_channels) VALUES (?, ?, ?, ? , ?)', (num_nodes, capacity_ltc, capacity_usd, price, num_channels))
        c.close()
        conn.commit()
        
    def get_latest_statistics(self):
        conn = sqlite3.connect(config.SQLITEDB_PATH)
        c = conn.cursor()
        c.execute('SELECT num_nodes, capacity_ltc, capacity_usd, price, num_channels FROM statistics WHERE id = (SELECT MAX(id) FROM statistics)')
        
        response = c.fetchall()   
        c.close()
              
        return response
        
    def start_saving(self, sleep=300):
        price_puller = cryptoprices.CoinbasePricePuller()
        
        while True:        
            network = self.connection.NetworkInfo()
            ltc_price = price_puller.get_price('LTC', 'USD')
            
            num_nodes = network.num_nodes
            capacity_ltc = float(network.total_network_capacity * 1e-8)
            capacity_usd = capacity_ltc * float(ltc_price)
            price = ltc_price
            num_channels = network.num_channels
            
            self.insert_statistics(num_nodes, capacity_ltc, capacity_usd, price, num_channels)
            
            time.sleep(sleep)
            
    def send_update(self, bot, job):
        subscribers = self.get_subscribers()
        
        statistics = self.get_latest_statistics()[0]
        num_nodes = statistics[0]
        capacity_ltc = statistics[1]
        capacity_usd = "{:,}".format(round(statistics[2],2))
        price = statistics[3]
        num_channels = statistics[4]
        
        message = '''
Number of nodes: {0}
Capacity: {1} LTC ({2} USD)
Number of channels: {3}
'''.format(num_nodes, capacity_ltc, capacity_usd, num_channels)
            
        for subscriber in subscribers:
            bot.send_message(chat_id=subscriber, text=message)
        
        