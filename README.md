# texttokenizer

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

texttokenizer is a tool and library to tokenize PDF documents. A token is essentially a text segment from the document along with its bounding box and text origin. The text segment groups together logically related text in the natural reading order.

The primary use case for this library is to convert documents into tokens that are used for ML model training data (generating datasets and transforms for inference). The library should be able to handle any arbitrary PDF document (even scanned ones) with high accuracy.

## How it works

The library processes documents in several phases detailed further below. Briefly, documents are first preprocessed and optimized, then tokenized and optionally annotated for validation.

Each phase is implemented in modular fashion so it can be replaced with a better or alternate implementation in the future.

### Preprocessing

This phase handles normalizing the input source (image or pdf) into an optimized searchable pdf/a document using ocrmypdf (and pikepdf under the hood). As part of the optimization, the document is restructured linearly making it easier to tokenize as well as ensuring the fonts used are available.

This phase is also important to be able to process scanned PDF documents by converting them into searchable OCR'd documents using ocrmypdf (and tesseract) capabilities.

### Processing

This phase extracts tokens from the document. This uses PyMuPDF (fitz) as that library has the best bounding box detection for this application. The tokens (text, bounding box, origin, font) are extracted and can be exported in various formats (csv,json).

This phase also optionally extracts all the fonts in the document as intermediate files, if annotation is required. This is requires so that the annotation phase can use the font files to generate the annotated images.

### Annotation

This optional phase is useful for manually validating the detectect text segments and bounding boxes for accuracy. Each page of the document is exported as an image with the tokens drawn at the corresponding bounding box. This phase uses Pillow (PIL) for drawing the image.

Currently, two alternatives are implemented - FitzAnnotator (using PyMuPDF) and PDFiumAnnotator (using PyPDFium2). PDFiumAnnotator has better rendering overall with anti-aliasing and sub-pixel aliasing support but both are sufficient for manual validation purposes.

### Running tests and coverage report

```pytest```

with coverage

```coverage -m pytest```

coverage report

```coverage html -d testdata```

one liner

```cover run -m pytest && coverage html -d testdata```