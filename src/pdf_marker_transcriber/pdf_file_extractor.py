from pathlib import Path



from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.renderers.json import JSONRenderer
from marker.renderers.markdown import MarkdownRenderer


from .utils import markdown_sanitizer


class PDFArticleExtractor:
    def __init__(self, suffix: str, replace: bool) -> None:
        self.suffix = suffix
        self.replace = replace

        self.converter = PdfConverter(
            artifact_dict=create_model_dict(),
            config={
                "mode": "fast",
                "disable_ocr": True,
                "disable_tqdm": False,
            },
        )

    def _watch_paths(self, pdf_path: Path) -> tuple[Path, Path, Path]:
        output_dir = pdf_path.parent / f"{pdf_path.stem}_artifacts"

        markdown_path = output_dir / f"{pdf_path.stem}{self.suffix}.md"
        json_path = output_dir / f"{pdf_path.stem}{self.suffix}.json"

        if not self.replace:
            for path in (markdown_path, json_path):
                if path.exists():
                    raise FileExistsError(
                        f"Output file already exists: {path}"
                    )

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OSError(
                f"Could not create output directory: {output_dir}"
            ) from exc

        return output_dir, markdown_path, json_path

    def extract(self, pdf_path: Path) -> Path:
        output_dir, markdown_path, json_path = self._watch_paths(pdf_path)
        document = self.converter.build_document(str(pdf_path))

        markdown_renderer = self.converter.resolve_dependencies(
            MarkdownRenderer
        )
        markdown_rendered = markdown_renderer(document)
        markdown, _, images = text_from_rendered(markdown_rendered)
        markdown_path.write_text(
            markdown_sanitizer(markdown),
            encoding="utf-8",
        )

        for image_name, image in images.items():
            image.save(output_dir / image_name)

        json_renderer = self.converter.resolve_dependencies(
            JSONRenderer
        )
        json_rendered = json_renderer(document)
        json_text, _, _ = text_from_rendered(json_rendered)
        json_path.write_text(
            json_text,
            encoding="utf-8",
        )

        return markdown_path
