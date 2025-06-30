from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


# Empower HPLC Tables
class SampleMetadata(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.IntegerField()
    system_name = models.CharField(max_length=255)
    project_name = models.CharField(max_length=255, null=True, blank=True)
    sample_prefix = models.CharField(max_length=255, null=True, blank=True)
    sample_number = models.IntegerField(null=True, blank=True)
    sample_suffix = models.CharField(max_length=255, null=True, blank=True)
    sample_type = models.CharField(max_length=255, null=True, blank=True)
    analysis_type = models.IntegerField(null=True, blank=True)  # 1:SEC,2:PROA
    sample_name = models.CharField(max_length=255, null=True, blank=True)  # ✅ Fixed
    sample_set_id = models.IntegerField(null=True, blank=True)
    sample_set_name = models.CharField(max_length=255, null=True, blank=True)
    date_acquired = models.DateTimeField(null=True, blank=True)  # ✅ Changed from DateTimeField
    acquired_by = models.CharField(max_length=255, null=True, blank=True)
    run_time = models.FloatField(null=True, blank=True)
    processing_method = models.CharField(max_length=255, null=True, blank=True)
    processed_channel_description = models.CharField(max_length=255, null=True, blank=True)
    injection_volume = models.FloatField(null=True, blank=True)
    injection_id = models.IntegerField(null=True, blank=True)
    column_name = models.CharField(max_length=255, null=True, blank=True)
    column_serial_number = models.CharField(max_length=255, null=True, blank=True)
    column_id = models.ForeignKey('EmpowerColumnLogbook', on_delete=models.SET_NULL, null=True, db_column="column_id",
                                  to_field="id")
    instrument_method_id = models.IntegerField(null=True, blank=True)
    instrument_method_name = models.CharField(max_length=255, null=True, blank=True)
    dilution = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'sample_metadata'
        managed = True
        unique_together = ('result_id', 'system_name')
        indexes = [
            models.Index(fields=['sample_type', 'sample_name', '-date_acquired']),
            models.Index(fields=['sample_set_name', 'sample_prefix']),
        ]


class PeakResults(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.IntegerField()
    system_name = models.CharField(max_length=255, null=True, blank=True)
    channel_name = models.CharField(max_length=255, null=True, blank=True)  # ✅ Fixed
    peak_name = models.CharField(max_length=255, null=True, blank=True)
    peak_retention_time = models.FloatField(null=True, blank=True)
    peak_start_time = models.FloatField(null=True, blank=True)
    peak_end_time = models.FloatField(null=True, blank=True)
    area = models.IntegerField(null=True, blank=True)
    percent_area = models.FloatField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    asym_at_10 = models.FloatField(null=True, blank=True)
    plate_count = models.FloatField(null=True, blank=True)
    res_hh = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'peak_results'
        managed = True
        unique_together = ('result_id', 'peak_retention_time')
        indexes = [
            models.Index(fields=['result_id', 'peak_retention_time']),
        ]


class ChromMetadata(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.IntegerField()
    system_name = models.CharField(max_length=255)
    sample_name = models.CharField(max_length=255, null=True, blank=True)  # ✅ Fixed
    sample_set_name = models.CharField(max_length=255, null=True, blank=True)
    sample_set_id = models.IntegerField(null=True, blank=True)
    channel_1 = models.CharField(max_length=255, null=True, blank=True)
    channel_2 = models.CharField(max_length=255, null=True, blank=True)
    channel_3 = models.CharField(max_length=255, null=True, blank=True)
    average_pressure = models.FloatField(null=True, blank=True)
    max_pressure = models.FloatField(null=True, blank=True)  # New field
    min_pressure = models.FloatField(null=True, blank=True)  # New field
    pressure_variance = models.FloatField(null=True, blank=True)  # New field
    pressure_stddev = models.FloatField(null=True, blank=True)  # New field
    retention_time_range = models.FloatField(null=True, blank=True)  # New field
    peak_pressure_time = models.FloatField(null=True, blank=True)  # New field

    class Meta:
        db_table = 'chrom_metadata'
        managed = True
        unique_together = ('result_id', 'system_name')


class TimeSeriesData(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.IntegerField()
    system_name = models.CharField(max_length=255)
    time = models.FloatField()
    channel_1 = models.FloatField(null=True, blank=True)
    channel_2 = models.FloatField(null=True, blank=True)
    channel_3 = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'time_series_data'
        managed = True
        unique_together = ('result_id', 'time')
        indexes = [
            models.Index(fields=['result_id', 'time']),
        ]
        ordering = ['result_id', 'time']


class EmpowerColumnLogbook(models.Model):
    id = models.AutoField(primary_key=True)  # Integer primary key
    column_serial_number = models.CharField(max_length=255, unique=True)  # Unique serial number
    column_name = models.CharField(max_length=255)
    total_injections = models.IntegerField(default=0)
    most_recent_injection_date = models.DateField(null=True, blank=True)  # ✅ Fixed

    class Meta:
        db_table = 'empower_column_logbook'
        managed = True


class SystemInformation(models.Model):
    system_name = models.CharField(max_length=255, primary_key=True)  # ✅ Fixed
    channel_1 = models.CharField(max_length=255, null=True, blank=True)
    channel_2 = models.CharField(max_length=255, null=True, blank=True)
    channel_3 = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'system_information'
        managed = True


# django Specific Tables


class Report(models.Model):
    report_id = models.AutoField(primary_key=True)
    report_name = models.CharField(max_length=255, null=True, blank=True)
    project_id = models.CharField(max_length=255, null=True, blank=True)
    analysis_type = models.IntegerField(null=True, blank=True)
    sample_type = models.CharField(max_length=255, null=True, blank=True)
    selected_samples = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    date_created = models.DateTimeField(null=True, blank=True)
    selected_result_ids = models.TextField(null=True, blank=True)
    department = models.IntegerField(null=True, blank=True)  # 1 = Process Development, 2 = Protein Engineering
    plot_settings = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'report'
        managed = True
        indexes = [
            models.Index(fields=['analysis_type', 'department', '-report_id']),
        ]


class Users(models.Model):
    user_id = models.IntegerField()
    user_name = models.CharField(max_length=255, primary_key=True)  # ✅ Fixed
    user_initials = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = 'users'
        managed = True


class Method(models.Model):
    method_id = models.AutoField(primary_key=True)
    method_type = models.IntegerField(null=True, blank=True)
    new_column_1 = models.IntegerField(null=True, blank=True)
    new_column_2 = models.IntegerField(null=True, blank=True)
    new_column_3 = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'method'
        managed = True


class ReportInstance(models.Model):
    report_instance_id = models.AutoField(primary_key=True)
    exclusions = models.TextField(null=True, blank=True)
    report_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'report_instance'
        managed = True


class Results(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.IntegerField()
    system_name = models.CharField(max_length=255, null=True, blank=True)  # ✅ Fixed
    project_name = models.CharField(max_length=255, null=True, blank=True)  # ✅ Fixed
    sample_set_id = models.IntegerField(null=True, blank=True)
    sample_set_name = models.CharField(max_length=255, null=True, blank=True)
    acquired_by = models.CharField(max_length=255, null=True, blank=True)
    column_serial_number = models.CharField(max_length=255, null=True, blank=True)
    new_column = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'results'
        managed = True


###UFDF/Viral Filtration Models

class UFDFMetadata(models.Model):
    result_id = models.AutoField(primary_key=True)  # Auto-incremented result ID
    molecule_name = models.TextField()
    experiment_name = models.TextField()
    experimental_notes = models.TextField(blank=True, null=True)

    cassette_type = models.TextField(null=True, blank=True)
    load_concentration = models.FloatField(null=True, blank=True)
    load_volume = models.FloatField(null=True, blank=True)
    load_mass = models.FloatField(null=True, blank=True)

    system_void_volume = models.FloatField(null=True, blank=True)
    target_diafiltration_concentration = models.FloatField(null=True, blank=True)

    uf1_target_reservoir_mass = models.FloatField(null=True, blank=True)
    diavolumes = models.IntegerField(null=True, blank=True)
    permeate_target_mass = models.FloatField(null=True, blank=True)
    diafiltration_volume_required = models.FloatField(null=True, blank=True)

    lmh_target = models.FloatField(null=True, blank=True)
    flow_rate = models.FloatField(null=True, blank=True)
    target_flow_rate = models.FloatField(null=True, blank=True)
    target_p2500_setpoint = models.FloatField(null=True, blank=True)
    target_p3000_setpoint = models.FloatField(null=True, blank=True)

    recovery = models.FloatField(null=True, blank=True)
    final_volume = models.FloatField(null=True, blank=True)
    final_concentration = models.FloatField(null=True, blank=True)
    product_mass = models.FloatField(null=True, blank=True)
    yield_percentage = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for record creation

    class Meta:
        db_table = "ufdf_metadata"


class SartoflowTimeSeriesData(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.ForeignKey(UFDFMetadata, on_delete=models.CASCADE, null=True, blank=True)
    batch_id = models.CharField(max_length=255)
    pdat_time = models.DateTimeField()
    process_time = models.FloatField(null=True, blank=True)

    ag2100_value = models.FloatField(null=True, blank=True)
    ag2100_setpoint = models.FloatField(null=True, blank=True)
    ag2100_mode = models.IntegerField(null=True, blank=True)
    ag2100_output = models.FloatField(null=True, blank=True)

    dpress_value = models.FloatField(null=True, blank=True)
    dpress_output = models.FloatField(null=True, blank=True)
    dpress_mode = models.IntegerField(null=True, blank=True)
    dpress_setpoint = models.FloatField(null=True, blank=True)

    f_perm_value = models.FloatField(null=True, blank=True)

    p2500_setpoint = models.FloatField(null=True, blank=True)
    p2500_value = models.FloatField(null=True, blank=True)
    p2500_output = models.FloatField(null=True, blank=True)
    p2500_mode = models.IntegerField(null=True, blank=True)

    p3000_setpoint = models.FloatField(null=True, blank=True)
    p3000_mode = models.IntegerField(null=True, blank=True)
    p3000_output = models.FloatField(null=True, blank=True)
    p3000_value = models.FloatField(null=True, blank=True)
    p3000_t = models.FloatField(null=True, blank=True)

    pir2600 = models.FloatField(null=True, blank=True)
    pir2700 = models.FloatField(null=True, blank=True)

    pirc2500_value = models.FloatField(null=True, blank=True)
    pirc2500_output = models.FloatField(null=True, blank=True)
    pirc2500_setpoint = models.FloatField(null=True, blank=True)
    pirc2500_mode = models.IntegerField(null=True, blank=True)

    qir2000 = models.FloatField(null=True, blank=True)
    qir2100 = models.FloatField(null=True, blank=True)

    tir2100 = models.FloatField(null=True, blank=True)
    tmp = models.FloatField(null=True, blank=True)

    wir2700 = models.FloatField(null=True, blank=True)

    wirc2100_output = models.FloatField(null=True, blank=True)
    wirc2100_setpoint = models.FloatField(null=True, blank=True)
    wirc2100_mode = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.batch_id} - {self.pdat_time}"

    class Meta:
        db_table = "sartoflow_time_series_data"
        managed = True


class VFMetadata(models.Model):
    result_id = models.AutoField(primary_key=True)  # Auto-incremented result ID
    molecule_name = models.TextField()
    experiment_name = models.TextField()
    experimental_notes = models.TextField(blank=True, null=True)
    filter_type = models.TextField(null=True, blank=True)
    load_concentration = models.FloatField(null=True, blank=True)
    load_volume = models.FloatField(null=True, blank=True)
    load_mass = models.FloatField(null=True, blank=True)
    target_pressure = models.FloatField(null=True, blank=True)
    final_volume = models.FloatField(null=True, blank=True)
    final_concentration = models.FloatField(null=True, blank=True)
    product_mass = models.FloatField(null=True, blank=True)
    yield_percentage = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for record creation

    class Meta:
        db_table = "vf_metadata"


class VFTimeSeriesData(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.ForeignKey(VFMetadata, on_delete=models.CASCADE, null=True, blank=True)
    unit_step = models.BigIntegerField(null=True, blank=True)  # 1= Water Flush, 2= Buffer Flush, 3=Product Filtration
    batch_id = models.CharField(max_length=255)
    pdat_time = models.DateTimeField()
    process_time = models.FloatField(null=True, blank=True)
    pir2700 = models.FloatField(null=True, blank=True)
    wir2700 = models.FloatField(null=True, blank=True)
    f_perm_value = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.batch_id} - {self.pdat_time}"

    class Meta:
        db_table = "vf_time_series_data"
        managed = True


# '''Akta Models for table'''
class AktaNodeIds(models.Model):
    result_id = models.CharField(primary_key=True, max_length=255)
    run_log = models.CharField(max_length=1024, null=True, blank=True)
    fraction = models.CharField(max_length=1024, null=True, blank=True)
    uv_1 = models.CharField(max_length=1024, null=True, blank=True)
    uv_2 = models.CharField(max_length=1024, null=True, blank=True)
    uv_3 = models.CharField(max_length=1024, null=True, blank=True)
    cond = models.CharField(max_length=1024, null=True, blank=True)
    conc_b = models.CharField(max_length=1024, null=True, blank=True)
    ph = models.CharField(max_length=1024, null=True, blank=True)
    system_flow = models.CharField(max_length=1024, null=True, blank=True)
    system_pressure = models.CharField(max_length=1024, null=True, blank=True)
    sample_flow = models.CharField(max_length=1024, null=True, blank=True)
    sample_pressure = models.CharField(max_length=1024, null=True, blank=True)
    prec_pressure = models.CharField(max_length=1024, null=True, blank=True)
    deltac_pressure = models.CharField(max_length=1024, null=True, blank=True)
    postc_pressure = models.CharField(max_length=1024, null=True, blank=True)
    imported = models.BooleanField(default=False)
    timestamp_collected = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'akta_node_ids'


class AktaResult(models.Model):
    id = models.AutoField(primary_key=True)  # Ensure primary key is explicitly set
    result_id = models.CharField(max_length=50, unique=True)
    report_name = models.CharField(max_length=255, null=True, blank=True)
    column_name = models.TextField(null=True, blank=True)
    column_volume = models.TextField(null=True, blank=True)
    method = models.TextField(null=True, blank=True)
    result_path = models.TextField(null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    user = models.CharField(max_length=255, null=True, blank=True)
    sample_id = models.CharField(max_length=255, null=True, blank=True)
    run_type = models.BigIntegerField(null=True, blank=True)
    scouting_id = models.BigIntegerField(null=True, blank=True)
    scouting_run_num = models.BigIntegerField(null=True, blank=True)
    group_id = models.BigIntegerField(null=True, blank=True)
    system = models.CharField(max_length=255, null=True, blank=True)
    source_material_id = models.BigIntegerField(null=True, blank=True)
    downstream_step_id = models.BigIntegerField(null=True, blank=True)

    # Experiment metadata fields
    dn_num = models.CharField(max_length=100, blank=True, null=True)
    column_id = models.TextField(blank=True, null=True)
    buffers = models.TextField(blank=True, null=True)
    study_name = models.CharField(max_length=200, blank=True, null=True)
    description_of_purpose = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    load_cond = models.FloatField(blank=True, null=True)
    load_ph = models.FloatField(blank=True, null=True)
    load_titer = models.FloatField(blank=True, null=True)
    load_volume_ml = models.FloatField(blank=True, null=True)
    suggested_filename = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'akta_result'
        indexes = [
            # Already has unique index on result_id
            models.Index(fields=['report_name'], name='idx_result_report_name'),
        ]

    # def __str__(self):
    #     return f"Result ID: {self.result_id} | User: {self.user} | Date: {self.date}"


class AktaColumnsCharacteristics(models.Model):
    column_id = models.BigAutoField(primary_key=True)
    column_type = models.CharField(max_length=255)
    technique = models.CharField(max_length=255)
    column_volume = models.FloatField()
    diameter = models.FloatField()
    bed_height = models.FloatField()
    resin = models.CharField(max_length=255)
    alias = models.CharField(max_length=255)
    asymmetry = models.FloatField()
    plates_per_meter = models.FloatField()
    HETP = models.FloatField()
    num_cycles = models.BigIntegerField()
    avg_starting_pressure = models.FloatField()

    class Meta:
        db_table = 'akta_columns_characteristics'


class AktaMethodInformation(models.Model):
    id = models.BigAutoField(primary_key=True)
    method_name = models.CharField(max_length=255)
    last_saved = models.DateTimeField()
    created_by_user = models.CharField(max_length=255)
    method_notes = models.TextField()
    result_name = models.CharField(max_length=255)
    start_notes = models.TextField()
    scouting = models.BigIntegerField()
    created_for_system = models.CharField(max_length=255)

    class Meta:
        db_table = 'akta_method_information'


class AktaChromatogram(models.Model):
    date_time = models.DateTimeField(null=True, blank=True)
    ml = models.FloatField(null=True, blank=True)  # Volume in mL
    result_id = models.CharField(max_length=50, null=True, blank=True)
    uv_1_280 = models.FloatField(null=True, blank=True)  # UV Absorbance at 280nm
    uv_2_0 = models.FloatField(null=True, blank=True)
    uv_3_0 = models.FloatField(null=True, blank=True)
    cond = models.FloatField(null=True, blank=True)  # Conductivity
    conc_b = models.FloatField(null=True, blank=True)  # Concentration B
    pH = models.FloatField(null=True, blank=True)
    system_flow = models.FloatField(null=True, blank=True)
    system_linear_flow = models.FloatField(null=True, blank=True)
    system_pressure = models.FloatField(null=True, blank=True)
    cond_temp = models.FloatField(null=True, blank=True)
    sample_flow = models.FloatField(null=True, blank=True)
    sample_linear_flow = models.FloatField(null=True, blank=True)
    sample_pressure = models.FloatField(null=True, blank=True)
    preC_pressure = models.FloatField(null=True, blank=True)
    deltaC_pressure = models.FloatField(null=True, blank=True)
    postC_pressure = models.FloatField(null=True, blank=True)
    frac_temp = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "akta_chromatogram"

        indexes = [
            models.Index(fields=['result_id', 'ml'], name='idx_chrom_result_ml'),
            # This helps with ID-based sampling
            models.Index(fields=['result_id', 'id'], name='idx_chrom_result_id'),
        ]


class AktaFraction(models.Model):
    date_time = models.DateTimeField(null=True, blank=True)
    result_id = models.CharField(max_length=50, null=True, blank=True)
    ml = models.FloatField(null=True, blank=True)
    fraction = models.CharField(max_length=100, null=True, blank=True)  # Example column

    class Meta:
        db_table = "akta_fraction"
        indexes = [
            # This speeds up fraction analysis
            models.Index(fields=['result_id', 'date_time'], name='idx_fraction_result_time'),
        ]
    # def __str__(self):
    #     return f"Result: {self.result.result_id} | Fraction at ml: {self.ml}"


class AktaRunLog(models.Model):
    date_time = models.DateTimeField(null=True, blank=True)
    result_id = models.CharField(max_length=50, null=True, blank=True)
    ml = models.FloatField(null=True, blank=True)
    log_text = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "akta_run_log"
        indexes = [
            # This speeds up phase extraction
            models.Index(fields=['result_id', 'date_time'], name='idx_runlog_result_time'),
        ]

    # def __str__(self):
    #     return f"Result: {self.result.result_id} | Log at ml: {self.ml}"


class AktaScoutingList(models.Model):
    scouting_id = models.BigAutoField(primary_key=True)
    total_num_of_scoutings = models.BigIntegerField()
    run_scouting = models.BigIntegerField()
    run = models.BigIntegerField()
    scouting = models.BooleanField()
    variable = models.TextField()
    block = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=255)
    value = models.FloatField()

    class Meta:
        db_table = 'akta_scouting_list'


# Cell Culture Models

# Nova Flex 2 Models
class NovaFlex2(models.Model):
    id = models.AutoField(primary_key=True)  # Ensure primary key is explicitly set
    date_time = models.DateTimeField()
    sample_id = models.CharField(max_length=255)
    sample_type = models.IntegerField(null=True, blank=True)  # 1 = UP, 2 = CLD , 3 = Uncategorized
    gln = models.FloatField(null=True, blank=True)
    glu = models.FloatField(null=True, blank=True)
    gluc = models.FloatField(null=True, blank=True)
    lac = models.FloatField(null=True, blank=True)
    nh4 = models.FloatField(null=True, blank=True)
    pH = models.FloatField(null=True, blank=True)
    po2 = models.FloatField(null=True, blank=True)
    pco2 = models.FloatField(null=True, blank=True)
    osm = models.FloatField(null=True, blank=True)

    # New fields to store parsed sample information
    experiment = models.CharField(max_length=50, null=True, blank=True)
    day = models.IntegerField(null=True, blank=True)
    reactor_type = models.CharField(max_length=10, null=True, blank=True)
    reactor_number = models.IntegerField(null=True, blank=True)
    special = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'nova_flex_2'
        unique_together = ('date_time', 'sample_id')  # Enforce uniqueness


class NovaReport(models.Model):
    id = models.AutoField(primary_key=True)  # Ensure primary key is explicitly set
    report_name = models.CharField(max_length=255)
    project_id = models.CharField(max_length=255, null=True, blank=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    department = models.IntegerField(null=True, blank=True)  # 1 = UP, 2 = CLD , 3 = Uncategorized
    comments = models.TextField(null=True, blank=True)
    selected_result_ids = models.TextField()  # Stores comma-separated result IDs
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nova_report'


# Vicell Models
class ViCellData(models.Model):
    id = models.AutoField(primary_key=True)  # Ensure primary key is explicitly set
    sample_id = models.CharField(max_length=100, unique=True)
    date_time = models.DateTimeField(null=True, blank=True)
    experiment = models.CharField(max_length=50, null=True, blank=True)
    day = models.IntegerField(null=True, blank=True)
    reactor_type = models.CharField(max_length=10, null=True, blank=True)
    reactor_number = models.IntegerField(null=True, blank=True)
    special = models.CharField(max_length=50, null=True, blank=True)
    cell_count = models.FloatField(null=True, blank=True)
    viable_cells = models.FloatField(null=True, blank=True)
    total_cells_per_ml = models.FloatField(null=True, blank=True)
    viable_cells_per_ml = models.FloatField(null=True, blank=True)
    viability = models.FloatField(null=True, blank=True)
    average_diameter = models.FloatField(null=True, blank=True)
    average_viable_diameter = models.FloatField(null=True, blank=True)
    average_circularity = models.FloatField(null=True, blank=True)
    average_viable_circularity = models.FloatField(null=True, blank=True)
    sample_type = models.IntegerField(null=True, blank=True)  # 1 = UP, 2 = CLD , 3 = Uncategorized

    class Meta:
        db_table = 'vicell_data'
        unique_together = ('date_time', 'sample_id')  # Enforce uniqueness


class ViCellReport(models.Model):
    id = models.AutoField(primary_key=True)  # Ensure primary key is explicitly set
    report_name = models.CharField(max_length=255)
    project_id = models.CharField(max_length=255, null=True, blank=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    department = models.IntegerField(null=True, blank=True)  # 1 = UP, 2 = CLD , 3 = Uncategorized
    comments = models.TextField(null=True, blank=True)
    selected_result_ids = models.TextField()  # Stores comma-separated result IDs
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vicell_report'


# Cell Culture Aggregated Data


# LC-MS Released N-Glycan
class ReleasedGlycanResult(models.Model):
    result_id = models.CharField(max_length=64, primary_key=True)  # UUIDv5 from filename
    result_name = models.TextField()  # e.g. filename without extension
    project_id = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'released_glycan_result'


class ReleasedGlycanComponent(models.Model):
    result = models.ForeignKey(ReleasedGlycanResult, on_delete=models.CASCADE, related_name='glycans')
    component_name = models.TextField()
    observed_rt_min = models.FloatField(null=True, blank=True)
    amount = models.FloatField(null=True, blank=True)
    percent_amount = models.FloatField(null=True, blank=True)
    expected_glycan_units = models.FloatField(null=True, blank=True)
    glycan_units = models.FloatField(null=True, blank=True)
    expected_mass_da = models.FloatField(null=True, blank=True)
    observed_mass_da = models.FloatField(null=True, blank=True)
    charge = models.IntegerField(null=True, blank=True)
    response = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'released_glycan_component'


class GlycanReport(models.Model):
    id = models.AutoField(primary_key=True)
    report_name = models.CharField(max_length=255, null=True, blank=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    project_id = models.CharField(max_length=255, null=True, blank=True)
    department = models.IntegerField(null=True, blank=True)  # 1 = UP, 2 = CLD , 3 = Uncategorized
    comments = models.TextField(null=True, blank=True)
    selected_result_ids = models.TextField(help_text="Comma-separated UUIDs of ReleasedGlycanResult")
    selected_glycan_names = models.TextField(help_text="Optional: comma-separated component_name values")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'released_glycan_report'


# LC-MS Mass Check
class MassCheckResult(models.Model):
    result_id = models.CharField(max_length=64, primary_key=True)  # UUIDv5 from filename
    result_name = models.TextField()  # e.g. filename without extension
    project_id = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mass_check_result'


class MassCheckComponent(models.Model):
    result = models.ForeignKey(MassCheckResult, on_delete=models.CASCADE, related_name='components')
    protein_name = models.TextField()
    expected_mass_da = models.FloatField(null=True, blank=True)
    observed_mass_da = models.FloatField(null=True, blank=True)
    mass_error_mda = models.FloatField(null=True, blank=True)
    mass_error_ppm = models.FloatField(null=True, blank=True)
    observed_rt_min = models.FloatField(null=True, blank=True)
    response = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'mass_check_component'


class MassCheckReport(models.Model):
    id = models.AutoField(primary_key=True)
    report_name = models.CharField(max_length=255, null=True, blank=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    project_id = models.CharField(max_length=255, null=True, blank=True)
    department = models.IntegerField(null=True, blank=True)  # 1 = UP, 2 = CLD , 3 = Uncategorized
    comments = models.TextField(null=True, blank=True)
    selected_result_ids = models.TextField(help_text="Comma-separated UUIDs of MassCheckResult")
    selected_result_names = models.TextField(help_text="Optional: comma-separated component_name values")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mass_check_report'


# CE-SDS Models
class CESDSMetadata(models.Model):
    original_file_name = models.CharField(max_length=255)
    sample_type = models.IntegerField(null=True, blank=True)  # 1:CLD/FB,2:UP,3:PD
    sample_id_full = models.CharField(max_length=255)
    sample_id_clean = models.CharField(max_length=255)
    sample_prefix = models.CharField(max_length=10)  # R or NR
    data_file_path = models.TextField()
    method_path = models.TextField()
    user_name = models.CharField(max_length=255)
    acquisition_datetime = models.DateTimeField(null=True, blank=True)
    sampling_rate = models.FloatField()
    total_data_points = models.IntegerField()
    x_axis_title = models.CharField(max_length=255)
    y_axis_title = models.CharField(max_length=255)
    x_axis_multiplier = models.FloatField()
    y_axis_multiplier = models.FloatField()

    # Sample set grouping
    sample_set_name = models.CharField(max_length=255)
    sample_set_id = models.BigIntegerField()  # Fast lookup ID (e.g., hash)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ce_sds_metadata'

    def __str__(self):
        return f"{self.sample_id_full} ({self.sample_set_name})"


class CESDSTimeSeries(models.Model):
    metadata = models.ForeignKey(CESDSMetadata, on_delete=models.CASCADE, related_name='time_series')
    time_min = models.FloatField()
    channel_1 = models.FloatField()
    channel_2 = models.FloatField()
    channel_3 = models.FloatField()

    class Meta:
        db_table = 'ce_sds_time_series'

    def __str__(self):
        return f"{self.metadata.sample_id_full} - {self.time_min:.3f} min"


class CESDSReport(models.Model):
    report_name = models.CharField(max_length=255)
    project_id = models.CharField(max_length=100)
    user_id = models.CharField(max_length=100)
    comments = models.TextField(blank=True)
    selected_samples = models.TextField()  # comma-separated sample names
    selected_result_ids = models.TextField()  # comma-separated result_ids
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ce_sds_report'


# cIEF Models
class CIEFMetadata(models.Model):
    original_file_name = models.CharField(max_length=255)
    sample_type = models.IntegerField(null=True, blank=True)  # 1:CLD/FB,2:UP,3:PD
    sample_id_full = models.CharField(max_length=255)
    sample_id_clean = models.CharField(max_length=255)
    sample_prefix = models.CharField(max_length=10)  # R or NR
    data_file_path = models.TextField()
    method_path = models.TextField()
    user_name = models.CharField(max_length=255)
    acquisition_datetime = models.DateTimeField(null=True, blank=True)
    sampling_rate = models.FloatField()
    total_data_points = models.IntegerField()
    x_axis_title = models.CharField(max_length=255)
    y_axis_title = models.CharField(max_length=255)
    x_axis_multiplier = models.FloatField()
    y_axis_multiplier = models.FloatField()

    # Sample set grouping
    sample_set_name = models.CharField(max_length=255)
    sample_set_id = models.BigIntegerField()  # Fast lookup ID (e.g., hash)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cief_metadata'

    def __str__(self):
        return f"{self.sample_id_full} ({self.sample_set_name})"


class CIEFTimeSeries(models.Model):
    metadata = models.ForeignKey(CIEFMetadata, on_delete=models.CASCADE, related_name='time_series')
    time_min = models.FloatField()
    channel_1 = models.FloatField()
    channel_2 = models.FloatField()
    channel_3 = models.FloatField()

    class Meta:
        db_table = 'cief_time_series'

    def __str__(self):
        return f"{self.metadata.sample_id_full} - {self.time_min:.3f} min"


class CIEFReport(models.Model):
    report_name = models.CharField(max_length=255)
    project_id = models.CharField(max_length=100)
    user_id = models.CharField(max_length=100)
    comments = models.TextField(blank=True)
    selected_samples = models.TextField()  # comma-separated sample names
    selected_result_ids = models.TextField()  # comma-separated result_ids
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cief_report'


# LIMS Sample Tracking
# --- Shared status choices ---
STATUS_CHOICES = [
    ("in_progress", "In Progress"),
    ("complete", "Complete"),
    ("review", "Under Review"),
]


# Overall Project Information
class LimsProjectInformation(models.Model):
    protein = models.TextField(null=True, blank=True)
    project = models.TextField()
    project_description = models.TextField(null=True, blank=True)
    molecule_type = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    purifications = models.TextField(null=True, blank=True)
    plasmids = models.TextField(null=True, blank=True)
    plasmid_description = models.TextField(null=True, blank=True)
    tags = models.TextField(null=True, blank=True)
    transfections = models.TextField(null=True, blank=True)
    titer = models.FloatField(null=True, blank=True)  # Titer [μg/mL]
    protein_concentration = models.FloatField(null=True, blank=True)  # Protein Concentration [mg/mL]
    nanodrop_e1 = models.FloatField(null=True, blank=True)
    molecular_weight = models.FloatField(null=True, blank=True)  # Molecular Weight [Da]
    percent_poi = models.FloatField(null=True, blank=True)  # % POI
    pi = models.FloatField(null=True, blank=True)  # pI
    latest_purification_date = models.DateTimeField(null=True, blank=True)
    purified = models.BooleanField(default=False)  # Boolean field for 'Purified'

    class Meta:
        db_table = 'lims_project_information'
        managed = True
        # indexes = [
        #     models.Index(fields=['protein']),  # For project lookups
        # ]


# Lims Fed Batch Sample Details
class LimsUpstreamSamples(models.Model):
    SAMPLE_TYPE_CHOICES = [
        (1, "UP"),
        (2, "FB"),
    ]
    id = models.AutoField(primary_key=True)
    sample_type = models.IntegerField(choices=SAMPLE_TYPE_CHOICES)
    sample_number = models.IntegerField()
    project = models.CharField(max_length=255, null=True, blank=True)
    sip_number = models.CharField(max_length=255, null=True, blank=True)
    cell_line = models.CharField(max_length=255, null=True, blank=True)
    # Up Specific
    experiment_number = models.IntegerField(null=True, blank=True)
    culture_duration = models.IntegerField(null=True, blank=True)
    vessel_type = models.CharField(max_length=255, null=True, blank=True)

    description = models.CharField(max_length=255, null=True, blank=True)
    development_stage = models.CharField(max_length=255, null=True, blank=True)  # CLD
    analyst = models.CharField(max_length=255, null=True, blank=True)
    harvest_date = models.DateField(null=True, blank=True)
    unifi_number = models.CharField(max_length=255, null=True, blank=True)
    titer_comment = models.TextField(null=True, blank=True)
    hf_octet_titer = models.FloatField(null=True, blank=True)
    pro_aqa_hf_titer = models.FloatField(null=True, blank=True)
    pro_aqa_e_titer = models.FloatField(null=True, blank=True)
    fast_pro_a_recovery = models.FloatField(null=True, blank=True)
    purification_recovery_a280 = models.FloatField(null=True, blank=True)
    proa_eluate_a280_conc = models.FloatField(null=True, blank=True)
    proa_eluate_volume = models.FloatField(null=True, blank=True)
    hccf_loading_volume = models.FloatField(null=True, blank=True)
    proa_recovery = models.FloatField(null=True, blank=True)
    proa_column_size = models.FloatField(null=True, blank=True)
    column_id = models.CharField(max_length=255, null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'lims_upstream_samples'
        managed = True


# --- Main SampleAnalysis Table ---
class LimsSampleAnalysis(models.Model):
    SAMPLE_TYPE_CHOICES = [
        (1, "UP"),
        (2, "FB"),
        (3, "PD"),
    ]
    sample_id = models.CharField(max_length=100, primary_key=True)
    sample_type = models.IntegerField(choices=SAMPLE_TYPE_CHOICES)
    sample_date = models.DateField(null=True, blank=True)
    project_id = models.CharField(max_length=100)
    description = models.CharField(max_length=256, blank=True)

    analyst = models.CharField(max_length=100)
    dn = models.ForeignKey("LimsDnAssignment", on_delete=models.CASCADE, related_name="samples", null=True, blank=True)
    up = models.ForeignKey(
        "LimsUpstreamSamples",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="related_analysis"
    )

    a280_result = models.FloatField(null=True, blank=True)
    sec_result = models.OneToOneField("LimsSecResult", null=True, blank=True, on_delete=models.SET_NULL)
    titer_result = models.OneToOneField("LimsTiterResult", null=True, blank=True, on_delete=models.SET_NULL)
    mass_check_result = models.OneToOneField("LimsMassCheckResult", null=True, blank=True, on_delete=models.SET_NULL)
    glycan_result = models.OneToOneField("LimsReleasedGlycanResult", null=True, blank=True, on_delete=models.SET_NULL)
    ce_sds_result = models.OneToOneField("LimsCeSdsResult", null=True, blank=True, on_delete=models.SET_NULL)
    cief_result = models.OneToOneField("LimsCiefResult", null=True, blank=True, on_delete=models.SET_NULL)
    hcp_result = models.OneToOneField("LimsHcpResult", null=True, blank=True, on_delete=models.SET_NULL)
    proa_result = models.OneToOneField("LimsProaResult", null=True, blank=True, on_delete=models.SET_NULL)

    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="in_progress")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sample_id} ({self.project_id})"

    class Meta:
        db_table = 'lims_sample_analysis'
        # indexes = [
        #     models.Index(fields=['sample_id']),
        # ]

#Sample Set Creation and tables for monitoring analysis progress
class LimsSampleSet(models.Model):
    """Represents a grouped collection of samples"""
    id = models.AutoField(primary_key=True)
    set_name = models.CharField(max_length=200, unique=True)  # e.g., "PROJ001_SIP001_MP"
    project_id = models.CharField(max_length=100)
    sip_number = models.CharField(max_length=50, null=True, blank=True)
    development_stage = models.CharField(max_length=50, null=True, blank=True)

    # Metadata
    sample_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Status tracking
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'lims_sample_sets'
        unique_together = ['project_id', 'sip_number', 'development_stage']
        managed = True


class LimsSampleSetMembership(models.Model):
    """Links individual samples to sample sets"""
    sample_set = models.ForeignKey(LimsSampleSet, on_delete=models.CASCADE, related_name='members')
    sample = models.ForeignKey(LimsSampleAnalysis, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lims_sample_set_membership'
        unique_together = ['sample_set', 'sample']
        managed = True


class LimsAnalysisRequest(models.Model):
    """Track analysis requests for sample sets"""
    sample_set = models.ForeignKey(LimsSampleSet, on_delete=models.CASCADE, related_name='analysis_requests')
    analysis_type = models.CharField(max_length=50)  # SEC, Titer, etc.
    requested_by = models.CharField(max_length=100)
    requested_at = models.DateTimeField(auto_now_add=True)
    priority = models.IntegerField(default=1)
    status = models.CharField(max_length=50, default='requested')
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'lims_analysis_requests'
        managed = True

# Lims Dn Assignment
class LimsDnAssignment(models.Model):
    dn = models.BigIntegerField(primary_key=True)
    # Link to optional source material used in this DN
    source_material = models.ForeignKey(
        "LimsSourceMaterial",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="used_in_dn_assignments"
    )

    project_id = models.CharField(max_length=255)
    unit_operation = models.CharField(max_length=100, null=True, blank=True)
    scouting_details = models.CharField(max_length=255,null=True, blank=True)
    study_name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="dn_created_by")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="dn_assigned_to")
    experiment_purpose = models.TextField()
    load_volume = models.FloatField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lims_dn_assignment'


# # --- Lims Source Material Table ---
class LimsSourceMaterial(models.Model):
    # The resulting sample from this source material prep
    sm_id = models.BigIntegerField(primary_key=True)  # e.g., "SM123"
    project_id = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    resulting_sample = models.OneToOneField(
        "LimsSampleAnalysis",
        on_delete=models.CASCADE,
        related_name="source_material_record"
    )

    # Input samples used to create this source material
    samples = models.ManyToManyField(
        "LimsSampleAnalysis",
        related_name="used_in_source_materials"
    )

    source_description = models.TextField(null=True, blank=True)
    source_volume = models.FloatField(null=True, blank=True)

    notes = models.TextField(null=True, blank=True)

    final_conductivity = models.FloatField(null=True, blank=True)
    final_pH = models.FloatField(null=True, blank=True)
    final_concentration = models.FloatField(null=True, blank=True)
    final_total_volume = models.FloatField(null=True, blank=True)

    created_by = models.ForeignKey(User, related_name="created_source_materials", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, related_name="updated_source_materials", on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lims_source_material'


class LimsSourceMaterialStep(models.Model):
    source_material = models.ForeignKey(LimsSourceMaterial, on_delete=models.CASCADE)
    step_number = models.IntegerField()
    process = models.CharField(max_length=100)  # e.g., "Concentration"
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'lims_source_material_step'


# --- Result Tables ---
class LimsSecResult(models.Model):
    sample_id = models.OneToOneField(LimsSampleAnalysis, on_delete=models.CASCADE, primary_key=True)
    main_peak = models.FloatField(blank=True, null=True)
    hmw = models.FloatField(blank=True, null=True)
    lmw = models.FloatField(blank=True, null=True)
    peak_data = models.JSONField(blank=True, null=True)
    qc_pass = models.BooleanField(default=True)

    report = models.ForeignKey("Report", null=True, blank=True, on_delete=models.SET_NULL)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="in_progress")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lims_sec_result'


class LimsTiterResult(models.Model):
    sample_id = models.OneToOneField(LimsSampleAnalysis, on_delete=models.CASCADE, primary_key=True)
    titer = models.FloatField(null=True, blank=True)
    qc_pass = models.BooleanField(default=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="in_progress")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lims_titer_result'


class LimsMassCheckResult(models.Model):
    sample_id = models.OneToOneField(LimsSampleAnalysis, on_delete=models.CASCADE, primary_key=True)
    expected_mass = models.FloatField()
    observed_mass = models.FloatField()
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="in_progress")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lims_mass_check_result'


class LimsReleasedGlycanResult(models.Model):
    sample_id = models.OneToOneField(LimsSampleAnalysis, on_delete=models.CASCADE, primary_key=True)
    glycan_profile = models.JSONField()
    major_species = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="in_progress")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lims_released_glycan_result'


class LimsHcpResult(models.Model):
    sample_id = models.OneToOneField(LimsSampleAnalysis, on_delete=models.CASCADE, primary_key=True)
    hcp_level = models.FloatField()
    unit = models.CharField(max_length=20, default="ng/mg")
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="in_progress")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lims_hcp_result'


class LimsProaResult(models.Model):
    sample_id = models.OneToOneField(LimsSampleAnalysis, on_delete=models.CASCADE, primary_key=True)
    proa_level = models.FloatField()
    unit = models.CharField(max_length=20, default="ng/mg")
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="in_progress")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lims_proa_result'


class LimsCiefResult(models.Model):
    sample_id = models.OneToOneField(LimsSampleAnalysis, on_delete=models.CASCADE, primary_key=True)
    main_peak = models.FloatField()
    acidic_variants = models.FloatField()
    basic_variants = models.FloatField()
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="in_progress")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lims_cief_result'


class LimsCeSdsResult(models.Model):
    sample_id = models.OneToOneField(LimsSampleAnalysis, on_delete=models.CASCADE, primary_key=True)
    purity = models.FloatField()
    band_pattern = models.JSONField(blank=True, null=True)
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="in_progress")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lims_ce_sds_result'

#
# #PD Variables
# class LimsPDSamples(models.Model):
#     id = models.AutoField(primary_key=True)  # Ensure primary key is explicitly set
#     result_id = models.IntegerField()
#     pd_number = models.CharField(max_length=255)  # PD#
#     sample_volume_ul = models.FloatField()  # Sample volume (uL)
#     identifier = models.CharField(max_length=255)  # Identifier (SM/DN)
#     description_volume = models.TextField()  # Description + Volume
#     a280_date = models.DateField(null=True, blank=True)  # A280 date
#     concentration_mg_ml = models.FloatField(null=True, blank=True)  # mg/ml
#     sec_date = models.DateField(null=True, blank=True)  # SEC date
#     hmw_percentage = models.FloatField(null=True, blank=True)
#     mp_percentage = models.FloatField(null=True, blank=True)  # MP%
#     lmw_percentage = models.FloatField(null=True, blank=True)
#     sec_total_area = models.FloatField(null=True, blank=True)
#     sec_injection_ug = models.FloatField(null=True, blank=True)  # Injection (ug)
#     sec_dilution = models.FloatField(null=True, blank=True)  # Dilution
#     sec_load_volume_ul = models.FloatField(null=True, blank=True)  # SEC load volume (uL)
#     hplc_proa_titer_mg_ml = models.FloatField(null=True, blank=True)  # HPLC-ProA Titer (mg/mL)
#     hcp_ppm = models.FloatField(null=True, blank=True)  # HCP (ppm)
#     proa_ppm = models.FloatField(null=True, blank=True)  # ProA (ppm)
#     dna_ppm = models.FloatField(null=True, blank=True)  # DNA (ppm)
#     akta_fraction_id = models.CharField(max_length=255, null=True, blank=True)  # AKTA Fraction ID
#
#     class Meta:
#         db_table = 'lims_pd_samples'
#
