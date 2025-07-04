# Generated by Django 5.1.4 on 2025-05-29 18:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plotly_integration', '0090_limsupstreamsamples_delete_limsfedbatchsamples'),
    ]

    operations = [
        migrations.RenameField(
            model_name='limsupstreamsamples',
            old_name='cld_30ml_octet_titer',
            new_name='hf_octet_titer',
        ),
        migrations.RenameField(
            model_name='limsupstreamsamples',
            old_name='pro_aqa_titer',
            new_name='pro_aqa_e_titer',
        ),
        migrations.RenameField(
            model_name='limsupstreamsamples',
            old_name='sec_2_wks_a_conc',
            new_name='pro_aqa_hf_titer',
        ),
        migrations.RemoveField(
            model_name='limsupstreamsamples',
            name='sec_2wks_n_conc',
        ),
    ]
