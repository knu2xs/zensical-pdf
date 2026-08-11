from pathlib import Path

import pytest

from zensical_pdf import AssetError
from zensical_pdf.assets import AssetCopy, copy_asset, find_local_images, rewrite_image_paths


# ---------------------------------------------------------------------------
# find_local_images
# ---------------------------------------------------------------------------


def test_find_local_images_markdown_basic() -> None:
    content = "![Alt text](images/logo.png)"
    assert find_local_images(content) == ["images/logo.png"]


def test_find_local_images_markdown_with_title() -> None:
    content = '![Alt](images/logo.png "My Logo")'
    refs = find_local_images(content)
    assert "images/logo.png" in refs


def test_find_local_images_html_double_quote() -> None:
    content = '<img src="images/logo.png" alt="logo">'
    assert find_local_images(content) == ["images/logo.png"]


def test_find_local_images_html_single_quote() -> None:
    content = "<img src='images/logo.png'>"
    assert find_local_images(content) == ["images/logo.png"]


def test_find_local_images_skips_http_urls() -> None:
    content = "![Logo](https://example.com/logo.png)"
    assert find_local_images(content) == []


def test_find_local_images_skips_http_in_html() -> None:
    content = '<img src="http://example.com/logo.png">'
    assert find_local_images(content) == []


def test_find_local_images_multiple() -> None:
    content = "![A](a.png)\n\n![B](b.png)\n\n<img src=\"c.png\">"
    refs = find_local_images(content)
    assert "a.png" in refs
    assert "b.png" in refs
    assert "c.png" in refs


def test_find_local_images_no_images_returns_empty() -> None:
    assert find_local_images("Just text.") == []


# ---------------------------------------------------------------------------
# copy_asset
# ---------------------------------------------------------------------------


def test_copy_asset_copies_file(tmp_path: Path) -> None:
    src = tmp_path / "src" / "logo.png"
    src.parent.mkdir()
    src.write_bytes(b"\x89PNG")
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    dest = copy_asset(src, assets_dir)
    assert dest.exists()
    assert dest.read_bytes() == b"\x89PNG"


def test_copy_asset_uses_hash_prefix_on_collision(tmp_path: Path) -> None:
    src1 = tmp_path / "src1" / "logo.png"
    src2 = tmp_path / "src2" / "logo.png"
    src1.parent.mkdir()
    src2.parent.mkdir()
    src1.write_bytes(b"file1")
    src2.write_bytes(b"file2")
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    dest1 = copy_asset(src1, assets_dir)
    dest2 = copy_asset(src2, assets_dir)
    assert dest1.name == "logo.png"
    assert dest2.name != "logo.png"
    assert dest2.name.endswith("_logo.png")


# ---------------------------------------------------------------------------
# rewrite_image_paths
# ---------------------------------------------------------------------------


def _png(p: Path) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\x89PNG")
    return p


def test_rewrite_copies_local_image(tmp_path: Path) -> None:
    img = _png(tmp_path / "docs" / "assets" / "logo.png")
    source_file = tmp_path / "docs" / "page.md"
    source_file.touch()
    assets_dir = tmp_path / "build" / "assets"
    assets_dir.mkdir(parents=True)

    content = "![Logo](assets/logo.png)"
    new_content, copies = rewrite_image_paths(content, source_file, assets_dir, "warn", [])
    assert (assets_dir / "logo.png").exists()
    assert len(copies) == 1


def test_rewrite_replaces_markdown_image_path(tmp_path: Path) -> None:
    _png(tmp_path / "docs" / "img.png")
    src = tmp_path / "docs" / "page.md"
    src.touch()
    assets_dir = tmp_path / "build" / "assets"
    assets_dir.mkdir(parents=True)

    content = "![Alt](img.png)"
    new_content, _ = rewrite_image_paths(content, src, assets_dir, "warn", [])
    assert "assets/img.png" in new_content
    assert "![Alt](img.png)" not in new_content


def test_rewrite_replaces_html_image_path(tmp_path: Path) -> None:
    _png(tmp_path / "docs" / "img.png")
    src = tmp_path / "docs" / "page.md"
    src.touch()
    assets_dir = tmp_path / "build" / "assets"
    assets_dir.mkdir(parents=True)

    content = '<img src="img.png" alt="x">'
    new_content, _ = rewrite_image_paths(content, src, assets_dir, "warn", [])
    assert 'src="assets/img.png"' in new_content


def test_rewrite_leaves_external_url_unchanged(tmp_path: Path) -> None:
    src = tmp_path / "docs" / "page.md"
    src.parent.mkdir(parents=True)
    src.touch()
    assets_dir = tmp_path / "build" / "assets"
    assets_dir.mkdir(parents=True)

    content = "![Logo](https://example.com/logo.png)"
    new_content, copies = rewrite_image_paths(content, src, assets_dir, "warn", [])
    assert new_content == content
    assert copies == []


def test_rewrite_missing_asset_warn_emits_warning(tmp_path: Path) -> None:
    src = tmp_path / "docs" / "page.md"
    src.parent.mkdir(parents=True)
    src.touch()
    assets_dir = tmp_path / "build" / "assets"
    assets_dir.mkdir(parents=True)

    warnings: list[str] = []
    content = "![Missing](ghost.png)"
    new_content, copies = rewrite_image_paths(content, src, assets_dir, "warn", warnings)
    assert any("ghost.png" in w for w in warnings)
    assert copies == []
    assert new_content == content  # reference left unchanged


def test_rewrite_missing_asset_error_raises(tmp_path: Path) -> None:
    src = tmp_path / "docs" / "page.md"
    src.parent.mkdir(parents=True)
    src.touch()
    assets_dir = tmp_path / "build" / "assets"
    assets_dir.mkdir(parents=True)

    content = "![Missing](ghost.png)"
    with pytest.raises(AssetError, match="ghost.png"):
        rewrite_image_paths(content, src, assets_dir, "error", [])


def test_rewrite_records_asset_copy_fields(tmp_path: Path) -> None:
    img = _png(tmp_path / "docs" / "logo.png")
    src = tmp_path / "docs" / "page.md"
    src.touch()
    assets_dir = tmp_path / "build" / "assets"
    assets_dir.mkdir(parents=True)

    content = "![L](logo.png)"
    _, copies = rewrite_image_paths(content, src, assets_dir, "warn", [])
    assert len(copies) == 1
    c = copies[0]
    assert c.source_path == img
    assert c.original_reference == "logo.png"
    assert c.rewritten_reference == "assets/logo.png"
    assert c.dest_path.name == "logo.png"
