from decimal import Decimal

import pytest

from apps.catalog.models import ProductVariant
from apps.inventory.models import PurchaseOrder, StockMovement, Supplier
from apps.orders.models import Order

from .test_orders import CUSTOMER, add_to_cart

pytestmark = pytest.mark.django_db

PO_URL = "/api/v1/admin/purchase-orders/"


def stock(variant):
    return ProductVariant.objects.get(pk=variant.pk).stock_quantity


def ledger_total(variant):
    return sum(StockMovement.objects.filter(variant=variant).values_list("quantity_change", flat=True))


@pytest.fixture
def supplier(db):
    return Supplier.objects.create(name="Dhaka Print House")


def create_po(staff_api, supplier, variant, quantity=10):
    res = staff_api.post(PO_URL, {
        "supplier": supplier.id,
        "lines": [{"variant": variant.id, "quantity_ordered": quantity, "unit_cost": "120.00"}],
    }, format="json")
    assert res.status_code == 201, res.data
    return res.data


def test_purchase_order_partial_then_full_receipt(staff_api, supplier, make_product):
    variant = make_product(stock=0).variants.get()
    po = create_po(staff_api, supplier, variant, quantity=10)
    assert po["number"].startswith("PO-") and po["status"] == "draft" and po["total_cost"] == "1200.00"
    line_id = po["lines"][0]["id"]

    # Nothing can be received until the PO is sent to the supplier.
    assert staff_api.post(f"{PO_URL}{po['id']}/receive/", {"lines": [{"line": line_id, "quantity": 1}]},
                          format="json").status_code == 400
    assert staff_api.post(f"{PO_URL}{po['id']}/mark-ordered/").data["status"] == "ordered"

    part = staff_api.post(f"{PO_URL}{po['id']}/receive/", {"lines": [{"line": line_id, "quantity": 4}]}, format="json")
    assert part.data["status"] == "partially_received" and stock(variant) == 4

    over = staff_api.post(f"{PO_URL}{po['id']}/receive/", {"lines": [{"line": line_id, "quantity": 7}]}, format="json")
    assert over.status_code == 400 and stock(variant) == 4

    full = staff_api.post(f"{PO_URL}{po['id']}/receive/", {"lines": [{"line": line_id, "quantity": 6}]}, format="json")
    assert full.data["status"] == "received" and full.data["received_at"] and stock(variant) == 10

    movements = StockMovement.objects.filter(variant=variant, reason="purchase_received")
    assert [m.quantity_change for m in movements] == [6, 4] and movements[0].balance_after == 10
    assert ledger_total(variant) == stock(variant)


def test_received_purchase_order_cannot_be_edited_or_cancelled(staff_api, supplier, make_product):
    variant = make_product(stock=0).variants.get()
    po = create_po(staff_api, supplier, variant, quantity=2)
    staff_api.post(f"{PO_URL}{po['id']}/mark-ordered/")
    staff_api.post(f"{PO_URL}{po['id']}/receive/", {"lines": [{"line": po["lines"][0]["id"], "quantity": 2}]},
                   format="json")

    edit = staff_api.patch(f"{PO_URL}{po['id']}/", {"lines": []}, format="json")
    assert edit.status_code == 400
    assert staff_api.post(f"{PO_URL}{po['id']}/cancel/").status_code == 400
    assert staff_api.delete(f"{PO_URL}{po['id']}/").status_code == 400
    assert PurchaseOrder.objects.get(pk=po["id"]).status == "received"


def test_sale_and_cancellation_are_recorded_in_ledger(api, staff_api, make_product):
    variant = make_product(stock=5).variants.get()
    cart_id = add_to_cart(api, variant.id, 2)["X-Cart-Id"]
    number = api.post("/api/v1/orders/", CUSTOMER, format="json", HTTP_X_CART_ID=cart_id).data["order_number"]
    order = Order.objects.get(order_number=number)

    sale = StockMovement.objects.get(order=order, reason="sale")
    assert sale.quantity_change == -2 and sale.balance_after == 3

    staff_api.post(f"/api/v1/admin/orders/{order.id}/status/", {"status": "cancelled"}, format="json")
    back = StockMovement.objects.get(order=order, reason="order_cancelled")
    assert back.quantity_change == 2 and back.balance_after == 5 and stock(variant) == 5


def test_manual_adjustment_and_variant_edit_write_ledger(staff_api, make_product):
    product = make_product(stock=0)
    variant = product.variants.get()

    res = staff_api.post("/api/v1/admin/stock-movements/adjust/",
                         {"variant": variant.id, "quantity_change": 3, "note": "Found in storeroom"}, format="json")
    assert res.status_code == 201 and res.data["balance_after"] == 3

    too_low = staff_api.post("/api/v1/admin/stock-movements/adjust/",
                             {"variant": variant.id, "quantity_change": -9, "note": "Damaged"}, format="json")
    assert too_low.status_code == 400 and stock(variant) == 3

    # Editing stock on the product page is recorded as an adjustment of the difference.
    edit = staff_api.patch(f"/api/v1/admin/products/{product.id}/variants/{variant.id}/",
                           {"stock_quantity": 8, "price": str(Decimal("9.50"))}, format="json")
    assert edit.status_code == 200 and edit.data["stock_quantity"] == 8
    assert StockMovement.objects.filter(variant=variant).first().quantity_change == 5
    assert ledger_total(variant) == stock(variant) == 8

    listing = staff_api.get("/api/v1/admin/stock-movements/", {"variant": variant.id})
    assert listing.data["count"] == 2
    assert staff_api.get("/api/v1/admin/stock-movements/export/").status_code == 200


def test_supplier_with_purchase_orders_cannot_be_deleted(staff_api, supplier, make_product):
    create_po(staff_api, supplier, make_product(stock=0).variants.get())
    assert staff_api.delete(f"/api/v1/admin/suppliers/{supplier.id}/").status_code == 400
    assert staff_api.get("/api/v1/admin/suppliers/").data["results"][0]["name"] == supplier.name
