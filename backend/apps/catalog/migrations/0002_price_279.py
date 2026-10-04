from django.db import migrations


def reprice(apps, schema_editor):
    apps.get_model("catalog", "ProductVariant").objects.update(price="279.00")
    apps.get_model("catalog", "Product").objects.update(base_price="279.00", compare_at_price="350.00")


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]
    operations = [migrations.RunPython(reprice, migrations.RunPython.noop)]
