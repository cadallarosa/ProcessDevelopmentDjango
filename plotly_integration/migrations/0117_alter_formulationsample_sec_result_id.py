# Generated manually to fix sec_result_id nullable issue

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plotly_integration', '0116_create_formulation_tables'),
    ]

    operations = [
        migrations.AlterField(
            model_name='formulationsample',
            name='sec_result_id',
            field=models.CharField(blank=True, help_text='HPLC/SEC Result ID', max_length=100, null=True),
        ),
    ]