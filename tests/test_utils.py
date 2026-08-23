from pathlib import Path

import pytest

from pdf_marker_transcriber.utils import FilePathResolver, markdown_sanitizer


class TestMarkdownSanitizer:
    @pytest.fixture
    def valid_markdown(self) -> str:
        return (
            "# Heading\n\n"
            "A **bold** statement with `inline_code`.\n\n"
            "- first item\n"
            "- second item\n"
        )

    @pytest.mark.parametrize(
        ("markdown", "expected"),
        [
            pytest.param("‘quoted’", "'quoted'", id="single-quotes"),
            pytest.param("“quoted”", '"quoted"', id="double-quotes"),
            pytest.param(
                "page 10–12 — notes",
                "page 10-12 - notes",
                id="dashes",
            ),
            pytest.param(
                "â€œquotedâ€\x9d â€“ notes",
                '"quoted" - notes',
                id="mojibake",
            ),
        ],
    )
    def test_normalizes_supported_punctuation(
        self,
        markdown: str,
        expected: str,
    ) -> None:
        assert markdown_sanitizer(markdown) == expected

    def test_preserves_valid_markdown(self, valid_markdown: str) -> None:
        assert markdown_sanitizer(valid_markdown) == valid_markdown


class TestFilePathResolver:
    @pytest.fixture
    def paths(self, tmp_path: Path) -> dict[str, Path]:
        file_path = tmp_path / "article.pdf"
        file_path.write_text("content", encoding="utf-8")

        directory_path = tmp_path / "articles"
        directory_path.mkdir()

        return {
            "file": file_path,
            "directory": directory_path,
        }

    def test_resolves_explicit_path(self, paths: dict[str, Path]) -> None:
        file_path = paths["file"]

        assert FilePathResolver.resolve(f"  {file_path}  ") == file_path

    def test_resolves_path_from_clipboard(
        self,
        paths: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        file_path = paths["file"]
        monkeypatch.setattr(
            "pdf_marker_transcriber.utils.pyperclip.paste",
            lambda: str(file_path),
        )

        assert FilePathResolver.resolve(None) == file_path

    def test_rejects_missing_path(self, tmp_path: Path) -> None:
        missing_path = tmp_path / "missing.pdf"

        with pytest.raises(FileNotFoundError, match="Path not found"):
            FilePathResolver.resolve(str(missing_path))

    @pytest.mark.parametrize(
        ("method_name", "path_kind"),
        [
            pytest.param("resolve_file", "file", id="file"),
            pytest.param("resolve_directory", "directory", id="directory"),
        ],
    )
    def test_resolves_expected_path_type(
        self,
        paths: dict[str, Path],
        method_name: str,
        path_kind: str,
    ) -> None:
        resolver = getattr(FilePathResolver, method_name)
        expected_path = paths[path_kind]

        assert resolver(str(expected_path)) == expected_path

    @pytest.mark.parametrize(
        ("method_name", "path_kind", "expected_error"),
        [
            pytest.param(
                "resolve_file",
                "directory",
                IsADirectoryError,
                id="directory-as-file",
            ),
            pytest.param(
                "resolve_directory",
                "file",
                NotADirectoryError,
                id="file-as-directory",
            ),
        ],
    )
    def test_rejects_unexpected_path_type(
        self,
        paths: dict[str, Path],
        method_name: str,
        path_kind: str,
        expected_error: type[OSError],
    ) -> None:
        resolver = getattr(FilePathResolver, method_name)

        with pytest.raises(expected_error):
            resolver(str(paths[path_kind]))
