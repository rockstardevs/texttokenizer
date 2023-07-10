from dataclasses import dataclass, field
from loguru import logger as log
from pathlib import Path
from typing import Set, Dict, List, Optional

from .util import suffix_path
from .token import Font


@dataclass(kw_only=True)
class Document:
    """Document represents a single (mulit page) document that is being analyzed."""

    filename: Path
    preprocessed: Optional[Path]
    pages: Optional[str]
    page_indices: List[int] = field(default_factory=list)
    tokens: Dict = field(default_factory=dict)
    fonts: Set[Font] = field(default_factory=set)

    def __post_init__(self):
        self.preprocessed = suffix_path(self.filename, "preprocessed")

    def save_tokens(self, idx: int):
        filename = suffix_path(self.filename, f"tokens-{idx}", ext=".txt")
        with open(filename, "w") as f:
            for token in self.tokens[idx]:
                f.write(str(token) + "\n")
        log.info(f"writing tokens in {filename}")
