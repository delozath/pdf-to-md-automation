from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

import pdf_marker_transcriber.pdf_file_extractor as extractor_module
from pdf_marker_transcriber.pdf_file_extractor import PDFArticleExtractor


class TestPDFArticleExtractor:
    @pytest.fixture
    def mocked_marker(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> SimpleNamespace:
        model_dict = {"model": "fake"}
        create_model_dict = MagicMock(return_value=model_dict)
        converter = MagicMock()
        converter_factory = MagicMock(return_value=converter)

        monkeypatch.setattr(
            extractor_module,
            "create_model_dict",
            create_model_dict,
        )
        monkeypatch.setattr(
            extractor_module,
            "PdfConverter",
            converter_factory,
        )

        return SimpleNamespace(
            model_dict=model_dict,
            create_model_dict=create_model_dict,
            converter=converter,
            converter_factory=converter_factory,
        )

    @pytest.fixture
    def extractor(self, mocked_marker: SimpleNamespace) -> PDFArticleExtractor:
        return PDFArticleExtractor(suffix="-rec", replace=False)

    @pytest.fixture
    def pdf_path(self, tmp_path: Path) -> Path:
        path = tmp_path / "article.pdf"
        path.touch()
        return path

    def test_configures_pdf_converter(
        self,
        extractor: PDFArticleExtractor,
        mocked_marker: SimpleNamespace,
    ) -> None:
        mocked_marker.create_model_dict.assert_called_once_with()
        mocked_marker.converter_factory.assert_called_once_with(
            artifact_dict=mocked_marker.model_dict,
            config={
                "mode": "fast",
                "disable_ocr": True,
                "disable_tqdm": False,
            },
        )
        assert extractor.converter is mocked_marker.converter

    def test_creates_expected_output_paths(
        self,
        extractor: PDFArticleExtractor,
        pdf_path: Path,
    ) -> None:
        output_dir, markdown_path, json_path = extractor._watch_paths(pdf_path)

        assert output_dir == pdf_path.parent / "article_artifacts"
        assert markdown_path == output_dir / "article-rec.md"
        assert json_path == output_dir / "article-rec.json"
        assert output_dir.is_dir()

    @pytest.mark.parametrize(
        "existing_name",
        [
            pytest.param("article-rec.md", id="markdown"),
            pytest.param("article-rec.json", id="json"),
        ],
    )
    def test_rejects_existing_output(
        self,
        extractor: PDFArticleExtractor,
        pdf_path: Path,
        existing_name: str,
    ) -> None:
        output_dir = pdf_path.parent / "article_artifacts"
        output_dir.mkdir()
        (output_dir / existing_name).touch()

        with pytest.raises(FileExistsError, match="Output file already exists"):
            extractor._watch_paths(pdf_path)

    def test_allows_existing_outputs_when_replace_is_enabled(
        self,
        mocked_marker: SimpleNamespace,
        pdf_path: Path,
    ) -> None:
        extractor = PDFArticleExtractor(suffix="-rec", replace=True)
        output_dir = pdf_path.parent / "article_artifacts"
        output_dir.mkdir()
        markdown_path = output_dir / "article-rec.md"
        json_path = output_dir / "article-rec.json"
        markdown_path.touch()
        json_path.touch()

        assert extractor._watch_paths(pdf_path) == (
            output_dir,
            markdown_path,
            json_path,
        )

    def test_reports_output_directory_creation_error(
        self,
        extractor: PDFArticleExtractor,
        pdf_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            Path,
            "mkdir",
            MagicMock(side_effect=OSError("permission denied")),
        )

        with pytest.raises(OSError, match="Could not create output directory"):
            extractor._watch_paths(pdf_path)

    def test_extracts_markdown_json_and_images(
        self,
        extractor: PDFArticleExtractor,
        mocked_marker: SimpleNamespace,
        pdf_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        document = object()
        markdown_rendered = object()
        json_rendered = object()
        markdown_renderer = MagicMock(return_value=markdown_rendered)
        json_renderer = MagicMock(return_value=json_rendered)
        image = MagicMock()
        text_from_rendered = MagicMock(
            side_effect=[
                ("raw markdown", {}, {"figure.png": image}),
                ('{"type": "document"}', {}, {}),
            ]
        )
        sanitizer = MagicMock(return_value="sanitized markdown")

        mocked_marker.converter.build_document.return_value = document
        mocked_marker.converter.resolve_dependencies.side_effect = (
            lambda renderer: {
                extractor_module.MarkdownRenderer: markdown_renderer,
                extractor_module.JSONRenderer: json_renderer,
            }[renderer]
        )
        monkeypatch.setattr(
            extractor_module,
            "text_from_rendered",
            text_from_rendered,
        )
        monkeypatch.setattr(
            extractor_module,
            "markdown_sanitizer",
            sanitizer,
        )

        result = extractor.extract(pdf_path)

        output_dir = pdf_path.parent / "article_artifacts"
        markdown_path = output_dir / "article-rec.md"
        json_path = output_dir / "article-rec.json"

        assert result == markdown_path
        assert markdown_path.read_text(encoding="utf-8") == "sanitized markdown"
        assert json_path.read_text(encoding="utf-8") == '{"type": "document"}'
        mocked_marker.converter.build_document.assert_called_once_with(
            str(pdf_path)
        )
        mocked_marker.converter.resolve_dependencies.assert_has_calls(
            [
                call(extractor_module.MarkdownRenderer),
                call(extractor_module.JSONRenderer),
            ]
        )
        markdown_renderer.assert_called_once_with(document)
        json_renderer.assert_called_once_with(document)
        text_from_rendered.assert_has_calls(
            [call(markdown_rendered), call(json_rendered)]
        )
        sanitizer.assert_called_once_with("raw markdown")
        image.save.assert_called_once_with(output_dir / "figure.png")
