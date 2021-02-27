from pyava import *
from pyava.api import *
from pyava.txparse import *

def read_any_tx(url, function: str, tx: str) -> Dict:
    txdata = defaultClient.call(url, function, txID=tx, encoding='hex')['tx']
    tx_raw = from_hex(txdata[2:])
    txdata = parse(tx_raw, 0, SignedTx)[0]
    return txdata['unsignedTx']

def read_Ptx(tx: str) -> Dict:
    return read_any_tx('ext/P', 'platform.getTx', tx)

def read_Xtx(tx: str) -> Dict:
    return read_any_tx('ext/bc/X', 'avm.getTx', tx)
