import pyperclip
from pathlib import Path


_TRANSLATION = str.maketrans(
    {
        # Apostrophes / single quotes
        "‘": "'",
        "’": "'",
        "‚": "'",
        "‛": "'",
        "‹": "'",
        "›": "'",
        "ʼ": "'",
        "ʻ": "'",
        "＇": "'",

        # Double quotes
        "“": '"',
        "”": '"',
        "„": '"',
        "‟": '"',
        "«": '"',
        "»": '"',
        "〝": '"',
        "〞": '"',
        "〟": '"',
        "「": '"',
        "」": '"',
        "『": '"',
        "』": '"',
        "＂": '"',

        # Hyphens / dashes / minus signs
        "‐": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
        "―": "-",
        "−": "-",
        "﹘": "-",
        "﹣": "-",
        "－": "-",
    }
)

_REPLACEMENTS = (
    ("4â€“", "-"),
    ("â€“", "-"),
    ("â€”", "-"),
    ("â€˜", "'"),
    ("â€™", "'"),
    ("â€œ", '"'),
    ("â€\x9d", '"'),
)

def markdown_sanitizer(markdown: str) -> str:
    for source, target in _REPLACEMENTS:
        markdown = markdown.replace(source, target)

    return markdown.translate(_TRANSLATION)



class FilePathResolver:
    @staticmethod
    def resolve(file: str | None) -> Path:
        source = file if file is not None else pyperclip.paste()
        path = Path(source.strip())

        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        return path

    @staticmethod
    def resolve_file(file: str | None) -> Path:
        path = FilePathResolver.resolve(file)

        if path.is_dir():
            raise IsADirectoryError(
                f"Expected a PDF file, got directory: {path}"
            )

        return path

    @staticmethod
    def resolve_directory(file: str | None) -> Path:
        path = FilePathResolver.resolve(file)

        if not path.is_dir():
            raise NotADirectoryError(
                f"Expected a directory, got file: {path}"
            )

        return path
