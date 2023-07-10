import fitz

from abc import ABC, abstractmethod
from loguru import logger as log
from typing import List, Dict, Set, Tuple

from .document import Document
from .token import Token, Font
from .util import expand_page_list, merge_bboxes


class Processor(ABC):
    """
    Represents a processor capable of tokenizing a given document.
    """

    @abstractmethod
    def tokenize(self, document: Document):
        """processes the given document to tokenize it."""


class FitzProccessor(Processor):
    """
    Implements a fitz (PyMuPDF) based processor.
    """

    def tokenize(self, document: Document):
        with fitz.open(document.preprocessed) as doc:
            pages = (
                expand_page_list(document.pages, len(doc) - 1)
                if document.pages
                else None
            )
            if pages:
                document.page_indices = pages
            for idx in range(len(doc)):
                if pages and idx not in pages:
                    continue
                tokens, fonts = self.tokenize_page(idx, doc[idx])
                log.info(f"extracted {len(tokens)} tokens from page {idx}")
                document.tokens[idx] = tokens
                document.save_tokens(idx)
                document.fonts.update(fonts)
        document.fonts = set(sorted(document.fonts))

    def tokenize_page(self, idx: int, page) -> Tuple[List[Token], Set[Font]]:
        fonts: Set[Font] = set()
        tokens: List[Token] = []
        for block in page.get_text("dict")["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    bbox = span["bbox"]
                    text = span["text"].strip()
                    font = self.extract_font(span)
                    if not text:
                        continue
                    token = Token(page=idx, text=text, bbox=bbox, font=font)
                    tokens.append(token)
                    fonts.add(font)
        tokens = merge_bboxes(tokens)
        return (tokens, fonts)

    def extract_font(self, span: Dict) -> Font:
        if "font" not in span:
            return ("", 0)
        return (span["font"], span["size"])
