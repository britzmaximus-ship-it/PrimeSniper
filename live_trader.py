import base58
import requests
from typing import Optional

from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.api import Client

from config import RPC_URL, SOLANA_PRIVATE_KEY, MAX_SOL_PER_TRADE, MIN_SOL_RESERVE_SOL

LAMPORTS_PER_SOL = 1_000_000_000
SOL_MINT = "So11111111111111111111111111111111111111112"
JUP_QUOTE = "https://quote-api.jup.ag/v6/quote"
JUP_SWAP = "https://quote-api.jup.ag/v6/swap"

class LiveTrader:
    def __init__(self):
        if not SOLANA_PRIVATE_KEY:
            raise ValueError("SOLANA_PRIVATE_KEY missing")
        self.client = Client(RPC_URL)
        secret = base58.b58decode(SOLANA_PRIVATE_KEY)
        self.kp = Keypair.from_bytes(secret)

    def sol_balance(self) -> float:
        bal = self.client.get_balance(self.kp.pubkey()).value
        return bal / LAMPORTS_PER_SOL

    def buy_token_with_sol(self, out_mint: str, sol_amount: float, slippage_bps: int = 2500) -> Optional[str]:
        """
        Buys out_mint using SOL via Jupiter.
        Returns tx signature if sent, else None.
        """
        sol_bal = self.sol_balance()
        if sol_bal - sol_amount < MIN_SOL_RESERVE_SOL:
            return None
        if sol_amount > MAX_SOL_PER_TRADE:
            sol_amount = MAX_SOL_PER_TRADE

        amount_lamports = int(sol_amount * LAMPORTS_PER_SOL)

        quote = requests.get(
            JUP_QUOTE,
            params={
                "inputMint": SOL_MINT,
                "outputMint": out_mint,
                "amount": str(amount_lamports),
                "slippageBps": str(slippage_bps),
            },
            timeout=20,
        ).json()

        if "error" in quote:
            return None

        swap = requests.post(
            JUP_SWAP,
            json={
                "quoteResponse": quote,
                "userPublicKey": str(self.kp.pubkey()),
                "wrapAndUnwrapSol": True,
            },
            timeout=30,
        ).json()

        swap_tx = swap.get("swapTransaction")
        if not swap_tx:
            return None

        tx_bytes = base58.b58decode(swap_tx)
        vtx = VersionedTransaction.from_bytes(tx_bytes)
        signed = VersionedTransaction(vtx.message, [self.kp])

        sig = self.client.send_raw_transaction(bytes(signed)).value
        return str(sig)