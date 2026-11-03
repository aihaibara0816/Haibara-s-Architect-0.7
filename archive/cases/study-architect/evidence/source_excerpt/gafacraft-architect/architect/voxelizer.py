"""One unit conversion and one half-up rounding policy for all components."""
from decimal import Decimal, ROUND_HALF_UP
from .legacy import core

def q(value, scale):
    return int((Decimal(str(value)) * Decimal(str(scale))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def q3(values, scale):
    return tuple(q(v, scale) for v in values)

def quantized_box(lo, hi, scale):
    a, b = q3(lo, scale), q3(hi, scale)
    if any(x >= y for x, y in zip(a, b)):
        raise ValueError("Feature collapsed after quantization; increase scale or explicitly redesign it")
    return a, b

def scene_from_readback(build):
    visible = {p: s for p, s in build.blocks.items() if s != core.AIR}
    return core.Scene(tuple(build.size), visible)

