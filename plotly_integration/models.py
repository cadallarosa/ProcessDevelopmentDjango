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

    id = models.AutoField(primary_key=True)
    experiment_id = models.CharField(max_length=100, unique=True)
    experiment_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
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

    id = models.AutoField(primary_key=True)
    process_step = models.ForeignKey(USPProcessStep, on_delete=models.CASCADE, related_name='seed_trains')
    seed_train_id = models.CharField(max_length=100, unique=True)  # UPST####
    vessel_type = models.CharField(max_length=20, choices=SEED_VESSEL_TYPE_CHOICES)
    thaw_date = models.DateField()
    culture_volume = models.FloatField(help_text="mL")
    cell_line = models.CharField(max_length=100)
    media_type = models.CharField(max_length=100)
    passage_number = models.IntegerField(null=True, blank=True)
    vial_id = models.CharField(max_length=100, blank=True, null=True)
    viability_at_thaw = models.FloatField(null=True, blank=True, help_text="percentage")
    cell_density_at_thaw = models.FloatField(null=True, blank=True, help_text="cells/mL")
    notes = models.TextField(blank=True, null=True)
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

    id = models.AutoField(primary_key=True)
    process_step = models.ForeignKey(USPProcessStep, on_delete=models.CASCADE, related_name='vessels')
    seed_train = models.ForeignKey(USPSeedTrain, on_delete=models.SET_NULL, null=True, blank=True, related_name='downstream_vessels')
    vessel_id = models.CharField(max_length=100)  # UPFB####
    vessel_type = models.CharField(max_length=20, choices=VESSEL_TYPE_CHOICES)
    cell_line = models.CharField(max_length=100, blank=True, null=True)
    media_type = models.CharField(max_length=100, blank=True, null=True)
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
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usp_vessel'
        unique_together = ('process_step', 'vessel_id')
        ordering = ['process_step', 'vessel_id']

    def __str__(self):
        return f"{self.vessel_id} ({self.vessel_type})"


class USPMediaRecipe(models.Model):
    """Model for storing media recipe templates"""
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


class USPMediaRecipeComponent(models.Model):
    """Model for storing components in media recipes"""
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
        ('other', 'Other'),
    ]

    UNIT_CHOICES = [
        ('g/L', 'g/L'),
        ('mg/L', 'mg/L'),
        ('mL/L', 'mL/L'),
        ('µL/L', 'µL/L'),
        ('mM', 'mM'),
        ('µM', 'µM'),
        ('%', '%'),
    ]

    id = models.AutoField(primary_key=True)
    recipe = models.ForeignKey(USPMediaRecipe, on_delete=models.CASCADE, related_name='recipe_components')
    component_type = models.CharField(max_length=50, choices=COMPONENT_TYPE_CHOICES)
    component_name = models.CharField(max_length=200)
    catalog_number = models.CharField(max_length=100, blank=True, null=True)
    concentration_per_liter = models.FloatField(help_text="Amount per liter of final media")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    vendor = models.CharField(max_length=100, blank=True, null=True)
    preparation_notes = models.TextField(blank=True, null=True)
    order_index = models.IntegerField(default=0, help_text="Order for adding components")

    class Meta:
        db_table = 'usp_media_recipe_component'
        ordering = ['recipe', 'order_index', 'component_name']

    def __str__(self):
        return f"{self.component_name} ({self.concentration_per_liter} {self.unit})"


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