from django.db import migrations


def record_opening_balances(apps, schema_editor):
    """Start the ledger from current stock so the sum of movements always equals stock_quantity."""
    ProductVariant = apps.get_model("catalog", "ProductVariant")
    StockMovement = apps.get_model("inventory", "StockMovement")
    StockMovement.objects.bulk_create([
        StockMovement(
            variant_id=variant_id, quantity_change=stock, balance_after=stock, reason="adjustment",
            note="Opening balance",
        )
        for variant_id, stock in ProductVariant.objects.filter(stock_quantity__gt=0).values_list("id", "stock_quantity")
    ])


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0001_initial"),
        ("catalog", "0002_price_279"),
    ]

    operations = [migrations.RunPython(record_opening_balances, migrations.RunPython.noop)]
