# pdf-marker-transcriber

`pdf-marker-transcriber` is a small command-line tool for converting PDFs to Markdown using [Marker](https://github.com/datalab-to/marker).

It can process a single PDF, all PDFs in a directory, or PDFs contained in first-level subdirectories (this is because I organize my paper library with one directory each reference).

For each document, it creates an output directory with:

* the generated Markdown;
* Marker's structural JSON;
* extracted images.

The Markdown is only lightly sanitized, mainly to normalize a few punctuation characters without modifying the document structure more than necessary.

Input paths can be passed directly or read from the clipboard. Existing outputs are preserved by default to avoid overwriting previous conversions.

The main use case is batch-converting collections of papers or technical documents into a format that can later be searched, versioned, indexed, or processed by other tools.



## Installation

```bash
python -m venv pdf_extraction
source pdf_extraction/bin/activate
pip install -e .
```

## Usage

Single PDF (the default `single` entry point):

```bash
pdf-marker-transcriber entry_point=single file=/path/to/article.pdf
```

If `file` is not provided, the path is read from the clipboard:

```bash
pdf-marker-transcriber
```

All PDFs located directly inside a folder:

```bash
pdf-marker-transcriber entry_point=folder file=/path/to/folder
```

PDFs located in each immediate subfolder of a root directory:

```bash
pdf-marker-transcriber entry_point=subfolders file=/path/to/root
```

Allow existing files to be overwritten:

```bash
pdf-marker-transcriber file=/path/to/article.pdf replace=true
```

Change the output suffix:

```bash
pdf-marker-transcriber file=/path/to/article.pdf suffix=-rec
```

## Output

Given:

```text
/data/paper.pdf
```

the following files are generated:

```text
/data/paper_artifacts/
├── paper-rec.md
├── paper-rec.json
└── <images extracted by Marker>
```

## TODO:
- [ ] add skip option when folder o subfolders are being processed to avoid stopping full folder extraction if there is some PDF files that hasn't be proceesed yet.