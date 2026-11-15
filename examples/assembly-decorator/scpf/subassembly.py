"""Reusable subassembly used by the @assembly qualification fixture."""

from scpf.core import Box
from scpf.model_objects import Placement
from scpf.runner import assembly, component


@component
class Post:
    def build(self):
        # Keep the existing visible -15/+15 qualification geometry while the
        # occurrence path itself stays replay-safe.
        return Box(10, 10, 20).move(x=-15)


@assembly
class PostPair:
    def build(self):
        left = Post(name="left")
        right = left.copy(name="right", placement=Placement(x=30))
        return left + right
