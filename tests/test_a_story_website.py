from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = ROOT / "website" / "a-story-of-two"


def test_a_story_website_represents_all_content_formats() -> None:
    html_path = SITE_ROOT / "index.html"
    assert html_path.exists()

    html = html_path.read_text(encoding="utf-8")
    for text in (
        "Reels that travel",
        "Carousels that stay",
        "Posts that become memory",
        "2.2M",
        "1.5M",
        "a.storyof.two",
    ):
        assert text in html


def test_a_story_website_matches_illustration_theme_and_real_reel_goal() -> None:
    html = (SITE_ROOT / "index.html").read_text(encoding="utf-8")

    for text in (
        "paper-flow",
        "Instagram Reel embed",
        "Creative room",
        "Story model",
        "Visual model",
        "Data judge",
        "Brand proof",
        "The photo archive still matters",
        "fit-check system",
    ):
        assert text in html

    assert html.count("instagram-media") >= 3
    assert "https://www.instagram.com/p/DXtVEqfiQKR/" in html
    assert "https://www.instagram.com/p/DYCvC_ap_8Z/" in html
    assert "https://www.instagram.com/p/DXrJeGQiemi/" in html


def test_a_story_website_has_local_visual_assets() -> None:
    for asset in (
        "assets/hero-laugh.jpg",
        "assets/reel-jaldi.jpg",
        "assets/carousel-calm.jpg",
        "assets/post-mountains.jpg",
        "design/concept-homepage.png",
        "scripts.js",
    ):
        assert (SITE_ROOT / asset).exists()
