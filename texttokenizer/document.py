import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

import fitz
from loguru import logger as log

from .token import Font, Token
from .util import expand_page_list


@dataclass(kw_only=True)
class Document:
    """Document represents a single (multi page) document that is being analyzed."""

    # These attributes are needed at instantiation.
    filename: Path
    pages: str | None

    # These attributes are populated through the phases.
    pdf_doc: fitz.Document | None
    page_indices: list[int] = field(default_factory=list)
    tokens: list = field(default_factory=list)
    fonts: set[Font] = field(default_factory=set)

    def __post_init__(self):
        self.update_pdf_doc(self.filename)

    def update_pdf_doc(self, filename: Path):
        if self.pdf_doc:
            self.pdf_doc.close()
        self.filename = filename
        self.pdf_doc = fitz.open(self.filename)
        self.page_indices = expand_page_list(self.pages, len(self.pdf_doc) - 1)

    def save_templatizer_tokens(self, filename: Path):
        data = {}
        for i, token in enumerate(self.tokens):
            data[f"token_{i}"] = [token.as_templatizer_dict()]
        with open(filename, "w") as f:
            f.write(json.dumps(data))
        log.info(f"writing tokens in {filename}")

    def save_csv_tokens(self, filename: Path):
        with open(filename, "w") as f:
            writer = csv.writer(f)
            writer.writerow(Token.csv_headers())
            for token in self.tokens:
                writer.writerow(token.as_csv_row())
        log.info(f"writing tokens in {filename}")
