from pathlib import Path

from django.urls import reverse

from .conf import get_setting


def activity_request_id(request):
    rid = getattr(request, "_request_id", "")
    return {"ACTIVITY_REQUEST_ID": rid}


def activity_open_source(request):
    """Branding, SEO, and GitHub links for templates (Nitesh Kumar Singh / nkscoder)."""
    author_name = get_setting("AUTHOR_NAME")
    author_handle = get_setting("AUTHOR_HANDLE")
    package_name = get_setting("PACKAGE_NAME")
    seo_site = get_setting("SEO_SITE_NAME")
    path = getattr(request, "path", "") or ""
    page_title = path.strip("/").replace("/", " ").title() or "Dashboard"
    seo_title = f"{page_title} — {seo_site} | {author_name} ({author_handle})"

    license_url = ""
    try:
        license_url = request.build_absolute_uri(reverse("activity_license"))
    except Exception:
        license_url = get_setting("GITHUB_URL") + "/blob/main/LICENSE"

    canonical = ""
    try:
        canonical = request.build_absolute_uri()
    except Exception:
        canonical = get_setting("HOMEPAGE_URL")

    license_text = ""
    license_path = Path(__file__).resolve().parent / "LICENSE"
    if license_path.is_file():
        license_text = license_path.read_text(encoding="utf-8")

    return {
        "activity_base_template": get_setting("BASE_TEMPLATE"),
        "activity_author_name": author_name,
        "activity_author_handle": author_handle,
        "activity_github_url": get_setting("GITHUB_URL"),
        "activity_homepage_url": get_setting("HOMEPAGE_URL"),
        "activity_package_name": package_name,
        "activity_package_version": get_setting("PACKAGE_VERSION"),
        "activity_seo_site_name": seo_site,
        "activity_seo_title": seo_title,
        "activity_seo_description": get_setting("SEO_DESCRIPTION"),
        "activity_seo_keywords": get_setting("SEO_KEYWORDS"),
        "activity_search_placeholder": get_setting("SEARCH_PLACEHOLDER"),
        "activity_canonical_url": canonical,
        "activity_license_url": license_url,
        "activity_license_text": license_text,
    }
