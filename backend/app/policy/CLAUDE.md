# app/policy — frozen, code-reviewed config data

Python constants validated by Pydantic at import time. Every constant has
a citation comment naming its source (statute, dataset, RFC, etc.).

May import: stdlib, third-party (Pydantic).

May not import: anything from `app.*`. The layering contract puts policy
at the bottom of the graph.

LL97 caps and the retrofit scenario library live here as
Pydantic-validated frozen dataclasses (`ll97_caps.py`, `retrofits.py`).
