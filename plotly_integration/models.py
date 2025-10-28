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
    analysis_type = models.IntegerField(null=True, blank=True)  # 1:SEC,2:PROA, 3:CESDS,4:CIEF
    sample_name = models.CharField(max_length=255, null=True, blank=True)
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
    unit_step = models.BigIntegerField(null=True, blank=True)  # 1=UF1, 2=UF2, 3=DF1, 4=DF2, 5=Rinse
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
    dilution_factor = models.FloatField(null=True, blank=True, default=1.0)

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
    sample_id = models.CharField(max_length=100)
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
        # unique_together = ('date_time', 'sample_id')  # Enforce uniqueness


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
    settings = models.JSONField(null=True, blank=True)

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
        indexes = [
            # models.Index(fields=['id']),  # Remove this - Primary key is already indexed
            models.Index(fields=['sample_id_full']),
            models.Index(fields=['acquisition_datetime']),
            models.Index(fields=['sample_set_id']),  # Add this for grouping queries
        ]

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
        indexes = [
            models.Index(fields=['metadata']),  # Use 'metadata' not 'metadata_id'
            models.Index(fields=['time_min']),
            models.Index(fields=['metadata', 'time_min']),  # Composite index
        ]
        ordering = ['time_min']

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
    settings = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'cief_report'
        indexes = [
            models.Index(fields=['date_created']),
            models.Index(fields=['user_id']),
            models.Index(fields=['project_id']),
        ]


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


# USP Sample Sets Management Models
class UspSampleSet(models.Model):
    """Represents a grouped collection of USP samples - grouped by project and reactor type"""
    id = models.AutoField(primary_key=True)
    set_name = models.CharField(max_length=200, unique=True)  # e.g., "PROJ001_Bioreactor_R1"
    project_id = models.CharField(max_length=100)
    reactor_type = models.CharField(max_length=50)  # e.g., "Bioreactor", "Shake Flask", "Ambr250"
    
    # Additional USP-specific metadata
    experiment_number = models.IntegerField(null=True, blank=True)
    culture_duration = models.IntegerField(null=True, blank=True)
    vessel_type = models.CharField(max_length=50, null=True, blank=True)
    cell_line = models.CharField(max_length=100, null=True, blank=True)

    # Common metadata
    sample_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Status tracking
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'usp_sample_sets'
        unique_together = ['project_id', 'reactor_type', 'experiment_number']
        managed = True

    def __str__(self):
        return f"{self.set_name} - {self.project_id} ({self.reactor_type})"


