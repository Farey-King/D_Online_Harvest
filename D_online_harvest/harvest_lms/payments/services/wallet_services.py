# payments/services/wallet_service.py

from web3 import Web3
from cryptography.fernet import Fernet # type: ignore
from django.conf import settings

class WalletService:

    @staticmethod
    def generate_deposit_wallet():
        web3 = Web3(Web3.HTTPProvider(settings.BSC_RPC))

        # create wallet
        account = web3.eth.account.create()

        private_key = account._private_key.hex()
        address = account.address

        # encrypt private key
        f = Fernet(settings.ENCRYPTION_KEY)
        encrypted_key = f.encrypt(private_key.encode()).decode()

        return address, encrypted_key
