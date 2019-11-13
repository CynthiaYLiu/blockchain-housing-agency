import pickle
from collections import defaultdict

from blockchain.block import Block
from blockchain.db import DB
from blockchain.transaction import CoinbaseTx
from blockchain.utils import ContinueIt, BreakIt


class Blockchain(object):
    """ Blockchain keeps a sequence of Blocks
    Attributes:
        _tip (bytes): Point to the latest hash of block.
        _db (DB): DB instance
    """
    latest = 'l'
    db_file = '../database/blockchain.db'
    genesis_coinbase_data = 'The Times 03/Jan/2009 Chancellor on brink of second bailout for banks'

    def __init__(self, subsidy=100, cointype=None, address=None):
        self._db = DB(Blockchain.db_file)

        try:
            self._tip = self._db.get('l')
        except KeyError:
            if not address:
                self._tip = None
            else:
                cb_tx = CoinbaseTx(
                    address, subsidy, cointype, Blockchain.genesis_coinbase_data).set_id()
                self.genesis = Block([cb_tx], 0).pow_of_block()


    def _block_put(self, block):        
        self._db.put(block.hash, block.serialize())
        self._db.put('l', block.hash)
        self._tip = block.hash
        self._db.commit()

    def MineBlock(self, transaction_lst):
        # Mines a new block with the provided transactions
        last_hash = self._db.get('l')
        encoded_block = self._db.get(last_hash)
        prev_block = pickle.loads(encoded_block)
        prev_height = prev_block.height
        new_block = Block(transaction_lst, prev_height, last_hash).pow_of_block()
        return new_block

    def find_utxo(self, address=None):
        # Finds and returns all unspent transaction outputs
        utxos = []
        unspent_txs = self.find_unspent_transactions(address)

        for tx in unspent_txs:
            for out in tx.vout:
                if out.is_locked_with_key(address):
                    utxos.append(out)

        return utxos

    def find_unspent_transactions(self, pubkey_hash):
        # Returns a list of transactions containing unspent outputs
        spent_txo = defaultdict(list)
        unspent_txs = []
        for block in self.blocks:
            for tx in block.transactions:

                if not isinstance(tx, CoinbaseTx):
                    for vin in tx.vin:
                        if vin.uses_key(pubkey_hash):
                            tx_id = vin.tx_id
                            spent_txo[tx_id].append(vin.vout)

                tx_id = tx.ID
                try:
                    for out_idx, out in enumerate(tx.vout):
                        # Was the output spent?
                        if spent_txo[tx_id]:
                            for spent_out in spent_txo[tx_id]:
                                if spent_out == out_idx:
                                    raise ContinueIt

                        if out.is_locked_with_key(pubkey_hash):
                            unspent_txs.append(tx)
                except ContinueIt:
                    pass

        return unspent_txs

    def find_spendable_outputs(self, pubkey_hash, amount, cointype):
        # Finds and returns unspent outputs to reference in inputs
        accumulated = 0
        unspent_outputs = defaultdict(list)
        unspent_txs = self.find_unspent_transactions(pubkey_hash)

        try:
            for tx in unspent_txs:
                tx_id = tx.ID

                for out_idx, out in enumerate(tx.vout):
                    if out.is_locked_with_key(pubkey_hash) and out.cointype==cointype and accumulated < amount:
                        accumulated += out.value
                        unspent_outputs[tx_id].append(out_idx)

                        if accumulated >= amount:
                            raise BreakIt
        except BreakIt:
            pass

        return accumulated, unspent_outputs

    @property
    def blocks(self):
        current_tip = self._tip
        while True:
            if not current_tip:
                # Encounter genesis block
                raise StopIteration
            encoded_block = self._db.get(current_tip)
            block = pickle.loads(encoded_block)
            yield block
            current_tip = block.prev_block_hash
    
    def find_transaction(self, ID):
        # finds a transaction by its ID
        for block in self.blocks:
            for tx in block.transactions:
                if tx.ID == ID:
                    return tx

        return None

    def sign_transaction(self, tx, priv_key):
        prev_txs = {}
        for vin in tx.vin:
            prev_tx = self.find_transaction(vin.tx_id)
            prev_txs[prev_tx.ID] = prev_tx

        tx.sign(priv_key, prev_txs)
