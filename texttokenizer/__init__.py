"""texttokenizer

This script tokenizes a given pdf document into text tokens where each token is
a pair of text extracted from the document and the corresponding bounding box 
for the text.
"""

import click
import dacite

from dataclasses import dataclass
from pathlib import Path

from .annotator import PDFiumAnnotator, FitzAnnotator
from .document import Document
from .preprocessor import Preproccessor
from .processor import FitzProccessor


@dataclass(kw_only=True)
class Options:
    annotate: bool
    annotator: str
    fontdir: Path
    filename: Path
    pages: str


@click.option("--annotate", is_flag=True, help="save the annotated document.")
@click.option(
    "--annotator",
    type=click.Choice(["fitz", "pdfium"]),
    default="fitz",
    help="annotator implementation to use.",
)
@click.option("--fontdir", default="~/.local/share/fonts", help="path to fonts.")
@click.option("--pages", help="process specified pages (ranges or comma separated)")
@click.argument("filename")
@click.command()
def cli(**kwargs):
    config = dacite.Config(type_hooks={Path: lambda d: Path(d).expanduser().resolve()})
    options = dacite.from_dict(data_class=Options, data=kwargs, config=config)
    doc = dacite.from_dict(data_class=Document, data=options)
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
