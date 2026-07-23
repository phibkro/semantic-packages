from __future__ import annotations

import json
import math
import sys


request = json.loads(sys.stdin.readline())
x = abs(float.fromhex(request["x"]))
y = abs(float.fromhex(request["y"]))
large = max(x, y)
small = min(x, y)
value = 0.0 if large == 0.0 else large * math.sqrt(1.0 + (small / large) ** 2)
print(json.dumps({"value": value.hex()}, sort_keys=True, separators=(",", ":")))
