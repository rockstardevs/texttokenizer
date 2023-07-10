"""texttokenizer

This script tokenizes a given pdf document into text tokens where each token is
a pair of text extracted from the document and the corresponding bounding box 
for the text.
"""

import click
import dacite

from dataclasses import dataclass, field
from pathlib import Path

from .annotator import PDFiumAnnotator, FitzAnnotator
from .document import Document
from .preprocessor import Preproccessor
from .processor import FitzProccessor


@click.option("--annotate", is_flag=True, help="save the annotated document.")
@click.option("--pages", help="process specified pages (ranges or comma separated)")
@click.option("--fontdir", default="~/.local/share/fonts", help="path to fonts.")
@click.argument("filename")
@click.command()
def cli(**kwargs):
    config = dacite.Config(type_hooks={Path: lambda d: Path(d).expanduser().resolve()})
    doc = dacite.from_dict(data_class=Document, data=kwargs, config=config)
    preprocessor = Preproccessor()
    preprocessor.optimize(doc.filename, doc.preprocessed)
    processor = FitzProccessor()
    processor.tokenize(doc)
    annotator = dacite.from_dict(data_class=FitzAnnotator, data=kwargs, config=config)
    annotator.annotate(doc)
