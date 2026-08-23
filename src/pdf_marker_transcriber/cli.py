from dataclasses import dataclass
from pathlib import Path

import hydra
from hydra.core.config_store import ConfigStore

from .utils import FilePathResolver
from .pdf_file_extractor import PDFArticleExtractor


@dataclass
class Config:
    file: str | None = None
    suffix: str = "-rec"
    replace: bool = False
    entry_point: str = "single"


class EntryPoint:
    def __init__(self, extractor: PDFArticleExtractor) -> None:
        self.extractor = extractor

    def __call__(self, name: str, path: Path) -> None:
        match name:
            case "single":
                self.extractor.extract(path)

            case "folder":
                for pdf_path in sorted(path.glob("*.pdf")):
                    self.extractor.extract(pdf_path)

            case "subfolders":
                subfolders = sorted(
                    path for path in path.iterdir()
                    if path.is_dir()
                )

                for subfolder in subfolders:
                    for pdf_path in sorted(subfolder.glob("*.pdf")):
                        self.extractor.extract(pdf_path)

            case _:
                raise ValueError(f"Unknown entry point: {name}")


ConfigStore.instance().store(name="config", node=Config)


@hydra.main(version_base="1.3", config_name="config")
def main(cfg: Config) -> None:
    extractor = PDFArticleExtractor(
        suffix=cfg.suffix,
        replace=cfg.replace,
    )

    entry_point = EntryPoint(extractor)

    match cfg.entry_point:
        case "single":
            path = FilePathResolver.resolve_file(cfg.file)

        case "folder" | "subfolders":
            path = FilePathResolver.resolve_directory(cfg.file)

        case _:
            raise ValueError(f"Unknown entry point: {cfg.entry_point}")

    entry_point(cfg.entry_point, path)


if __name__ == "__main__":
    main()