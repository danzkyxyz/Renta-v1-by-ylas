from web3 import Web3, HTTPProvider
from eth_abi import encode
from decimal import Decimal
import json
import time
import random
import requests
import schedule

# Load proxies from the proxylist.txt file
def load_proxies(file_path):
    with open(file_path, 'r') as file:
        proxies = [line.strip() for line in file if line.strip()]
    return proxies

# Custom HTTP Provider with proxy support
class ProxyHTTPProvider(Web3.HTTPProvider):
    def __init__(self, endpoint_uri=None, request_kwargs=None, proxies=None):
        if request_kwargs is None:
            request_kwargs = {}
        if proxies:
            request_kwargs["proxies"] = proxies
        super().__init__(endpoint_uri=endpoint_uri, request_kwargs=request_kwargs)

# Extract IP address from proxy URL
def extract_ip(proxy_url):
    if "@" in proxy_url:  # Proxy with authentication
        proxy = proxy_url.split("@")[1]
    else:  # Proxy without authentication
        proxy = proxy_url
    return proxy.split(":")[0]

# Get the real external IP using an IP checker API
def get_real_ip(proxy):
    try:
        response = requests.get("https://api.ipify.org?format=json", proxies=proxy, timeout=5)
        if response.status_code == 200:
            return response.json().get("ip", "Unknown")
        else:
            return "Unknown"
    except Exception as e:
        print(f"Error fetching real IP: {e}")
        return "Unknown"

# Rotate through proxies
def get_random_proxy(proxies):
    proxy = random.choice(proxies)
    proxy_dict = {
        "http": proxy,
        "https": proxy,
    }
    return proxy_dict, proxy

# Load proxies
proxy_list = load_proxies("proxylist.txt")

if not proxy_list:
    print("No proxies found in proxylist.txt!")
    exit()

# Select a random proxy
proxy_dict, proxy_url = get_random_proxy(proxy_list)

# Get real external IP
real_ip = get_real_ip(proxy_dict)

# Initialize Web3 with the selected proxy
web3 = Web3(ProxyHTTPProvider(endpoint_uri="https://rpc-bluetail.renta.network", proxies=proxy_dict))

#web3 = Web3(Web3.HTTPProvider("https://rpc-bluetail.renta.network"))
chainId = web3.eth.chain_id

# Connecting to Web3
if web3.is_connected():
    print("Web3 Connected...\n")
else:
    print("Error Connecting. Please Try Again. Exiting...")
    exit()

def tapOnchain(sender, key):
    try:
        gasPricePlus = web3.from_wei(web3.eth.gas_price, 'gwei')
        gasPrice = web3.to_wei(gasPricePlus*Decimal(1.1), 'gwei')
        nonce = web3.eth.get_transaction_count(sender)
        tapaddr = web3.to_checksum_address('0x3280E2F59536991B5726B41B9bEEd613B1E0Be0A')
        data = '0xf482ee72'

        gasAmount = web3.eth.estimate_gas({
            'chainId': chainId,
            'from': sender,
            'to': tapaddr,
            'data': data,
            'gasPrice': gasPrice,
            'nonce': nonce
        })

        tap_tx = {
            'chainId': chainId,
            'from': sender,
            'to': tapaddr,
            'data': data,
            'gas': gasAmount,
            'gasPrice': gasPrice,
            'nonce': nonce
        }
        
        # Sign and send the transaction
        tx_hash = web3.eth.send_raw_transaction(web3.eth.account.sign_transaction(tap_tx, key).rawTransaction)
        # Get transaction hash
        print(f'For Address {sender} | Using IP {real_ip}')
        print(f'Processing Tap Onchain...')
        web3.eth.wait_for_transaction_receipt(tx_hash)
        print(f'Tap Onchain Success!')
        print(f'TX-ID : {str(web3.to_hex(tx_hash))}')
    except Exception as e:
        print(f"Error: {e}")
        pass

while True:
    with open('pvkeylist.txt', 'r') as file:
        local_data = file.read().splitlines()
        for pvkeylist in local_data:
            sender = web3.eth.account.from_key(pvkeylist)
            tapOnchain(sender.address, sender.key)