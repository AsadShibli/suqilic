from django.db import migrations, models


def to_taka(apps, schema_editor):
    SiteSettings = apps.get_model("core", "SiteSettings")
    for s in SiteSettings.objects.all():
        s.currency_symbol = "৳"
        s.currency_code = "BDT"
        if s.announcement_text and "$" in s.announcement_text:
            s.announcement_text = "Free shipping on orders over ৳500"
        s.save()


class Migration(migrations.Migration):
    dependencies = [("core", "0002_stored_file")]

    operations = [
        migrations.AlterField("sitesettings", "currency_symbol", models.CharField(default="৳", max_length=5)),
        migrations.AlterField("sitesettings", "currency_code", models.CharField(default="BDT", max_length=3)),
        migrations.RunPython(to_taka, migrations.RunPython.noop),
    ]
