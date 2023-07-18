"""texttokenizer

This script tokenizes a given pdf document into text tokens where each token is
a pair of text extracted from the document and the corresponding bounding box 
for the text.
"""

import click
import dacite

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from .annotator import PDFiumAnnotator, FitzAnnotator
from .document import Document
from .preprocessor import Preproccessor
from .processor import FitzProccessor


@dataclass(kw_only=True)
class Options:
    annotate: bool
    annotate_bbox: bool
    annotate_text: bool
    annotate_token: bool
    annotator: str
    annotator_font: Path
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

    preprocessor.optimize(doc.filename, doc.preprocessed)
    processor.tokenize(doc)

    if options.annotate:
        annotatorCls = (
            PDFiumAnnotator if options.annotator == "pdfium" else FitzAnnotator
        )
        annotator = dacite.from_dict(
            data_class=annotatorCls, data=kwargs, config=config
        )
        annotator.annotate(doc)
