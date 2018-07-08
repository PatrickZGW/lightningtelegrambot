import rpc_pb2 as ln
import rpc_pb2_grpc as lnrpc
import grpc
import os
import codecs

ip = 'localhost' #ip of the server where lnd is running
port = '10009' #grpc port
admin_macaroon_path = '~/.lnd/admin.macaroon' #path to the downloaded admin.macaroon
tls_cert_path = '~/.lnd/tls.cert' #path to the downloaded tls certificate

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
    

