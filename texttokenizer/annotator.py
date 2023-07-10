import pypdfium2 as pdfium
import fitz

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from loguru import logger as log
from typing import Dict, List, Set, Tuple

from .document import Document
from .token import Font
from .util import suffix_path


fitz.TOOLS.set_aa_level(4)


class Config:
    dpi: int = 300
    scale: float = 4.16666667  # (dpi * 1/72)
    genfiles_suffix: str = "png"
    text_color = (255, 0, 0)
    box_color = (255, 0, 0)
    stroke = 1


@dataclass(kw_only=True)
class Annotator(ABC):
    """Generates an token annotated image of each page of the document."""

    fontdir: Path
    fonts: Dict[str, ImageFont.ImageFont] = field(default_factory=dict)

    def __post_init__(self):
        self.fontdir = self.fontdir.expanduser().resolve()
        self.default_font = ImageFont.load_default()

    def get_font(self, font: Font) -> ImageFont.ImageFont:
        if font in self.fonts:
            return self.fonts[font]
        return self.default_font

    def write_tokens(self, img: Image.Image, tokens):
        draw = ImageDraw.Draw(img)
        for token in tokens:
            font = self.get_font(token.font)
            bbox = tuple(map(lambda x: x * Config.scale, token.bbox))
            draw.text(bbox, token.text, font=font, fill=Config.text_color)
            draw.rectangle(bbox, outline=Config.box_color, width=Config.stroke)

    def annotate(self, document: Document):
        page_images = self.get_page_images(document)
        for idx, img in page_images:
            self.write_tokens(img=img, tokens=document.tokens[idx])
            filename = suffix_path(document.filename, f"annotated-{idx}", ext=".png")
            img.save(filename)
            log.info(f"writing annotated {filename}")

    @abstractmethod
    def get_page_images(self, document: Document) -> List[Tuple[int, Image.Image]]:
        """Returns a list of tuples of page indices and corresponding PIL image."""


@dataclass(kw_only=True)
class PDFiumAnnotator(Annotator):
    """A pdfium (PyPdfium2) based annotator."""

    def build_fonts(self, fontset: Set[Font]):
        fonts = {}
        for name, size in fontset:
            fontpath = self.fontdir.joinpath(name).with_suffix(".ttf")
            try:
                font = ImageFont.truetype(str(fontpath), round(size * Config.scale))
                fonts[(name, size)] = font
            except OSError:
                log.error(f"font {name} not found at {fontpath}")
        self.fonts = fonts
        self.default_font = ImageFont.load_default()

    def get_page_images(self, document: Document):
        doc = pdfium.PdfDocument(document.preprocessed)
        pages = document.page_indices
        renderer = doc.render(
            pdfium.PdfBitmap.to_pil, page_indices=pages, scale=Config.scale
        )
        return zip(pages, renderer)


@dataclass(kw_only=True)
class FitzAnnotator(Annotator):
    """A fitz (PyMuPdf) based annotator."""

    def get_page_images(self, document: Document):
        page_images = []
        with fitz.open(document.preprocessed) as doc:
            pages = document.page_indices
            for idx in pages:
                pix = doc[idx].get_pixmap(dpi=Config.dpi)
                pix.gamma_with(1.01)
                buff = pix.pil_tobytes("png")
                img = Image.open(BytesIO(buff))
                page_images.append((idx, img))
        return page_images