import fitz

from abc import ABC, abstractmethod
from loguru import logger as log
from pathlib import Path
from typing import List, Dict, Set, Tuple

from .document import Document
from .token import Token, Font
from .util import expand_page_list, merge_bboxes, flag_composer


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

    def extract_page_fonts(
        self, doc: fitz.Document, idx: int, fonts: Set[str], dir: Path
    ):
        filepath = dir.joinpath(str(idx))
        filepath.mkdir(parents=True, exist_ok=True)
        for font in doc.get_page_fonts(idx):
            log.info(f"extracting page font: {font}")
            xref, ext, _, name, _, enc = font
            if "+" in name:
                name = name.split("+")[-1]
            font_obj, flags = None, 0
            if ext == "n/a":
                font_obj = fitz.Font(fontname=name)
            else:
                font_data = doc.extract_font(xref, named=True)
                font_obj = fitz.Font(fontbuffer=font_data["content"])
                flags = flag_composer(font_obj.flags)
            name = f"{name}-{flags}"
            if name in fonts:
                filename = filepath.joinpath(name).with_suffix(f".{font_data['ext']}")
                with open(filename, "wb") as f:
                    f.write(font_obj.buffer)
                log.info(f"writing font {filename} {enc}")

    def tokenize(self, document: Document):
        log.info(f"processing - {document.preprocessed}")
        with fitz.open(document.preprocessed) as doc:
            pages = expand_page_list(document.pages, len(doc) - 1)
            if pages:
                document.page_indices = pages
            for idx in range(len(doc)):
                if pages and idx not in pages:
                    continue
                tokens, fonts = self.tokenize_page(idx, doc[idx], document.merge_bboxes)
                log.info(f"extracted {len(tokens)} tokens from page {idx}")
                log.info(f"fonts used: {fonts}")
                document.tokens.extend(tokens)
                if document.annotate:
                    self.extract_page_fonts(doc, idx, fonts, document.fontdir)
        document.fonts = set(sorted(document.fonts))

    def tokenize_page(
        self, idx: int, page: fitz.Page, merge: bool
    ) -> Tuple[List[Token], Set[str]]:
        fonts: Set[str] = set()
        tokens: List[Token] = []
        for block in page.get_text("dict")["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    args = {
                        "page": idx,
                        "bbox": span["bbox"],
                        "origin": span["origin"],
                        "text": span["text"].strip(),
                    }
                    if not args["text"]:
                        continue
                    args["font"] = self.extract_font(span)
                    token = Token(**args)
                    tokens.append(token)
                    fonts.add(args["font"][0])
        if merge:
            tokens = merge_bboxes(tokens)
        return (tokens, fonts)

    def extract_font(self, span: Dict) -> Font:
        if "font" not in span:
            log.warning(f"no font info for span {span['text']}")
            return ("", 0)
        font_name = f"{span['font']}-{span['flags']}"
        return (font_name, span["size"])
