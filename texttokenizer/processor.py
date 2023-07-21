import fitz

from abc import ABC, abstractmethod
from loguru import logger as log
from pathlib import Path
from typing import List, Dict, Set, Tuple

from .document import Document
from .token import Token, Font
from .util import flag_composer, merge_bboxes


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

    def tokenize(self, document: Document, fonts_dir: Path | None = None):
        log.info(f"processing - {document.filename}")
        for idx in document.page_indices:
            tokens, fonts = self.tokenize_page(
                idx, document.pdf_doc[idx], document.merge_bboxes
            )
            log.info(f"extracted {len(tokens)} tokens from page {idx}")
            log.info(f"fonts used: {fonts}")
            document.tokens.extend(tokens)
            if fonts_dir is not None:
                self.extract_page_fonts(document.pdf_doc, idx, fonts, fonts_dir)
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
