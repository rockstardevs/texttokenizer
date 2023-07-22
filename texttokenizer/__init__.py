"""texttokenizer

This script tokenizes a given pdf document into text tokens where each token is
a pair of text extracted from the document and the corresponding bounding box 
for the text.
"""

import click
import dacite

from dataclasses import dataclass, asdict
from loguru import logger as log
from pathlib import Path
from tempfile import mkdtemp
from typing import Optional

from .annotator import PDFiumAnnotator, FitzAnnotator
from .document import Document
from .preprocessor import Preproccessor
from .processor import FitzProccessor
from .util import suffix_path


@dataclass(kw_only=True)
class Options:
    annotate: bool
    annotate_bbox: bool
    annotate_text: bool
    annotate_token: bool
    annotator: str
    annotator_font: Path
    preprocessor_use_pdfa: bool
    filename: Path
    pages: Optional[str]
    merge_bboxes: bool
    token_format: str
    tmproot: Path


@click.option("--annotate", is_flag=True, help="save the annotated document.")
@click.option("--annotate_bbox", default=True, help="annotate token bbox.")
@click.option("--annotate_text", default=False, help="annotate token text.")
@click.option("--annotate_token", default=True, help="annotate token index.")
@click.option(
    "--annotator",
    type=click.Choice(["fitz", "pdfium"]),
    default="fitz",
    help="annotator implementation to use.",
)
@click.option(
    "--annotator_font",
    default="~/.local/share/fonts/Verdana.ttf",
    help="path to font for annotation.",
)
@click.option("--merge_bboxes", is_flag=True, help="flag to merge overlapping bboxes.")
@click.option("--pages", help="process specified pages (ranges or comma separated)")
@click.option(
    "--token_format",
    type=click.Choice(["csv", "templatizer"]),
    default="templatizer",
    help="output format for tokens.",
)
@click.option(
    "--preprocessor_use_pdfa",
    is_flag=True,
    help="use pdf/a format conversion in preprocessor.",
)
@click.option("--tmproot", default="./tmp", help="root directory for temp files.")
@click.argument("filename")
@click.command()
def cli(**kwargs):
    config = dacite.Config(type_hooks={Path: lambda d: Path(d).expanduser().resolve()})
    options = dacite.from_dict(data_class=Options, data=kwargs, config=config)
    options.tmproot.mkdir(parents=True, exist_ok=True)

    doc = dacite.from_dict(data_class=Document, data=asdict(options))
    preprocessor = Preproccessor()
    processor = FitzProccessor()

    fonts_dir = None
    if options.annotate:
        tempdir = Path(
            mkdtemp(prefix=f"{doc.filename.with_suffix('').name}-", dir=options.tmproot)
        )
        log.info(f"using tempdir {tempdir}")
        fonts_dir = tempdir.joinpath("fonts")
        annotatorCls = (
            PDFiumAnnotator if options.annotator == "pdfium" else FitzAnnotator
        )
        annotator = dacite.from_dict(
            data_class=annotatorCls,
            data={"fonts_dir": fonts_dir, **kwargs},
            config=config,
        )

    format = "pdfa" if options.preprocessor_use_pdfa else "pdf"
    preprocessed = suffix_path(doc.filename, "preprocessed")
    preprocessor.optimize(doc.filename, preprocessed, format)
    doc.update_pdf_doc(preprocessed)

    processor.tokenize(doc, fonts_dir=fonts_dir, merge_bboxes=options.merge_bboxes)

    if options.token_format == "templatizer":
        filename = suffix_path(doc.filename, f"tokens", ext=".json")
        doc.save_templatizer_tokens(filename)
    else:
        filename = suffix_path(doc.filename, f"tokens", ext=".csv")
        doc.save_csv_tokens(filename)

    if options.annotate:
        annotator.annotate(doc)
