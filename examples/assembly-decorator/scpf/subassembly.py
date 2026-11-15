"""Reusable subassembly used by the @assembly qualification fixture."""

from scpf.core import Box
from scpf.runner import assembly, component


@component
class Post:
    def build(self):
        return Box(10, 10, 20)


@assembly
class PostPair:
    def build(self):
        left = Post(name="left").at(x=-15)
        right = left.copy().at(x=15)
        return left + right
