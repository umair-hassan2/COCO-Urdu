"""Reference-free QE scorers (all open models, no paid APIs). Each exposes score(pairs) -> list[float] on (src_en, mt_ur[, image]) tuples.

Heavy imports are inside the classes so the package imports without torch.
"""
