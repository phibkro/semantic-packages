from __future__ import annotations

import json
import math
import sys


request = json.loads(sys.stdin.readline())
x = float.fromhex(request["x"])
y = float.fromhex(request["y"])
value = math.sqrt(x * x + y * y)
print(json.dumps({"value": value.hex()}, sort_keys=True, separators=(",", ":")))