class UspSampleSetMembership(models.Model):
    """Links individual USP samples to USP sample sets"""
    sample_set = models.ForeignKey(UspSampleSet, on_delete=models.CASCADE, related_name='members')
    sample = models.ForeignKey('LimsUpstreamSamples', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usp_sample_set_membership'
        unique_together = ['sample_set', 'sample']
        managed = True


class UspAnalysisRequest(models.Model):
    """Track analysis requests for USP sample sets"""
    sample_set = models.ForeignKey(UspSampleSet, on_delete=models.CASCADE, related_name='analysis_requests')
    analysis_type = models.CharField(max_length=50)  # SEC, AKTA, Titer, Viability, Metabolites, etc.
    requested_by = models.CharField(max_length=100)
    requested_at = models.DateTimeField(auto_now_add=True)
    priority = models.IntegerField(default=1)
    status = models.CharField(max_length=50, default='requested')
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'usp_analysis_requests'
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

    # Mass Balance fields
    input_volume = models.FloatField(null=True, blank=True, help_text="Input volume in mL")
    input_concentration = models.FloatField(null=True, blank=True, help_text="Input concentration in mg/mL")
    output_volume = models.FloatField(null=True, blank=True, help_text="Output volume in mL")
    output_concentration = models.FloatField(null=True, blank=True, help_text="Output concentration in mg/mL")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lims_dn_assignment'


# Experimental Set Management Models
class ExperimentalSet(models.Model):
    STUDY_TYPE_CHOICES = [
        ('cex', 'CEX Optimization'),
        ('aex', 'AEX Optimization'),
        ('hic', 'HIC Study'),
        ('prota', 'Protein A'),
        ('custom', 'Custom')
    ]
    
    name = models.CharField(max_length=255, unique=True)
    project_id = models.CharField(max_length=255)
    study_type = models.CharField(max_length=50, choices=STUDY_TYPE_CHOICES, default='custom')
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_experimental_sets")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'experimental_set'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.project_id})"


class ExperimentalSetData(models.Model):
    experimental_set = models.ForeignKey(ExperimentalSet, on_delete=models.CASCADE, related_name='experimental_data')
    dn_assignment = models.ForeignKey(LimsDnAssignment, on_delete=models.CASCADE)
    
    # Process Parameters
    resin = models.CharField(max_length=100, blank=True)
    cv_ml = models.FloatField(null=True, blank=True, verbose_name='CV (mL)')
    residence_time = models.FloatField(null=True, blank=True, verbose_name='Residence Time (min)')
    
    # Buffer Conditions
    elution_condition = models.CharField(max_length=200, blank=True)
    eq = models.CharField(max_length=100, blank=True)
    wash_condition = models.CharField(max_length=200, blank=True)
    
    # Load Parameters
    load_density = models.FloatField(null=True, blank=True, verbose_name='Load Density (mg/mL)')
    product_required = models.FloatField(null=True, blank=True, verbose_name='Product Required (mg)')
    load_volume = models.FloatField(null=True, blank=True, verbose_name='Load Volume (mL)')
    
    # Results
    eluate_volume = models.FloatField(null=True, blank=True, verbose_name='Eluate Volume (mL)')
    eluate_concentration = models.FloatField(null=True, blank=True, verbose_name='Eluate Concentration (mg/mL)')
    eluate_amount = models.FloatField(null=True, blank=True, verbose_name='Eluate Amount (mg)')
    yield_percent = models.FloatField(null=True, blank=True, verbose_name='Yield (%)')
    
    # Analytics
    mp_sec_percent = models.FloatField(null=True, blank=True, verbose_name='% MP SEC')
    ppm_hcp = models.FloatField(null=True, blank=True, verbose_name='PPM HCP')
    ppb_dna = models.FloatField(null=True, blank=True, verbose_name='PPB DNA')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'experimental_set_data'
        unique_together = ('experimental_set', 'dn_assignment')
        ordering = ['dn_assignment__dn']
    
    def __str__(self):
        return f"{self.experimental_set.name} - DN{self.dn_assignment.dn:03d}"


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

    report = models.ForeignKey("Report", null=True, blank=True, on_delete=models.SET_NULL)

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
    band_pattern = models.JSONField(blank=True, null=True)  # Store band pattern data as JSON

    report = models.ForeignKey("CIEFReport", null=True, blank=True, on_delete=models.SET_NULL)

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

    report = models.ForeignKey("CESDSReport", null=True, blank=True, on_delete=models.SET_NULL)

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


# =====================================================
# DASGIP Bioreactor Models (USP - Upstream Processing)
# =====================================================

# Simplified DASGIP Models - Two table approach
class USPBioreactorRun(models.Model):
    """Simplified metadata table for bioreactor runs - one row per UP number"""
    up_number = models.CharField(max_length=50, primary_key=True, help_text="UP Number (Primary Key)")
    
    # File info
    file_name = models.CharField(max_length=255, help_text="Original CSV filename")
    file_path = models.TextField(help_text="Path to uploaded file")
    
    # Run metadata
    project_name = models.CharField(max_length=255, blank=True, help_text="DASGIP project name")
    unit_number = models.IntegerField(help_text="DASGIP unit number (1, 3, 4, 7, 8, etc.)")
    setup_name = models.CharField(max_length=255, blank=True, help_text="Setup description")
    
    # Timestamps
    start_timestamp = models.DateTimeField(help_text="Run start time")
    stop_timestamp = models.DateTimeField(help_text="Run stop time")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Optional metadata
    comment = models.TextField(blank=True, help_text="Run notes/comments")
    host = models.CharField(max_length=100, blank=True, help_text="DASGIP host system")
    
    def __str__(self):
        return f"{self.up_number} - Unit {self.unit_number}"
    
    class Meta:
        db_table = 'usp_bioreactor_runs'
        verbose_name = "Bioreactor Run"
        verbose_name_plural = "Bioreactor Runs"


class USPTimeSeriesData(models.Model):
    """Time series data for bioreactor parameters"""
    run = models.ForeignKey(USPBioreactorRun, on_delete=models.CASCADE, related_name='timeseries_data')
    timestamp = models.DateTimeField(help_text="Data timestamp")
    duration = models.FloatField(null=True, blank=True, help_text="Duration from start (hours)")
    
    # Process parameters based on PROCESS_PARAMETERS
    # Dissolved Oxygen
    do_pv = models.FloatField(null=True, blank=True, help_text="DO Process Value (% DO)")
    do_sp = models.FloatField(null=True, blank=True, help_text="DO Setpoint (% DO)")
    do_out = models.FloatField(null=True, blank=True, help_text="DO Controller Output (%)")
    
    # pH
    ph_pv = models.FloatField(null=True, blank=True, help_text="pH Process Value")
    ph_sp = models.FloatField(null=True, blank=True, help_text="pH Setpoint")
    ph_out = models.FloatField(null=True, blank=True, help_text="pH Controller Output (%)")
    
    # Temperature
    temp_pv = models.FloatField(null=True, blank=True, help_text="Temperature Process Value (°C)")
    temp_sp = models.FloatField(null=True, blank=True, help_text="Temperature Setpoint (°C)")
    temp_out = models.FloatField(null=True, blank=True, help_text="Temperature Controller Output (%)")
    
    # Agitation Speed
    rpm_pv = models.FloatField(null=True, blank=True, help_text="Agitation Speed Process Value (RPM)")
    rpm_sp = models.FloatField(null=True, blank=True, help_text="Agitation Speed Setpoint (RPM)")
    
    # Volume
    volume_pv = models.FloatField(null=True, blank=True, help_text="Reactor Volume (mL)")
    
    # Air Flow
    air_flow_pv = models.FloatField(null=True, blank=True, help_text="Air Flow Process Value (sL/h)")
    air_flow_sp = models.FloatField(null=True, blank=True, help_text="Air Flow Setpoint (sL/h)")
    
    # Feed A Flow
    feed_a_pv = models.FloatField(null=True, blank=True, help_text="Feed A Flow Process Value (mL/h)")
    feed_a_sp = models.FloatField(null=True, blank=True, help_text="Feed A Flow Setpoint (mL/h)")
    
    # Feed B Flow
    feed_b_pv = models.FloatField(null=True, blank=True, help_text="Feed B Flow Process Value (mL/h)")
    feed_b_sp = models.FloatField(null=True, blank=True, help_text="Feed B Flow Setpoint (mL/h)")
    
    # O2 Concentration
    o2_conc_pv = models.FloatField(null=True, blank=True, help_text="O2 Concentration Process Value (%)")
    o2_conc_sp = models.FloatField(null=True, blank=True, help_text="O2 Concentration Setpoint (%)")
    
    # CO2 Concentration
    co2_conc_pv = models.FloatField(null=True, blank=True, help_text="CO2 Concentration Process Value (%)")
    co2_conc_sp = models.FloatField(null=True, blank=True, help_text="CO2 Concentration Setpoint (%)")
    
    def __str__(self):
        return f"{self.run.up_number} - {self.timestamp}"
    
    class Meta:
        db_table = 'usp_timeseries_data'
        verbose_name = "Time Series Data"
        verbose_name_plural = "Time Series Data"
        indexes = [
            models.Index(fields=['run', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['run', 'timestamp']


# =====================================================
# COMPLETE FORMULATION DATABASE - 4 TABLES ONLY
# =====================================================

class FormulationExperiment(models.Model):
    """Master experiment table"""

    experiment_id = models.CharField(max_length=50, unique=True, primary_key=True, help_text="e.g., FD-003")
    name = models.CharField(max_length=200, help_text="Experiment name/description")
    molecule = models.CharField(max_length=100, help_text="Molecule/Protein name")
    target_concentration_mg_ml = models.FloatField(default=50.0, help_text="Target protein concentration")
    start_date = models.DateField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'formulation_experiment'
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.experiment_id}: {self.name}"


class FormulationMatrix(models.Model):
    """Each formulation design (buffer matrix)"""

    formulation_id = models.AutoField(primary_key=True)
    experiment = models.ForeignKey(FormulationExperiment, on_delete=models.CASCADE, related_name='formulations')
    formulation_number = models.IntegerField(help_text="Formulation number (1, 2, 3...)")
    target_ph = models.FloatField(help_text="Target pH")
    osmolality = models.FloatField(null=True, blank=True, help_text="Target osmolality (mOsm/kg)")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'formulation_matrix'
        unique_together = ('experiment', 'formulation_number')
        ordering = ['experiment', 'formulation_number']

    def get_formulation_code(self):
        return f"{self.experiment_id}-F{self.formulation_number:02d}"

    def __str__(self):
        return f"{self.experiment_id}-F{self.formulation_number:02d}"


class FormulationComponent(models.Model):
    """Flexible components for each formulation"""

    COMPONENT_TYPE = [
        ('buffer', 'Buffer'),
        ('excipient', 'Excipient'),
        ('surfactant', 'Surfactant'),
        ('salt', 'Salt'),
        ('sugar', 'Sugar/Polyol'),
        ('amino_acid', 'Amino Acid'),
        ('preservative', 'Preservative'),
        ('other', 'Other')
    ]

    CONCENTRATION_UNIT = [
        ('mg/mL', 'mg/mL'),
        ('mM', 'mM'),
        ('M', 'M'),
        ('g/L', 'g/L'),
        ('%', '% (w/v)'),
        ('% v/v', '% (v/v)'),
    ]

    component_id = models.AutoField(primary_key=True)
    formulation = models.ForeignKey(FormulationMatrix, on_delete=models.CASCADE, related_name='components')
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPE)
    name = models.CharField(max_length=100, help_text="e.g., Histidine, Sucrose, Arginine HCl, PS80")
    concentration = models.FloatField()
    unit = models.CharField(max_length=10, choices=CONCENTRATION_UNIT, default='mg/mL')

    class Meta:
        db_table = 'formulation_component'
        unique_together = ('formulation', 'name')
        ordering = ['formulation', 'component_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.concentration} {self.unit})"


class FormulationSample(models.Model):
    """Combined sample info + all analytical results in ONE table"""

    STORAGE_CONDITIONS = [
        ('FT', 'Freeze/Thaw'),
        ('25C', '25°C'),
        ('40C', '40°C'),
        ('4C', '4°C'),
        ('-80C', '-80°C'),
    ]

    # Sample Identity
    sample_id = models.CharField(max_length=50, primary_key=True, help_text="e.g., FD-003-001")
    formulation = models.ForeignKey(FormulationMatrix, on_delete=models.CASCADE, related_name='samples')

    # Storage and Timepoint
    storage_condition = models.CharField(max_length=10, choices=STORAGE_CONDITIONS)
    pull_day = models.IntegerField(null=True, blank=True, help_text="Day of pull (e.g., 7, 14, 30)")
    time_point_months = models.FloatField(help_text="Time point in months (e.g., 0, 1, 3, 6, 12)")
    pull_date = models.DateField(null=True, blank=True)

    # Physical Properties & Appearance
    appearance = models.CharField(max_length=200, blank=True, help_text="Visual appearance")
    concentration_mg_ml = models.FloatField(null=True, blank=True, help_text="Measured protein concentration")
    ph_measured = models.FloatField(null=True, blank=True, help_text="Measured pH")
    osmolality_measured = models.FloatField(null=True, blank=True, help_text="Measured osmolality (mOsm/kg)")

    # SEC Results
    sec_result_id = models.CharField(max_length=100, null=True, blank=True, help_text="HPLC/SEC Result ID")
    hmw = models.FloatField(null=True, blank=True, help_text="High Molecular Weight (%)")
    main = models.FloatField(null=True, blank=True, help_text="Main Peak (%)")
    lmw = models.FloatField(null=True, blank=True, help_text="Low Molecular Weight (%)")
    total_area = models.FloatField(null=True, blank=True, help_text="Total peak area")

    # Thermal Stability
    tm_celsius = models.FloatField(null=True, blank=True, help_text="Melting temperature (°C)")
    scattering_onset = models.FloatField(null=True, blank=True, help_text="Light scattering onset temperature (°C)")

    # Metadata
    analysis_date = models.DateField(null=True, blank=True)
    analyst = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'formulation_sample'
        ordering = ['formulation__experiment', 'formulation__formulation_number', 'time_point_months',
                    'storage_condition']
        unique_together = ('formulation', 'storage_condition', 'time_point_months')

    def __str__(self):
        return f"{self.sample_id} - {self.storage_condition} @ {self.time_point_months}M"

    def save(self, *args, **kwargs):
        # Auto-generate sample_id if not provided
        if not self.sample_id:
            base_id = f"{self.formulation.experiment_id}-{self.formulation.formulation_number:03d}"
            condition_code = self.storage_condition.replace('°C', '').replace('/', '')
            time_code = f"{int(self.time_point_months)}M" if self.time_point_months else "T0"
            self.sample_id = f"{base_id}-{condition_code}-{time_code}"
        super().save(*args, **kwargs)


# CLD Project Management Models
class CLDProject(models.Model):
    """Model for tracking CLD projects with Gantt chart visualization"""
    HARVEST_TYPE_CHOICES = [
        ('24_deepwell', '24 Deepwell'),
        ('48_deepwell', '48 Deepwell'),
        ('shake_flask', 'Shake Flask'),
        ('beacon', 'Beacon'),
    ]

    PURIFICATION_TYPE_CHOICES = [
        ('PROA', 'Protein A'),
        ('Kappa', 'Kappa'),
        ('Lambda', 'Lambda'),
        ('G_protein', 'G Protein'),
        ('L_protein', 'L Protein'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('Planning', 'Planning'),
        ('In Progress', 'In Progress'),
        ('Complete', 'Complete'),
    ]

    TRANSFECTION_TYPE_CHOICES = [
        ('Lonza', 'Lonza'),
        ('BTX', 'BTX'),
    ]

    OPTIONS_CHOICES = [
        ('Minipool', 'Minipool'),
        ('Bulkpool', 'Bulkpool'),
        ('Minipool+Bulkpool', 'Minipool+Bulkpool'),
    ]

    id = models.AutoField(primary_key=True)
    project_id = models.CharField(max_length=100, default='CLD-2025-001')  # Project ID field
    sip_number = models.CharField(max_length=100, default='SIP-001')  # SIP Number
    project_number = models.CharField(max_length=100)  # Keep for backward compatibility
    number_of_samples = models.IntegerField()

    # Transfection details
    transfection_start_date = models.DateField(null=True, blank=True)  # New primary date field
    transfection_type = models.CharField(max_length=20, choices=TRANSFECTION_TYPE_CHOICES, default='Lonza')
    transfection_amount_mg = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # mg
    options = models.CharField(max_length=50, choices=OPTIONS_CHOICES, default='Minipool')

    # Legacy fields (keep for backward compatibility)
    start_date = models.DateField(null=True, blank=True)
    target_harvest_date = models.DateField(null=True, blank=True)
    harvest_type = models.CharField(max_length=50, choices=HARVEST_TYPE_CHOICES, null=True, blank=True)
    purification_type = models.CharField(max_length=50, choices=PURIFICATION_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Planning')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'cld_project'
        ordering = ['-created_date', '-start_date']
        indexes = [
            models.Index(fields=['project_number', '-created_date']),
            models.Index(fields=['status', '-start_date']),
        ]

    def __str__(self):
        return f"{self.project_number} - {self.start_date}"

    def days_to_harvest(self):
        """Calculate days remaining to harvest"""
        from datetime import date
        if self.target_harvest_date:
            delta = self.target_harvest_date - date.today()
            return delta.days
        return None

    def project_duration(self):
        """Calculate total project duration in days"""
        if self.start_date and self.target_harvest_date:
            delta = self.target_harvest_date - self.start_date
            return delta.days
        return None


class CLDAnalytics(models.Model):
    """Model for tracking analytics requirements and status for CLD projects"""
    ANALYSIS_TYPE_CHOICES = [
        ('SEC', 'Size Exclusion Chromatography'),
        ('Titer', 'Titer'),
        ('Octet', 'Octet'),
        ('CE-SDS', 'CE-SDS'),
        ('cIEF', 'cIEF'),
        ('LCMS', 'LC-MS'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Complete', 'Complete'),
        ('Reported', 'Reported'),
    ]

    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(CLDProject, on_delete=models.CASCADE, related_name='analytics')
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPE_CHOICES)
    required = models.BooleanField(default=True)
    scheduled_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cld_analytics'
        unique_together = ('project', 'analysis_type')
        ordering = ['project', 'scheduled_date', 'analysis_type']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['scheduled_date', 'status']),
        ]

    def __str__(self):
        return f"{self.project.project_number} - {self.analysis_type} - {self.status}"

    def days_until_scheduled(self):
        """Calculate days until scheduled analysis"""
        from datetime import date
        if self.scheduled_date:
            delta = self.scheduled_date - date.today()
            return delta.days
        return None


class CLDProcessStep(models.Model):
    """Model for tracking individual process steps in CLD projects"""
    STEP_TYPE_CHOICES = [
        ('Transfection', 'Transfection'),
        ('mP/BP', 'mP/BP'),
        ('Recovery', 'Recovery'),
        ('Beacon', 'Beacon'),
        ('Grow Up', 'Grow Up'),
        ('Cydem', 'Cydem'),
        ('Harvest', 'Harvest'),
        ('Purification', 'Purification'),
        ('Analytics', 'Analytics'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Complete', 'Complete'),
        ('Skipped', 'Skipped'),
    ]

    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(CLDProject, on_delete=models.CASCADE, related_name='process_steps')
    step_name = models.CharField(max_length=50, choices=STEP_TYPE_CHOICES)
    step_order = models.PositiveIntegerField()  # Order in the process
    planned_duration_days = models.PositiveIntegerField()  # Planned duration
    actual_duration_days = models.PositiveIntegerField(null=True, blank=True)  # Actual duration
    planned_start_date = models.DateField(null=True, blank=True)  # Calculated
    actual_start_date = models.DateField(null=True, blank=True)  # When actually started
    planned_end_date = models.DateField(null=True, blank=True)  # Calculated
    actual_end_date = models.DateField(null=True, blank=True)  # When actually completed
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    notes = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cld_process_step'
        unique_together = ('project', 'step_name')
        ordering = ['project', 'step_order']
        indexes = [
            models.Index(fields=['project', 'step_order']),
            models.Index(fields=['status', 'planned_start_date']),
        ]

    def __str__(self):
        return f"{self.project.project_id} - {self.step_name} ({self.status})"

    def calculate_dates(self):
        """Calculate planned dates based on project start and previous steps"""
        from datetime import timedelta

        # Get the project's transfection start date
        base_date = self.project.transfection_start_date

        # Get all previous steps in order
        previous_steps = CLDProcessStep.objects.filter(
            project=self.project,
            step_order__lt=self.step_order
        ).order_by('step_order')

        # Calculate start date based on previous steps
        current_date = base_date
        for prev_step in previous_steps:
            duration = prev_step.actual_duration_days if prev_step.actual_duration_days else prev_step.planned_duration_days
            current_date += timedelta(days=duration)

        self.planned_start_date = current_date
        self.planned_end_date = current_date + timedelta(days=self.planned_duration_days)

    def save(self, *args, **kwargs):
        # Auto-calculate dates when saving
        self.calculate_dates()

        # Auto-calculate actual duration if step is complete and we have dates
        if self.status == 'Complete' and not self.actual_duration_days:
            self.auto_calculate_duration()

        super().save(*args, **kwargs)

        # Recalculate subsequent steps if this step's duration changed
        self.recalculate_subsequent_steps()

    def auto_calculate_duration(self):
        """Auto-calculate actual duration when step is marked complete"""
        from datetime import date, timedelta

        # Determine start date (end of previous step or project start)
        previous_step = CLDProcessStep.objects.filter(
            project=self.project,
            step_order__lt=self.step_order
        ).order_by('-step_order').first()

        if previous_step and previous_step.actual_end_date:
            start_date = previous_step.actual_end_date
        elif previous_step and previous_step.status == 'Complete':
            # Calculate from previous step's completion
            start_date = previous_step.planned_start_date + timedelta(days=previous_step.planned_duration_days)
        else:
            start_date = self.project.transfection_start_date

        # Set actual start date if not already set
        if not self.actual_start_date:
            self.actual_start_date = start_date

        # Set actual end date to today if not set and calculate duration
        if not self.actual_end_date:
            self.actual_end_date = date.today()

        # Calculate actual duration
        if self.actual_start_date and self.actual_end_date:
            duration = (self.actual_end_date - self.actual_start_date).days
            self.actual_duration_days = max(1, duration)  # Minimum 1 day

    def recalculate_subsequent_steps(self):
        """Recalculate dates for all subsequent steps when this step's duration changes"""
        subsequent_steps = CLDProcessStep.objects.filter(
            project=self.project,
            step_order__gt=self.step_order
        ).order_by('step_order')

        for step in subsequent_steps:
            step.calculate_dates()
            step.save_without_recalculation()

    def save_without_recalculation(self):
        """Save without triggering recalculation to avoid infinite loops"""
        super().save()


class CLDProcessTemplate(models.Model):
    """Model for storing reusable process templates"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cld_process_template'
        ordering = ['-created_date']

    def __str__(self):
        return self.name


class CLDProcessTemplateStep(models.Model):
    """Model for storing template step definitions"""
    STEP_TYPE_CHOICES = [
        ('Transfection', 'Transfection'),
        ('mP/BP', 'mP/BP'),
        ('Recovery', 'Recovery'),
        ('Beacon', 'Beacon'),
        ('Grow Up', 'Grow Up'),
        ('Cydem', 'Cydem'),
        ('Harvest', 'Harvest'),
        ('Purification', 'Purification'),
        ('Analytics', 'Analytics'),
    ]

    id = models.AutoField(primary_key=True)
    template = models.ForeignKey(CLDProcessTemplate, on_delete=models.CASCADE, related_name='template_steps')
    step_name = models.CharField(max_length=50, choices=STEP_TYPE_CHOICES)
    step_order = models.PositiveIntegerField()
    default_duration_days = models.PositiveIntegerField()
    is_required = models.BooleanField(default=True)

    class Meta:
        db_table = 'cld_process_template_step'
        unique_together = ('template', 'step_name')
        ordering = ['template', 'step_order']

    def __str__(self):
        return f"{self.template.name} - {self.step_name} ({self.default_duration_days}d)"


# USP Experiment Management Models
class USPExperiment(models.Model):
    """Model for tracking USP experiments with bioreactors and shake flasks"""

    STATUS_CHOICES = [
        ('Planning', 'Planning'),
        ('In Progress', 'In Progress'),
        ('Complete', 'Complete'),
        ('On Hold', 'On Hold'),
        ('Cancelled', 'Cancelled'),
    ]

    EXPERIMENT_TYPE_CHOICES = [
        ('Conformance', 'Conformance'),
        ('pH_Test', 'pH Test'),
        ('Temperature_Test', 'Temperature Test'),
        ('Media_Optimization', 'Media Optimization'),
        ('Feed_Optimization', 'Feed Optimization'),
        ('Scale_Up', 'Scale Up'),
        ('Process_Characterization', 'Process Characterization'),
        ('Other', 'Other'),
    ]

    id = models.AutoField(primary_key=True)
    experiment_id = models.CharField(max_length=100, unique=True)
    experiment_name = models.CharField(max_length=255)
    project_id = models.CharField(max_length=100, blank=True, null=True, help_text="Project identifier")
    description = models.TextField(blank=True, null=True)
    experiment_type = models.CharField(max_length=50, choices=EXPERIMENT_TYPE_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Planning')
    start_date = models.DateField()
    target_end_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'usp_experiment'
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.experiment_id} - {self.experiment_name}"


class USPProcessStep(models.Model):
    """Model for tracking process steps (can contain multiple vessels)"""
    STEP_TYPE_CHOICES = [
        ('Seed_Train', 'Seed Train'),
        ('Bioreactor', 'Bioreactor'),
        ('Shake_Flask', 'Shake Flask'),
        ('Bioreactor_and_Shake_Flask', 'Bioreactor and Shake Flask'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Complete', 'Complete'),
        ('Skipped', 'Skipped'),
    ]

    id = models.AutoField(primary_key=True)
    experiment = models.ForeignKey(USPExperiment, on_delete=models.CASCADE, related_name='process_steps')
    step_name = models.CharField(max_length=100)
    step_type = models.CharField(max_length=50, choices=STEP_TYPE_CHOICES)
    step_order = models.PositiveIntegerField()
    planned_duration_days = models.PositiveIntegerField()
    actual_duration_days = models.PositiveIntegerField(null=True, blank=True)
    planned_start_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    planned_end_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    notes = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usp_process_step'
        unique_together = ('experiment', 'step_order')
        ordering = ['experiment', 'step_order']

    def save(self, *args, **kwargs):
        """Calculate planned dates based on previous steps"""
        if not self.planned_start_date and self.experiment:
            previous_steps = USPProcessStep.objects.filter(
                experiment=self.experiment,
                step_order__lt=self.step_order
            ).order_by('-step_order')

            if previous_steps.exists():
                prev_step = previous_steps.first()
                self.planned_start_date = prev_step.planned_end_date or prev_step.planned_start_date
            else:
                self.planned_start_date = self.experiment.start_date

        if self.planned_start_date and self.planned_duration_days and not self.planned_end_date:
            from datetime import timedelta
            self.planned_end_date = self.planned_start_date + timedelta(days=self.planned_duration_days)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.experiment.experiment_id} - {self.step_name} ({self.step_type})"


class USPSeedTrain(models.Model):
    """Model for tracking seed train samples (thawed cells in T-flasks or small shake flasks)"""
    SEED_VESSEL_TYPE_CHOICES = [
        ('T25', 'T25 Flask'),
        ('T75', 'T75 Flask'),
        ('T175', 'T175 Flask'),
        ('T225', 'T225 Flask'),
        ('125mL_SF', '125mL Shake Flask'),
        ('250mL_SF', '250mL Shake Flask'),
        ('500mL_SF', '500mL Shake Flask'),
    ]

    POOL_OR_CLONE_CHOICES = [
        ('Pool', 'Pool'),
        ('Clone', 'Clone'),
    ]

    id = models.AutoField(primary_key=True)
    process_step = models.ForeignKey(USPProcessStep, on_delete=models.CASCADE, related_name='seed_trains')
    seed_train_id = models.CharField(max_length=100, unique=True)  # UPST####
    vessel_type = models.CharField(max_length=20, choices=SEED_VESSEL_TYPE_CHOICES)
    thaw_date = models.DateField()
    start_volume = models.FloatField(help_text="mL")  # Renamed from culture_volume
    cell_line = models.CharField(max_length=100)
    media_type = models.CharField(max_length=100)
    media_prep = models.ForeignKey('USPMediaPrep', on_delete=models.SET_NULL, null=True, blank=True, related_name='seed_trains_used')
    passage_number = models.IntegerField(null=True, blank=True)
    vial_id = models.CharField(max_length=100, blank=True, null=True)
    viability_at_thaw = models.FloatField(null=True, blank=True, help_text="percentage")
    cell_density_at_thaw = models.FloatField(null=True, blank=True, help_text="cells/mL")
    notes = models.TextField(blank=True, null=True)

    # Excel template fields
    bank_age = models.CharField(max_length=50, blank=True, null=True, help_text='e.g., P4, P5')
    pool_or_clone = models.CharField(max_length=50, blank=True, null=True, choices=POOL_OR_CLONE_CHOICES)
    program = models.CharField(max_length=100, blank=True, null=True, help_text='e.g., SI-49T5, 205X1')
    clone = models.CharField(max_length=100, blank=True, null=True, help_text='e.g., 1B2, 25H8')
    media_lot = models.CharField(max_length=100, blank=True, null=True, help_text='Media lot number')

    # Archive/Discard status fields
    is_archived = models.BooleanField(default=False, help_text="Sample created in error")
    archive_reason = models.CharField(max_length=255, blank=True, null=True)
    archive_date = models.DateTimeField(null=True, blank=True)
    is_discarded = models.BooleanField(default=False, help_text="Experiment ended/sample discarded")
    discard_reason = models.CharField(max_length=255, blank=True, null=True)
    discard_date = models.DateTimeField(null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usp_seed_train'
        ordering = ['process_step', 'seed_train_id']

    def __str__(self):
        return f"{self.seed_train_id} ({self.cell_line})"


class USPVessel(models.Model):
    """Model for tracking bioreactors and shake flasks (production vessels)"""
    VESSEL_TYPE_CHOICES = [
        ('2L_BRX', '2L Bioreactor'),
        ('5L_BRX', '5L Bioreactor'),
        ('10L_BRX', '10L Bioreactor'),
        ('15L_BRX', '15L Bioreactor'),
        ('250mL_SF', '250mL Shake Flask'),
        ('500mL_SF', '500mL Shake Flask'),
        ('1L_SF', '1L Shake Flask'),
        ('2L_SF', '2L Shake Flask'),
    ]

    FEEDING_STRATEGY_CHOICES = [
        ('Platform', 'Platform'),
        ('Standard', 'Standard'),
        ('Other', 'Other'),
    ]

    POOL_OR_CLONE_CHOICES = [
        ('Pool', 'Pool'),
        ('Clone', 'Clone'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Archived', 'Archived'),
        ('Complete', 'Complete'),
    ]

    id = models.AutoField(primary_key=True)
    process_step = models.ForeignKey(USPProcessStep, on_delete=models.CASCADE, related_name='vessels')
    seed_train = models.ForeignKey(USPSeedTrain, on_delete=models.SET_NULL, null=True, blank=True, related_name='downstream_vessels')
    vessel_id = models.CharField(max_length=100)  # UPFB####
    vessel_type = models.CharField(max_length=20, choices=VESSEL_TYPE_CHOICES)
    start_volume = models.FloatField(null=True, blank=True, help_text="mL")
    cell_line = models.CharField(max_length=100, blank=True, null=True)
    media_type = models.CharField(max_length=100, blank=True, null=True)
    media_prep = models.ForeignKey('USPMediaPrep', on_delete=models.SET_NULL, null=True, blank=True, related_name='vessels_used')
    feeding_strategy = models.CharField(max_length=50, choices=FEEDING_STRATEGY_CHOICES, null=True, blank=True)
    inoculation_date = models.DateField(null=True, blank=True)
    inoculation_density = models.FloatField(null=True, blank=True, help_text="cells/mL")
    harvest_date = models.DateField(null=True, blank=True)
    harvest_viability = models.FloatField(null=True, blank=True, help_text="percentage")
    harvest_vcd = models.FloatField(null=True, blank=True, help_text="cells/mL")
    harvest_volume = models.FloatField(null=True, blank=True, help_text="mL")
    temperature_setpoint = models.FloatField(null=True, blank=True, default=37.0, help_text="°C")
    ph_setpoint = models.FloatField(null=True, blank=True, default=7.0)
    do_setpoint = models.FloatField(null=True, blank=True, default=40.0, help_text="% air saturation")
    agitation_rpm = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    serial_numbers = models.JSONField(null=True, blank=True, help_text="JSON field for storing vessel serial numbers (DO probes, pH probes, etc.)")

    # Excel template fields
    vessel_size = models.CharField(max_length=50, blank=True, null=True, help_text='e.g., 125 mL, 1L, 2L')
    pool_or_clone = models.CharField(max_length=50, blank=True, null=True, choices=POOL_OR_CLONE_CHOICES)
    program = models.CharField(max_length=100, blank=True, null=True, help_text='e.g., SI-49T5, 205X1')
    clone = models.CharField(max_length=100, blank=True, null=True, help_text='e.g., 1B2, 25H8')
    status = models.CharField(max_length=50, blank=True, null=True, choices=STATUS_CHOICES)

    # Archive/Discard status fields
    is_archived = models.BooleanField(default=False, help_text="Vessel created in error")
    archive_reason = models.CharField(max_length=255, blank=True, null=True)
    archive_date = models.DateTimeField(null=True, blank=True)
    is_discarded = models.BooleanField(default=False, help_text="Experiment ended/vessel discarded")
    discard_reason = models.CharField(max_length=255, blank=True, null=True)
    discard_date = models.DateTimeField(null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usp_vessel'
        unique_together = ('process_step', 'vessel_id')
        ordering = ['process_step', 'vessel_id']

    def __str__(self):
        return f"{self.vessel_id} ({self.vessel_type})"


class USPMediaComponentLibrary(models.Model):
    """Component library for media preparation"""
    COMPONENT_TYPE_CHOICES = [
        ('base_powder', 'Base Powder'),
        ('glucose', 'Glucose'),
        ('glutamine', 'Glutamine'),
        ('amino_acid', 'Amino Acid'),
        ('vitamin', 'Vitamin'),
        ('salt', 'Salt'),
        ('growth_factor', 'Growth Factor'),
        ('antibiotic', 'Antibiotic'),
        ('buffer', 'Buffer'),
        ('serum', 'Serum'),
        ('supplement', 'Supplement'),
        ('acid', 'Acid (pH adjustment)'),
        ('base', 'Base (pH adjustment)'),
        ('water', 'Water'),
        ('other', 'Other'),
    ]

    id = models.AutoField(primary_key=True)
    component_type = models.CharField(max_length=50, choices=COMPONENT_TYPE_CHOICES)
    component_name = models.CharField(max_length=200)
    catalog_number = models.CharField(max_length=100, blank=True, null=True)
    vendor = models.CharField(max_length=100, blank=True, null=True)
    typical_units = models.CharField(max_length=50, help_text="Typical units used (e.g., g, mL, L)")
    molecular_weight = models.FloatField(null=True, blank=True, help_text="g/mol")
    stock_concentration = models.FloatField(null=True, blank=True)
    stock_concentration_unit = models.CharField(max_length=20, blank=True, null=True)
    storage_conditions = models.CharField(max_length=200, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usp_media_component_library'
        ordering = ['component_type', 'component_name']
        unique_together = ['component_name', 'catalog_number']

    def __str__(self):
        return f"{self.component_name} ({self.catalog_number})" if self.catalog_number else self.component_name


class USPMediaRecipe(models.Model):
    """Model for storing media recipe templates with process steps"""
    id = models.AutoField(primary_key=True)
    recipe_id = models.CharField(max_length=100, unique=True)  # e.g., RCP001
    recipe_name = models.CharField(max_length=200)
    recipe_type = models.CharField(max_length=100)  # e.g., Growth Media, Feed A, Feed B, Basal Media
    version = models.CharField(max_length=20, default='1.0')
    description = models.TextField(blank=True, null=True)
    base_volume = models.FloatField(default=1.0, help_text="Base volume in L for recipe calculations")
    ph_target = models.FloatField(null=True, blank=True)
    osmolality_target = models.FloatField(null=True, blank=True, help_text="mOsm/kg")
    storage_temp = models.CharField(max_length=50, blank=True, null=True)
    shelf_life_days = models.IntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usp_media_recipe'
        ordering = ['recipe_type', 'recipe_name']

    def __str__(self):
        return f"{self.recipe_name} v{self.version}"


class USPMediaRecipeStep(models.Model):
    """Process steps for media recipe preparation - Long format base"""
    STEP_TYPE_CHOICES = [
        ('add_component', 'Add Component'),
        ('initial_water_fill', 'Initial MilliQ Water Fill (80%)'),
        ('add_water', 'Add Water (MilliQ)'),
        ('final_water_fill', 'Final Water Fill (to 100%)'),
        ('stir', 'Stir'),
        ('heat', 'Heat'),
        ('cool', 'Cool'),
        ('measure_ph', 'Measure pH'),
        ('adjust_ph', 'Adjust pH'),
        ('measure_osmolality', 'Measure Osmolality'),
        ('adjust_osmolality', 'Adjust Osmolality'),
        ('filter_sterilize', 'Filter Sterilize'),
        ('autoclave', 'Autoclave'),
        ('aliquot', 'Aliquot'),
        ('note', 'General Note/Instruction'),
    ]

    id = models.AutoField(primary_key=True)
    recipe = models.ForeignKey(USPMediaRecipe, on_delete=models.CASCADE, related_name='process_steps')
    step_number = models.IntegerField(help_text="Order of step in recipe")
    step_type = models.CharField(max_length=50, choices=STEP_TYPE_CHOICES)
    instructions = models.TextField(blank=True, null=True, help_text="General instructions or notes")
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'usp_media_recipe_step'
        ordering = ['recipe', 'step_number']
        unique_together = ['recipe', 'step_number']
        indexes = [
            models.Index(fields=['recipe', 'step_type']),
            models.Index(fields=['step_type', 'step_number']),
        ]

    def __str__(self):
        return f"Recipe {self.recipe.recipe_id} - Step {self.step_number}: {self.get_step_type_display()}"

    def clean(self):
        """Validate that required parameters exist for this step type"""
        from django.core.exceptions import ValidationError

        # Only validate if step has been saved and has parameters
        if self.pk:
            params = {p.parameter_key: p for p in self.parameters.all()}

            if self.step_type == 'add_component':
                required = ['component_id', 'amount_per_liter', 'amount_unit']
                missing = [k for k in required if k not in params or not params[k].value_text]
                if missing:
                    raise ValidationError(f"Component step missing required parameters: {', '.join(missing)}")

            elif self.step_type in ['stir', 'heat', 'cool']:
                if 'duration_minutes' not in params:
                    raise ValidationError(f"{self.get_step_type_display()} step requires 'duration_minutes' parameter")
                if self.step_type in ['heat', 'cool'] and 'temperature' not in params:
                    raise ValidationError(f"{self.get_step_type_display()} step requires 'temperature' parameter")

            elif self.step_type in ['measure_ph', 'adjust_ph']:
                if 'target_ph' not in params:
                    raise ValidationError(f"pH step requires 'target_ph' parameter")

            elif self.step_type == 'add_water':
                if 'target_volume' not in params:
                    raise ValidationError(f"Add water step requires 'target_volume' parameter")

    @property
    def is_complete(self):
        """Check if step has all required parameters"""
        try:
            self.clean()
            return True
        except:
            return False

    def get_params(self):
        """Get parameter helper for easier access"""
        return StepParameterHelper(self)


class USPMediaRecipeStepParameter(models.Model):
    """Flexible parameters for recipe steps - long format"""

    PARAMETER_TYPE_CHOICES = [
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('string', 'String'),
        ('boolean', 'Boolean'),
        ('fk_component', 'Foreign Key: Component'),
    ]

    id = models.AutoField(primary_key=True)
    step = models.ForeignKey(USPMediaRecipeStep, on_delete=models.CASCADE, related_name='parameters')
    parameter_key = models.CharField(max_length=50, help_text="Parameter name (e.g., 'component_id', 'amount_per_liter')")
    parameter_type = models.CharField(max_length=20, choices=PARAMETER_TYPE_CHOICES, help_text="Data type for validation")

    # Store values as text, cast based on parameter_type
    value_text = models.TextField(help_text="String representation of value")

    # Optional: denormalized typed values for efficient queries
    value_int = models.IntegerField(null=True, blank=True, db_index=True)
    value_float = models.FloatField(null=True, blank=True, db_index=True)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usp_media_recipe_step_parameter'
        unique_together = ['step', 'parameter_key']
        indexes = [
            models.Index(fields=['step', 'parameter_key']),
        ]

    def clean(self):
        """Validate value matches parameter_type"""
        from django.core.exceptions import ValidationError

        if not self.value_text:
            raise ValidationError("value_text is required")

        try:
            if self.parameter_type == 'integer':
                val = int(self.value_text)
                self.value_int = val
            elif self.parameter_type == 'float':
                val = float(self.value_text)
                self.value_float = val
            elif self.parameter_type == 'boolean':
                if self.value_text.lower() not in ['true', 'false', '1', '0']:
                    raise ValueError()
            elif self.parameter_type == 'fk_component':
                val = int(self.value_text)
                self.value_int = val
                # Verify component exists
                if not USPMediaComponentLibrary.objects.filter(id=val).exists():
                    raise ValidationError(f"Component with id {val} does not exist")
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid value '{self.value_text}' for type '{self.parameter_type}'")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_value(self):
        """Get typed value based on parameter_type"""
        if self.parameter_type == 'integer':
            return int(self.value_text)
        elif self.parameter_type == 'float':
            return float(self.value_text)
        elif self.parameter_type == 'boolean':
            return self.value_text.lower() in ['true', '1']
        elif self.parameter_type == 'fk_component':
            return USPMediaComponentLibrary.objects.get(id=int(self.value_text))
        else:
            return self.value_text

    def __str__(self):
        return f"{self.parameter_key}={self.value_text} ({self.parameter_type})"


# Helper class for easier parameter access
class StepParameterHelper:
    """Helper to make accessing step parameters easier"""

    def __init__(self, step):
        self.step = step
        self._params = None

    @property
    def params(self):
        """Lazy load parameters"""
        if self._params is None:
            self._params = {
                p.parameter_key: p for p in self.step.parameters.all()
            }
        return self._params

    def get(self, key, default=None):
        """Get parameter value"""
        if key in self.params:
            return self.params[key].get_value()
        return default

    def get_component(self):
        """Get component for add_component steps"""
        comp_id = self.get('component_id')
        if comp_id:
            return USPMediaComponentLibrary.objects.get(id=comp_id)
        return None

    def set(self, key, value, param_type):
        """Set parameter value"""
        param, created = USPMediaRecipeStepParameter.objects.update_or_create(
            step=self.step,
            parameter_key=key,
            defaults={
                'value_text': str(value),
                'parameter_type': param_type
            }
        )
        # Invalidate cache
        self._params = None
        return param


class USPMediaPrep(models.Model):
    """Model for tracking media preparations for cell culture"""
    id = models.AutoField(primary_key=True)
    media_id = models.CharField(max_length=100, unique=True)  # UPMP#### (changed from UPMD)
    recipe = models.ForeignKey(USPMediaRecipe, on_delete=models.SET_NULL, null=True, blank=True, related_name='preparations')
    media_name = models.CharField(max_length=200)
    media_type = models.CharField(max_length=100)  # e.g., Growth Media, Feed Media, Basal Media
    batch_size = models.FloatField(help_text="Total volume in L")
    preparation_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    prepared_by = models.CharField(max_length=100)
    ph_actual = models.FloatField(null=True, blank=True)
    osmolality_actual = models.FloatField(null=True, blank=True, help_text="mOsm/kg")
    sterility_check = models.BooleanField(default=False)
    storage_location = models.CharField(max_length=200, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # Status tracking
    is_used_up = models.BooleanField(default=False, help_text="Has this media been completely used or discarded?")
    date_used_up = models.DateField(null=True, blank=True, help_text="Date when media was used up or discarded")

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    # Link to experiment
    experiment = models.ForeignKey(USPExperiment, on_delete=models.SET_NULL, null=True, blank=True, related_name='media_preps')

    class Meta:
        db_table = 'usp_media_prep'
        ordering = ['-preparation_date', 'media_id']

    def __str__(self):
        return f"{self.media_id} - {self.media_name} ({self.preparation_date})"


class USPMediaComponent(models.Model):
    """Model for tracking individual components in media preparations"""
    COMPONENT_TYPE_CHOICES = [
        ('base_powder', 'Base Powder'),
        ('glucose', 'Glucose'),
        ('glutamine', 'Glutamine'),
        ('amino_acid', 'Amino Acid'),
        ('vitamin', 'Vitamin'),
        ('salt', 'Salt'),
        ('growth_factor', 'Growth Factor'),
        ('antibiotic', 'Antibiotic'),
        ('buffer', 'Buffer'),
        ('serum', 'Serum'),
        ('other', 'Other'),
    ]

    UNIT_CHOICES = [
        ('g', 'g'),
        ('mg', 'mg'),
        ('L', 'L'),
        ('mL', 'mL'),
        ('µL', 'µL'),
        ('g/L', 'g/L'),
        ('mg/L', 'mg/L'),
        ('mM', 'mM'),
        ('µM', 'µM'),
        ('%', '%'),
    ]

    id = models.AutoField(primary_key=True)
    media_prep = models.ForeignKey(USPMediaPrep, on_delete=models.CASCADE, related_name='components')
    component_type = models.CharField(max_length=50, choices=COMPONENT_TYPE_CHOICES)
    component_name = models.CharField(max_length=200)
    lot_number = models.CharField(max_length=100, blank=True, null=True)
    target_amount = models.FloatField()
    actual_amount = models.FloatField()
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    vendor = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'usp_media_component'
        ordering = ['media_prep', 'component_type', 'component_name']

    def __str__(self):
        return f"{self.component_name} ({self.actual_amount} {self.unit})"


class USPCellBank(models.Model):
    """Model for tracking cell banks derived from seed trains"""
    id = models.AutoField(primary_key=True)
    cell_bank_id = models.CharField(max_length=100, unique=True)  # UPCB####
    seed_train_source = models.ForeignKey(
        USPSeedTrain,
        on_delete=models.CASCADE,
        related_name='cell_banks',
        help_text="Seed train from which this cell bank was created"
    )
    density = models.FloatField(help_text="Viable cells/mL")
    number_of_vials = models.IntegerField()
    media = models.CharField(max_length=200, help_text="e.g., CHO MaxX + 10% DMSO")
    banking_date = models.DateField()
    bank_age_days = models.IntegerField(null=True, blank=True, help_text="Age in days")
    bank_age_notes = models.TextField(blank=True, null=True)
    ln2_location = models.CharField(max_length=200, blank=True, null=True, help_text="Liquid nitrogen storage location")
    notes = models.TextField(blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usp_cell_bank'
        ordering = ['-banking_date', 'cell_bank_id']

    def __str__(self):
        return f"{self.cell_bank_id} - {self.seed_train_source.seed_train_id} ({self.banking_date})"


# ============================================================================
# OCTET BIOLAYER INTERFEROMETRY MODELS
# ============================================================================

class OctetExperiment(models.Model):
    """
    Main experiment table - imported from 'Experiment Metadata' sheet
    One row per experiment (one per consolidated Excel file)
    """
    # Primary identifiers
    run_id = models.CharField(max_length=100, unique=True, help_text="UUID from manifest")
    experiment_name = models.CharField(max_length=255, db_index=True)

    # Experiment classification (from ExpMethod.fmf)
    experiment_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="KINETICS, QUANTITATION, SCREENING, EPITOPE"
    )
    experiment_subtype = models.CharField(
        max_length=50,
        blank=True,
        help_text="KBASIC, EPITOPE, etc."
    )
    description = models.TextField(blank=True)

    # Timing
    experiment_datetime = models.CharField(max_length=50, blank=True, help_text="From ExpMethod")
    start_datetime = models.DateTimeField(null=True, blank=True, help_text="From FRD files")

    # Instrument metadata
    machine_name = models.CharField(max_length=100, blank=True)
    instrument_type = models.CharField(max_length=50, blank=True)
    instrument_serial = models.CharField(max_length=50, blank=True)
    sensor_type = models.CharField(max_length=100, blank=True)

    # Experimental parameters
    temperature = models.FloatField(null=True, blank=True, help_text="°C")
    cycle_time_ms = models.IntegerField(null=True, blank=True)
    flow_rate_units = models.CharField(max_length=20, default='RPM')
    concentration_units = models.CharField(max_length=20, default='µg/ml')
    molar_conc_units = models.CharField(max_length=20, default='nM')

    # User & method info
    user_name = models.CharField(max_length=100, blank=True, db_index=True)
    method_template = models.CharField(max_length=500, blank=True)

    # File tracking
    consolidated_file_path = models.CharField(max_length=500, help_text="Path to consolidated Excel")
    original_folder_path = models.CharField(max_length=500, blank=True, help_text="Original data folder")

    # Import tracking
    date_imported = models.DateTimeField(auto_now_add=True)
    imported_by = models.CharField(max_length=100, blank=True)

    # Group and organizational fields
    group = models.CharField(
        max_length=10,
        choices=[
            ('PD', 'Process Development'),
            ('PE', 'Protein Engineering'),
            ('CLD', 'Cell Science'),
            ('IO', 'IO')
        ],
        db_index=True,
        blank=True,
        null=True,
        help_text="Department/group that generated the data"
    )

    assay_type = models.CharField(
        max_length=50,
        choices=[
            ('Asymmetric', 'Asymmetric'),
            ('Binding Kinetics', 'Binding Kinetics'),
            ('HCP', 'HCP'),
            ('Octet Titer', 'Octet Titer')
        ],
        db_index=True,
        blank=True,
        null=True,
        help_text="Specific assay type"
    )

    import_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Import'),
            ('imported', 'Imported'),
            ('archived', 'Archived')
        ],
        default='imported',
        db_index=True,
        help_text="Import workflow status"
    )

    source_folder = models.CharField(
        max_length=500,
        blank=True,
        help_text="Original folder path in Imports directory"
    )

    imported_folder = models.CharField(
        max_length=500,
        blank=True,
        help_text="Folder path in Imported directory (after import)"
    )

    # Vendor software settings (from HTSettings.efrd)
    vendor_analysis_settings = models.JSONField(
        null=True,
        blank=True,
        help_text="Vendor software analysis settings from HTSettings.efrd (preprocessing, reference wells, etc.)"
    )

    class Meta:
        db_table = 'octet_experiment'
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['run_id']),
            models.Index(fields=['experiment_name']),
            models.Index(fields=['experiment_type', 'experiment_subtype']),
            models.Index(fields=['start_datetime']),
            models.Index(fields=['user_name']),
        ]

    def __str__(self):
        return f"{self.experiment_name} ({self.experiment_type})"


class OctetSensorData(models.Model):
    """
    Results for each sensor - imported from 'Results Table' sheet
    One row per sensor (typically 8-96 per experiment)
    """
    # Foreign key to experiment
    experiment = models.ForeignKey(
        OctetExperiment,
        on_delete=models.CASCADE,
        related_name='sensors'
    )

    # Sensor identification
    sensor_location = models.CharField(max_length=10, help_text="A1, B1, etc.")
    sensor_type = models.CharField(max_length=100, blank=True)

    # Sample information
    sample_id = models.CharField(max_length=255, blank=True, db_index=True)
    loading_sample_id = models.CharField(max_length=255, blank=True)

    # Well locations (from Results Table)
    baseline_location = models.CharField(max_length=10, blank=True)
    loading_location = models.CharField(max_length=10, blank=True)
    association_location = models.CharField(max_length=10, blank=True)

    # Concentration
    concentration = models.FloatField(null=True, blank=True)
    concentration_units = models.CharField(max_length=20, blank=True)

    # Response (calculated binding)
    response = models.FloatField(null=True, blank=True, help_text="Binding response (nm)")

    # Quality flags (from Results Table)
    selected = models.CharField(max_length=5, default='x')
    include = models.CharField(max_length=5, default='x')
    cycle = models.IntegerField(default=1)

    class Meta:
        db_table = 'octet_sensor_data'
        ordering = ['sensor_location']
        unique_together = [['experiment', 'sensor_location', 'cycle']]
        indexes = [
            models.Index(fields=['experiment', 'sensor_location']),
            models.Index(fields=['sample_id']),
            models.Index(fields=['loading_sample_id']),
        ]

    def __str__(self):
        return f"{self.experiment.experiment_name} - {self.sensor_location}: {self.sample_id}"


class OctetStepData(models.Model):
    """
    Step-level data for each sensor - imported from 'Step Summary' sheet
    Multiple rows per sensor (one per experimental step)
    """
    # Foreign key to sensor
    sensor = models.ForeignKey(
        OctetSensorData,
        on_delete=models.CASCADE,
        related_name='steps'
    )

    # Step identification
    step_number = models.IntegerField()
    step_name = models.CharField(max_length=100, db_index=True)
    step_type = models.CharField(max_length=50)
    step_status = models.CharField(max_length=20, default='OK')

    # Sample info for this step
    sample_location = models.CharField(max_length=10)
    sample_id = models.CharField(max_length=255, blank=True)
    sample_group = models.CharField(max_length=100, blank=True)
    sample_row = models.CharField(max_length=5, blank=True)
    well_type = models.CharField(max_length=50, blank=True)

    # Concentration for this step
    concentration = models.CharField(max_length=50, blank=True)
    concentration_units = models.CharField(max_length=20, blank=True)

    # Timing
    start_time = models.FloatField(null=True, blank=True, help_text="Start time (s)")
    assay_time = models.FloatField(null=True, blank=True, help_text="Duration (s)")
    actual_time = models.FloatField(null=True, blank=True, help_text="Actual duration (s)")

    # Environmental
    temperature = models.FloatField(null=True, blank=True, help_text="°C")
    flow_rate = models.IntegerField(null=True, blank=True, help_text="RPM")

    # Statistics (calculated from time series)
    data_points = models.IntegerField(null=True, blank=True)
    mean_response = models.FloatField(null=True, blank=True, help_text="nm")
    final_response = models.FloatField(null=True, blank=True, help_text="nm")

    class Meta:
        db_table = 'octet_step_data'
        ordering = ['sensor', 'step_number']
        unique_together = [['sensor', 'step_number']]
        indexes = [
            models.Index(fields=['sensor', 'step_number']),
            models.Index(fields=['step_name']),
            models.Index(fields=['step_type']),
        ]

    def __str__(self):
        return f"{self.sensor.sensor_location} - Step {self.step_number}: {self.step_name}"


class OctetTimeSeriesData(models.Model):
    """
    Time series data points - imported from 'Time Series Data' sheet
    Individual rows approach for maximum database compatibility

    Includes denormalized fields (run_id, sensor_location, step_number) for efficient querying
    without JOINs. These match the consolidated Excel structure.
    """
    # Foreign key to step
    step = models.ForeignKey(
        OctetStepData,
        on_delete=models.CASCADE,
        related_name='time_series'
    )

    # Denormalized fields for efficient querying (match Excel structure)
    run_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text="Experiment run ID for easy querying (denormalized)"
    )
    sensor_location = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        db_index=True,
        help_text="Sensor location (A1, B2, etc.) for easy querying (denormalized)"
    )
    step_number = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Step number (1-8) for easy filtering (denormalized)"
    )

    # Time series point
    time = models.FloatField(help_text="Time in seconds")
    response = models.FloatField(help_text="Response in nm")

    class Meta:
        db_table = 'octet_time_series_data'
        ordering = ['step', 'time']
        indexes = [
            models.Index(fields=['step', 'time']),
            models.Index(fields=['run_id', 'sensor_location', 'step_number', 'time'], name='octet_time_query_idx'),
        ]

    def __str__(self):
        return f"{self.step} - t={self.time:.2f}s"


class OctetSensorLayout(models.Model):
    """
    Sensor plate layout - imported from 'Sensor Layout' sheet
    Defines which sensors are used and their types
    """
    experiment = models.ForeignKey(
        OctetExperiment,
        on_delete=models.CASCADE,
        related_name='sensor_layout'
    )

    sensor_location = models.CharField(max_length=10)
    sensor_state = models.IntegerField(help_text="0=unused, 1=active")
    sensor_type = models.CharField(max_length=100, blank=True)
    sensor_lot = models.CharField(max_length=100, blank=True)
    sensor_info = models.TextField(blank=True)

    class Meta:
        db_table = 'octet_sensor_layout'
        unique_together = [['experiment', 'sensor_location']]
        indexes = [
            models.Index(fields=['experiment', 'sensor_location']),
        ]

    def __str__(self):
        return f"{self.experiment.experiment_name} - {self.sensor_location}: {self.sensor_type}"


class OctetSampleLayout(models.Model):
    """
    Sample plate layout - imported from 'Sample Layout' sheet
    Defines what's in each well of the sample plate
    """
    experiment = models.ForeignKey(
        OctetExperiment,
        on_delete=models.CASCADE,
        related_name='sample_layout'
    )

    sample_location = models.CharField(max_length=10)
    sample_type = models.CharField(max_length=50, help_text="BUFFER, SAMPLE, KLOAD, etc.")
    sample_state = models.IntegerField(help_text="0=unused, 2=active")
    sample_id = models.CharField(max_length=255, blank=True)
    sample_group = models.CharField(max_length=100, blank=True)
    sample_conc = models.FloatField(null=True, blank=True)
    sample_info = models.TextField(blank=True)

    class Meta:
        db_table = 'octet_sample_layout'
        unique_together = [['experiment', 'sample_location']]
        indexes = [
            models.Index(fields=['experiment', 'sample_location']),
            models.Index(fields=['sample_id']),
        ]

    def __str__(self):
        return f"{self.experiment.experiment_name} - {self.sample_location}: {self.sample_id}"


class OctetStepSequence(models.Model):
    """
    Experimental step sequence - imported from 'Step Sequence' sheet
    Defines the method protocol (order of steps)
    """
    experiment = models.ForeignKey(
        OctetExperiment,
        on_delete=models.CASCADE,
        related_name='step_sequence'
    )

    step_name = models.CharField(max_length=100)
    step_order = models.IntegerField(help_text="Order in sequence")
    assay_time = models.FloatField(help_text="Duration in seconds")
    flow_rate = models.IntegerField(help_text="RPM")
    step_type = models.IntegerField(help_text="Numeric step type code")

    class Meta:
        db_table = 'octet_step_sequence'
        ordering = ['experiment', 'step_order']
        unique_together = [['experiment', 'step_order']]
        indexes = [
            models.Index(fields=['experiment', 'step_order']),
        ]

    def __str__(self):
        return f"{self.experiment.experiment_name} - {self.step_order}: {self.step_name}"


class OctetKineticAnalysis(models.Model):
    """
    Kinetic analysis results (curve fitting)
    Created by analysis dashboard, not from Excel import
    """
    sensor = models.ForeignKey(
        OctetSensorData,
        on_delete=models.CASCADE,
        related_name='kinetic_analyses'
    )

    # Analysis metadata
    analysis_method = models.CharField(
        max_length=100,
        choices=[
            ('1_TO_1_BINDING', '1:1 Binding'),
            ('2_TO_1_BINDING', '2:1 Heterogeneous Ligand'),
            ('STEADY_STATE', 'Steady-State Analysis'),
            ('MASS_TRANSPORT', 'Mass Transport Limitation'),
            ('CUSTOM', 'Custom Model'),
        ],
        default='1_TO_1_BINDING'
    )
    analysis_date = models.DateTimeField(auto_now_add=True)
    analyzed_by = models.CharField(max_length=100, blank=True)

    # Kinetic parameters
    KD = models.FloatField(null=True, blank=True, help_text="Dissociation constant (M)")
    kon = models.FloatField(null=True, blank=True, help_text="Association rate (1/Ms)")
    koff = models.FloatField(null=True, blank=True, help_text="Dissociation rate (1/s)")
    Rmax = models.FloatField(null=True, blank=True, help_text="Maximum response (nm)")

    # Intermediate parameters
    kobs = models.FloatField(null=True, blank=True, help_text="Observed rate (1/s)")
    Req = models.FloatField(null=True, blank=True, help_text="Equilibrium response (nm)")

    # Goodness of fit
    chi_squared = models.FloatField(null=True, blank=True)
    R_squared_assoc = models.FloatField(null=True, blank=True)
    R_squared_dissoc = models.FloatField(null=True, blank=True)

    # Steady-state specific
    SSG_KD = models.FloatField(null=True, blank=True)
    SSG_Rmax = models.FloatField(null=True, blank=True)
    SSG_R_squared = models.FloatField(null=True, blank=True)

    # Fit status
    fit_converged = models.BooleanField(default=False)
    fit_error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'octet_kinetic_analysis'
        ordering = ['-analysis_date']
        indexes = [
            models.Index(fields=['sensor']),
            models.Index(fields=['analysis_method']),
        ]

    def __str__(self):
        kd_str = f"KD={self.KD:.2e}" if self.KD else "KD=N/A"
        return f"{self.sensor} - {self.analysis_method} ({kd_str})"


class OctetAnalysisTemplate(models.Model):
    """
    Reusable analysis configuration templates

    Stores saved analysis configurations that can be reused across experiments.
    Users can create custom templates for different assay types (asymmetric,
    kinetics, titer, HCP, etc.) with their preferred parameters.

    Example:
        template = OctetAnalysisTemplate.objects.create(
            template_name="Standard Asymmetric v1",
            analysis_type="ASYMMETRIC",
            parameters={
                'proa_start': 420,
                'proa_end': 430,
                'kappa_start': 520,
                'kappa_end': 530,
                'buffer_baseline_correction': True
            },
            created_by="user@example.com"
        )
    """
    # Template Metadata
    template_name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Unique name for this template"
    )
    analysis_type = models.CharField(
        max_length=50,
        db_index=True,
        choices=[
            ('ASYMMETRIC', 'Asymmetric Analysis'),
            ('KINETICS_1TO1', '1:1 Binding Kinetics'),
            ('KINETICS_2TO1', '2:1 Binding Kinetics'),
            ('STEADY_STATE', 'Steady-State Analysis'),
            ('TITER', 'Titer Quantification'),
            ('HCP', 'HCP Quantification'),
        ],
        help_text="Type of analysis this template is for"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of what this template does"
    )

    # Template Authorship
    created_by = models.CharField(
        max_length=100,
        blank=True,
        help_text="Username of template creator"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    # Default Flag
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default template for this analysis type"
    )

    # Analysis Parameters (stored as JSON)
    parameters = models.JSONField(
        help_text="Analysis-specific parameters stored as JSON dictionary"
    )
    # Example parameters for ASYMMETRIC:
    # {
    #     "proa_start": 420,
    #     "proa_end": 430,
    #     "proa_enabled": True,
    #     "bb_time1": 440,
    #     "bb_time2": 450,
    #     "bb_enabled": True,
    #     "kappa_start": 520,
    #     "kappa_end": 530,
    #     "kappa_enabled": True,
    #     "buffer_baseline_correction": True,
    #     "smoothing_enabled": False,
    #     "use_all_standards": True
    # }

    class Meta:
        db_table = 'octet_analysis_template'
        ordering = ['analysis_type', '-is_default', 'template_name']
        indexes = [
            models.Index(fields=['analysis_type']),
            models.Index(fields=['analysis_type', 'is_default']),
            models.Index(fields=['template_name']),
        ]
        constraints = [
            # Ensure only one default template per analysis type
            models.UniqueConstraint(
                fields=['analysis_type'],
                condition=models.Q(is_default=True),
                name='unique_default_per_type'
            )
        ]

    def __str__(self):
        default_str = " (Default)" if self.is_default else ""
        return f"{self.template_name} - {self.analysis_type}{default_str}"

    def get_parameter(self, key, default=None):
        """Get a specific parameter value"""
        return self.parameters.get(key, default)

    def set_parameter(self, key, value):
        """Set a specific parameter value"""
        self.parameters[key] = value
        self.save()

    def clone(self, new_name, created_by=""):
        """Create a copy of this template with a new name"""
        return OctetAnalysisTemplate.objects.create(
            template_name=new_name,
            analysis_type=self.analysis_type,
            description=f"Copy of {self.template_name}",
            created_by=created_by,
            parameters=self.parameters.copy(),
            is_default=False
        )

# ============================================================================

# ============================================================================
# OCTET KINETICS MODELS (NEW OPTIMIZED ARCHITECTURE)
# ============================================================================
# These are the new optimized models for kinetics data
# Prefix: OctetKinetics (to distinguish from old Octet models)
# Architecture: 2 tables instead of 4
#   - OctetKineticsExperiment: One per experiment
#   - OctetKineticsSensor: One per antibody×concentration (stores time series as JSON)
# ============================================================================

class OctetKineticsExperiment(models.Model):
    """
    Kinetics experiment metadata
    One row per experiment
    """
    # Primary identifiers
    run_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="UUID from manifest/FRD files"
    )
    experiment_name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="User-friendly experiment name (e.g., OE292)"
    )
    description = models.TextField(
        blank=True,
        help_text="Experiment description"
    )

    # Experiment classification
    experiment_type = models.CharField(
        max_length=50,
        default='KINETICS',
        db_index=True
    )
    experiment_subtype = models.CharField(
        max_length=50,
        default='KBASIC',
        blank=True
    )

    # Timing
    experiment_datetime = models.CharField(
        max_length=50,
        blank=True,
        help_text="Datetime from FRD files"
    )
    start_datetime = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True
    )

    # Instrument metadata
    machine_name = models.CharField(max_length=100, blank=True)
    instrument_type = models.CharField(max_length=50, blank=True)
    instrument_serial = models.CharField(max_length=50, blank=True)
    sensor_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., AHC (Anti-hIgG Fc Capture)"
    )

    # Experimental parameters (from HTSettings.efrd)
    binding_model = models.CharField(
        max_length=50,
        default='FastOne2One',
        help_text="1:1, 2:1, etc."
    )
    fit_type = models.CharField(
        max_length=50,
        default='Global',
        help_text="Global or Local fitting"
    )
    steps_to_analyze = models.CharField(
        max_length=50,
        default='Both',
        help_text="Association, Dissociation, or Both"
    )

    # Association window (from HTSettings)
    assoc_start_time = models.FloatField(default=0.0, help_text="seconds")
    assoc_end_time = models.FloatField(default=180.0, help_text="seconds")
    assoc_start_pt = models.IntegerField(default=0)
    assoc_end_pt = models.IntegerField(default=900)

    # Dissociation window (from HTSettings)
    dissoc_start_time = models.FloatField(default=0.0, help_text="seconds")
    dissoc_end_time = models.FloatField(default=60.0, help_text="seconds")
    dissoc_start_pt = models.IntegerField(default=0)
    dissoc_end_pt = models.IntegerField(default=300)

    # Sampling
    delta_t = models.FloatField(
        default=0.2,
        help_text="Sampling interval (seconds)"
    )
    sampling_rate_hz = models.FloatField(
        default=5.0,
        help_text="Sampling rate (Hz)"
    )

    # Fit grouping (from HTSettings)
    fit_group_by = models.CharField(max_length=50, default='Color')
    rmax_unlink = models.CharField(max_length=50, default='Sensor')

    # Units
    concentration_units = models.CharField(max_length=20, default='nM')
    response_units = models.CharField(max_length=20, default='nm')

    # File tracking
    original_folder_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to folder with FRD files"
    )
    ht_settings_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to HTSettings.efrd"
    )
    analysis_excel_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to FRD_Analysis.xlsx"
    )

    # Import tracking
    date_imported = models.DateTimeField(auto_now_add=True)
    imported_by = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'octet_kinetics_experiment'
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['run_id']),
            models.Index(fields=['experiment_name']),
            models.Index(fields=['experiment_type']),
            models.Index(fields=['start_datetime']),
        ]

    def __str__(self):
        return f"{self.experiment_name} ({self.run_id[:8]}...)"


class OctetKineticsSensor(models.Model):
    """
    Complete sensor data - ONE ROW per antibody×concentration
    All time series data stored as JSON in single row

    This is the core table - everything you need in one place!
    """
    # Foreign key to experiment
    experiment = models.ForeignKey(
        OctetKineticsExperiment,
        on_delete=models.CASCADE,
        related_name='sensors'
    )

    # ==========================================
    # SENSOR IDENTIFICATION
    # ==========================================
    sensor_location = models.CharField(
        max_length=50,
        db_index=True,
        help_text="t1_001_01 format from FRD file"
    )
    frd_file = models.CharField(
        max_length=100,
        db_index=True,
        help_text="251013_001.frd"
    )
    frd_number = models.IntegerField(
        help_text="1-16 for OE292"
    )
    cycle_number = models.IntegerField(
        help_text="Cycle within FRD file"
    )

    # ==========================================
    # SAMPLE IDENTIFICATION
    # ==========================================
    antibody_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Loading sample (e.g., SI-157C11_P5158)"
    )
    analyte_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Sample being tested (e.g., hsCD3d/e_Acro_CDD-H52W1)"
    )
    concentration_nm = models.FloatField(
        db_index=True,
        help_text="Analyte concentration in nM"
    )

    # ==========================================
    # WELL LOCATIONS (for traceability)
    # ==========================================
    loading_sample = models.CharField(
        max_length=255,
        help_text="Sample name loaded"
    )
    loading_well = models.CharField(
        max_length=10,
        db_index=True,
        help_text="e.g., A5, C10"
    )

    baseline_sample = models.CharField(
        max_length=255,
        blank=True,
        help_text="Usually buffer"
    )
    baseline_well = models.CharField(
        max_length=10,
        blank=True,
        help_text="e.g., A1, A3"
    )

    association_sample = models.CharField(
        max_length=255,
        blank=True,
        help_text="Analyte sample"
    )
    association_well = models.CharField(
        max_length=10,
        db_index=True,
        blank=True,
        help_text="e.g., A2, A4"
    )

    dissociation_well = models.CharField(
        max_length=10,
        blank=True,
        help_text="Usually buffer (same as baseline)"
    )

    # ==========================================
    # REFERENCE TRACKING
    # ==========================================
    is_reference = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True if concentration_nm = 0.0 (buffer only)"
    )
    reference_sensor = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='samples_using_this_ref',
        help_text="Link to reference sensor for subtraction"
    )

    # ==========================================
    # DATA POINT COUNTS
    # ==========================================
    loading_points = models.IntegerField(default=0)
    baseline_points = models.IntegerField(default=0)
    association_points = models.IntegerField(default=0)
    dissociation_points = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)

    # ==========================================
    # TIME SERIES DATA (JSON)
    # ==========================================
    # Each step stored as: {'time': [array], 'response': [array]}

    loading_data = models.JSONField(
        default=dict,
        help_text="{'time': [...], 'response': [...]}"
    )
    baseline_data = models.JSONField(
        default=dict,
        help_text="{'time': [...], 'response': [...]}"
    )
    association_data = models.JSONField(
        default=dict,
        help_text="{'time': [...], 'response': [...]}"
    )
    dissociation_data = models.JSONField(
        default=dict,
        help_text="{'time': [...], 'response': [...]}"
    )

    # ==========================================
    # TIME RANGES (for quick reference)
    # ==========================================
    assoc_time_start = models.FloatField(
        null=True,
        blank=True,
        help_text="Association start time (s)"
    )
    assoc_time_end = models.FloatField(
        null=True,
        blank=True,
        help_text="Association end time (s)"
    )

    # ==========================================
    # KINETIC PARAMETERS (from vendor analysis)
    # ==========================================
    # These come from Excel if available

    # Primary kinetic constants
    kd_m = models.FloatField(
        null=True,
        blank=True,
        help_text="Dissociation constant (M)"
    )
    kd_error = models.FloatField(
        null=True,
        blank=True,
        help_text="KD error (M)"
    )
    ka_1_ms = models.FloatField(
        null=True,
        blank=True,
        help_text="Association rate constant (1/Ms)"
    )
    ka_error = models.FloatField(
        null=True,
        blank=True,
        help_text="ka error (1/Ms)"
    )
    kdis_1_s = models.FloatField(
        null=True,
        blank=True,
        help_text="Dissociation rate constant (1/s)"
    )
    kdis_error = models.FloatField(
        null=True,
        blank=True,
        help_text="kdis error (1/s)"
    )

    # Response parameters
    response = models.FloatField(
        null=True,
        blank=True,
        help_text="Response (nm)"
    )
    rmax = models.FloatField(
        null=True,
        blank=True,
        help_text="Maximum response (nm)"
    )
    rmax_error = models.FloatField(
        null=True,
        blank=True,
        help_text="Rmax error (nm)"
    )

    # Intermediate parameters
    kobs = models.FloatField(
        null=True,
        blank=True,
        help_text="Observed rate (1/s)"
    )
    kobs_error = models.FloatField(
        null=True,
        blank=True,
        help_text="kobs error (1/s)"
    )
    req = models.FloatField(
        null=True,
        blank=True,
        help_text="Equilibrium response (nm)"
    )
    req_rmax_percent = models.FloatField(
        null=True,
        blank=True,
        help_text="Req/Rmax (%)"
    )

    # Goodness of fit
    rss = models.FloatField(
        null=True,
        blank=True,
        help_text="Residual sum of squares"
    )
    r_squared = models.FloatField(
        null=True,
        blank=True,
        help_text="Full R² (goodness of fit)"
    )

    # Steady-state global (SSG) parameters
    ssg_kd = models.FloatField(
        null=True,
        blank=True,
        help_text="Steady-state global KD"
    )
    ssg_rmax = models.FloatField(
        null=True,
        blank=True,
        help_text="Steady-state global Rmax"
    )
    ssg_r_squared = models.FloatField(
        null=True,
        blank=True,
        help_text="Steady-state global R²"
    )

    class Meta:
        db_table = 'octet_kinetics_sensor'
        ordering = ['antibody_id', 'concentration_nm']
        unique_together = [
            ['experiment', 'antibody_id', 'concentration_nm']
        ]
        indexes = [
            models.Index(fields=['experiment', 'antibody_id']),
            models.Index(fields=['experiment', 'antibody_id', 'concentration_nm']),
            models.Index(fields=['antibody_id']),
            models.Index(fields=['is_reference']),
            models.Index(fields=['loading_well']),
            models.Index(fields=['association_well']),
            models.Index(fields=['frd_file']),
        ]

    def __str__(self):
        ref_str = " [REF]" if self.is_reference else ""
        return f"{self.antibody_id} @ {self.concentration_nm} nM{ref_str}"

    def get_full_timeseries(self):
        """
        Combine all steps into single time series
        Returns: (time_array, response_array) as numpy arrays
        """
        import numpy as np

        all_time = []
        all_response = []

        for step_data in [
            self.loading_data,
            self.baseline_data,
            self.association_data,
            self.dissociation_data
        ]:
            if step_data and 'time' in step_data:
                all_time.extend(step_data['time'])
                all_response.extend(step_data['response'])

        return np.array(all_time), np.array(all_response)

    def get_association_data(self):
        """Get just association step as numpy arrays"""
        import numpy as np

        if not self.association_data:
            return np.array([]), np.array([])

        return (
            np.array(self.association_data.get('time', [])),
            np.array(self.association_data.get('response', []))
        )

    def get_dissociation_data(self):
        """Get just dissociation step as numpy arrays"""
        import numpy as np

        if not self.dissociation_data:
            return np.array([]), np.array([])

        return (
            np.array(self.dissociation_data.get('time', [])),
            np.array(self.dissociation_data.get('response', []))
        )
