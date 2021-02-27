# Avalanche Python SDK

This library provides functions for working with the Avalanche cryptocurrency API, parse transactions and work with addresses.

## Calling API

```
from pyava.api import *

tx = defaultClient.call('ext/bc/X', 'avm.getTx', txid)
```

## Parsing transactions

```
from pyava.api import *

data = read_Ptx(txid)
```

NOTE that not all data structures are currently represented but it should be easy enough to fill the missing ones into `pyava.txparse`
based on the docs or gecko golang source code.
