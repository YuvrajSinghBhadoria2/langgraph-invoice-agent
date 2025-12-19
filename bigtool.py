import random
from typing import List, Optional

class BigtoolPicker:
    """
    Bigtool selector for choosing the best tool from a pool.
    """
    @staticmethod
    def select(capability: str, pool: List[str]) -> str:
        # Real-world logic would involve model-based selection,
        # but for this demo, we'll pick the first one or a random one.
        choice = random.choice(pool)
        print(f"[Bigtool] Selected tool '{choice}' for capability '{capability}' from pool {pool}")
        return choice
