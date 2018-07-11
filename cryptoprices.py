import requests

class CoinbasePricePuller:
    
    def get_price(self, crypto='BTC', fiat='USD'):
        url = 'https://api.coinbase.com/v2/prices/' + crypto + '-' + fiat + '/spot'
        res = requests.get(url)
        res = res.json()
        current_price = res['data']['amount']
        
        return current_price