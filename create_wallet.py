from web3 import Web3

# Generate a new Ethereum account
new_account = Web3().eth.account.create()

# Print private key and address
print("Private Key:", new_account.key.hex())
print("Wallet Address:", new_account.address)
