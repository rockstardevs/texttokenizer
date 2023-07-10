import ocrmypdf

from loguru import logger as log
from pathlib import Path


class Preproccessor:
    """
    Implements a OMP (OcrMyPDF) based preprocessor.
    """

    def optimize(self, src: Path, dest: Path):
        """pre-processes the given document to optimize it."""
        args = {
            "input_file": src,
            "output_file": dest,
            "skip_text": True,
            "clean": True,
            "optimize": 3,
        }
        ocrmypdf.ocr(**args)
        log.info(f"writing preprocessed - {dest}")
