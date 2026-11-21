from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("eventos", "0003_validar_precios_no_negativos"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="detalleevento",
            name="cantidad",
        ),
    ]
