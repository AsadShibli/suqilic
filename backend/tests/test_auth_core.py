import pytest

from apps.core.models import MenuItem

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db


def test_register_login_me(api):
    res = api.post("/api/v1/auth/register/", {"email": "New@Example.com", "password": PASSWORD}, format="json")
    assert res.status_code == 201 and res.data["user"]["email"] == "new@example.com"

    login = api.post("/api/v1/auth/login/", {"email": "NEW@example.com", "password": PASSWORD}, format="json")
    assert login.status_code == 200
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    assert api.get("/api/v1/me/").data["email"] == "new@example.com"


def test_contact_and_newsletter(api, mailoutbox):
    assert api.post("/api/v1/contact/", {"name": "A", "email": "a@a.com", "message": "Hi"}).status_code == 201
    assert len(mailoutbox) == 1
    assert api.post("/api/v1/newsletter/subscribe/", {"email": "a@a.com"}).status_code == 201


def test_menu_tree_and_seo(api):
    parent = MenuItem.objects.create(menu="header", label="Shop", url="/collections")
    MenuItem.objects.create(menu="header", label="Card Skins", url="/collections/card-skins", parent=parent)

    menu = api.get("/api/v1/menus/header/").data
    assert menu[0]["children"][0]["label"] == "Card Skins"
    assert api.get("/robots.txt").status_code == 200
    assert api.get("/sitemap.xml").status_code == 200
