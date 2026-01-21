"""
TODO
"""

import json
from typing import Any


def c_to_json(c_file: str) -> Any:
    pass


def parse(c_code: str, jsn: str) -> None:
    blob = c_to_json(c_code)
    if jsn:
        json.dump(blob, open(jsn, "w"))
    else:
        print(json.dumps(blob))
