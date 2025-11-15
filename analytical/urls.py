from django.urls import path
from .views import sec, sec_report_creation

app_name = "analytical"

urlpatterns = [
    # SEC App - Main pages
    path("sec/", sec.index, name="sec_index"),
    path("sec/create-report/", sec_report_creation.create_report_page, name="sec_create_report_page"),

    # Legacy HTMX endpoints (keep for backward compatibility)
    path("sec/update-plot/", sec.update_plot, name="sec_update_plot"),
    path("sec/load-report/", sec.load_report, name="sec_load_report"),

    # JSON API endpoints for tiered loading
    path("sec/api/list-reports/", sec.list_reports, name="sec_list_reports"),
    path("sec/api/list-samples/", sec_report_creation.list_samples, name="sec_list_samples"),
    path("sec/api/create-report/", sec_report_creation.create_report_api, name="sec_create_report"),
    path("sec/api/get-report/<int:report_id>/", sec_report_creation.get_report, name="sec_get_report"),
    path("sec/api/update-report/<int:report_id>/", sec_report_creation.update_report_api, name="sec_update_report"),
    path("sec/api/load-initial/<int:report_id>/", sec.load_initial_data, name="sec_load_initial"),
    path("sec/api/load-channel/<int:report_id>/<str:channel>/", sec.load_channel_data, name="sec_load_channel"),
    path("sec/api/load-results/<int:report_id>/", sec.load_results_table, name="sec_load_results"),
    path("sec/api/load-std/<int:report_id>/", sec.load_std_analysis, name="sec_load_std"),
    path("sec/api/save-settings/", sec.save_settings, name="sec_save_settings"),
    path("sec/api/export-excel/<int:report_id>/", sec.export_excel, name="sec_export_excel"),
    path("sec/api/export-ppt/<int:report_id>/", sec.export_ppt, name="sec_export_ppt"),
    path("sec/api/get-chromatograms/", sec.get_chromatograms, name="sec_get_chromatograms"),
]
