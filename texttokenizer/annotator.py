from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import fitz
import pypdfium2 as pdfium
from loguru import logger as log
from PIL import Image, ImageDraw
from PIL.ImageFont import FreeTypeFont, ImageFont, truetype

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

    annotate_bbox: bool
    annotate_text: bool
    annotate_token: bool
    annotator_font: Path
    fonts_dir: Path

    fonts: dict[str, Path] = field(default_factory=dict)
    default_font: ImageFont | None

    def __post_init__(self):
        self.default_font = truetype(str(self.annotator_font), size=22)

    def load_fonts(self, fonts_dir: Path):
        fonts = {}
        for f in fonts_dir.iterdir():
            if f.is_file():
                fonts[f.with_suffix("").name] = f
        self.fonts = fonts
        log.info(f"page fonts {self.fonts}")

    def get_font(self, font: Font) -> ImageFont:
        name, size = font
        size = size * Config.scale
        if name in self.fonts:
            return FreeTypeFont(font=str(self.fonts[name]), size=size)
        log.warning(f"font {font[0]} not found in loaded page fonts.")
        return self.default_font

    def write_tokens(self, img: Image.Image, tokens):
        draw = ImageDraw.Draw(img)
        for i, token in enumerate(tokens):
            font = self.get_font(token.font)
            bbox = tuple(map(lambda x: x * Config.scale, token.bbox))
            origin = tuple(map(lambda x: x * Config.scale, token.origin))
            if self.annotate_token:
                draw.text(
                    origin,
                    str(i),
                    font=self.default_font,
                    fill=Config.text_color,
                    anchor="ls",
                )
            if self.annotate_text:
                draw.text(
                    origin, token.text, font=font, fill=Config.text_color, anchor="ls"
                )
            if self.annotate_bbox:
                draw.rectangle(bbox, outline=Config.box_color, width=Config.stroke)

    def annotate(self, document: Document):
        log.info(f"annotating - {document.filename}")
        if not (self.annotate_bbox or self.annotate_text or self.annotate_token):
            log.warning("annotation requested but nothing to annotate")
            return
        page_images = self.get_page_images(document)
        for idx, img in page_images:
            page_tokens = [t for t in document.tokens if t.page == idx]
            self.load_fonts(self.fonts_dir.joinpath(str(idx)))
            self.write_tokens(img=img, tokens=page_tokens)
            filename = suffix_path(document.filename, f"annotated-{idx}", ext=".png")
            img.save(filename)
            log.info(f"writing annotated {filename}")

    @abstractmethod
    def get_page_images(self, document: Document) -> list[tuple[int, Image.Image]]:
        """Returns a list of tuples of page indices and corresponding PIL image."""


@dataclass(kw_only=True)
class PDFiumAnnotator(Annotator):
    """A pdfium (PyPdfium2) based annotator."""

    def get_page_images(self, document: Document):
        doc = pdfium.PdfDocument(document.filename)
        renderer = doc.render(
            pdfium.PdfBitmap.to_pil,
            page_indices=document.page_indices,
            scale=Config.scale,
        )
        return zip(document.page_indices, renderer)


@dataclass(kw_only=True)
class FitzAnnotator(Annotator):
    """A fitz (PyMuPdf) based annotator."""

    def get_page_images(self, document: Document):
        page_images = []
        for idx in document.page_indices:
            pix = document.pdf_doc[idx].get_pixmap(dpi=Config.dpi)
            pix.gamma_with(1.01)
            buff = pix.pil_tobytes("png")
            img = Image.open(BytesIO(buff))
            page_images.append((idx, img))
        return page_images
