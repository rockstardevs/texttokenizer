from dataclasses import dataclass, field
from loguru import logger as log
from pathlib import Path
from tempfile import mkdtemp
from typing import Set, Dict, List, Optional

from .util import suffix_path
from .token import Font


@dataclass(kw_only=True)
class Document:
    """Document represents a single (mulit page) document that is being analyzed."""

    # These attributes are needed at instantiation.
    annotate: bool
    filename: Path
    pages: Optional[str]
    merge_bboxes: bool
    tmproot: Path

    # These attributes are populated through the phases.
    preprocessed: Optional[Path]
    tempdir: Optional[Path]
    fontdir: Optional[Path]
    page_indices: List[int] = field(default_factory=list)
    tokens: Dict = field(default_factory=dict)
    fonts: Set[Font] = field(default_factory=set)

    def __post_init__(self):
        self.preprocessed = suffix_path(self.filename, "preprocessed")
        if self.annotate:
            self.tempdir = Path(
                mkdtemp(
                    prefix=f"{self.filename.with_suffix('').name}-", dir=self.tmproot
                )
            )
            self.fontdir = self.tempdir.joinpath("fonts")
            log.info(f"using tempdir {self.tempdir}")

    def save_tokens(self, idx: int):
        filename = suffix_path(self.filename, f"tokens-{idx}", ext=".txt")
        with open(filename, "w") as f:
            for token in self.tokens[idx]:
                f.write(str(token) + "\n")
        log.info(f"writing tokens in {filename}")
