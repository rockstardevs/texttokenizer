from pathlib import Path

import ocrmypdf
from loguru import logger as log


class Preprocessor:
    """
    Implements a OMP (OcrMyPDF) based preprocessor.
    """

    def optimize(self, src: Path, dest: Path, format="pdfa"):
        """pre-processes the given document to optimize it."""
        log.info(f"preprocessing - {src}")
        args = {
            "input_file": src,
            "output_file": dest,
            "output_type": format,
            "skip_text": True,
            "clean": True,
            "optimize": 3,
        }
        ocrmypdf.ocr(**args)
        log.info(f"writing preprocessed - {dest}")
