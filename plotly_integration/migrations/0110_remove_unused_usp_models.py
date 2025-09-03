# Generated migration to remove unused USP models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plotly_integration', '0109_add_simplified_dasgip_models'),
    ]

    operations = [
        # Drop unused tables in reverse dependency order
        migrations.RunSQL(
            "DROP TABLE IF EXISTS usp_bioreactor_data;",
            reverse_sql=migrations.RunSQL.noop
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS usp_parameter_track;",
            reverse_sql=migrations.RunSQL.noop
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS usp_bioreactor_unit;",
            reverse_sql=migrations.RunSQL.noop
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS usp_dasgip_experiment;",
            reverse_sql=migrations.RunSQL.noop
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS usp_dasgip_file;",
            reverse_sql=migrations.RunSQL.noop
        ),
    ]