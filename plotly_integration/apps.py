import threading
import time
from django.apps import AppConfig

class PlotlyIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plotly_integration'

    def ready(self):
        from django.core.checks import run_checks
        run_checks()  # Ensures Django settings are loaded before importing

        def delayed_import():
            time.sleep(5)  # Delay import by 5 seconds
            try:
                import plotly_integration.process_development.downstream_processing.empower.create_report_app
                import plotly_integration.homepage
                import plotly_integration.process_development.downstream_processing.empower.database_manager
                import plotly_integration.process_development.downstream_processing.empower.sec_report_app
                import plotly_integration.process_development.downstream_processing.empower.sec_report_app.app
                import plotly_integration.process_development.downstream_processing.empower.titer_report_app
                import plotly_integration.process_development.downstream_processing.empower.column_analysis_app
                import plotly_integration.process_development.downstream_processing.sartoflow_smart.viral_filtration_app
                import plotly_integration.process_development.downstream_processing.sartoflow_smart.ufdf_app
                import plotly_integration.process_development.downstream_processing.sartoflow_smart.create_experiment
                import plotly_integration.process_development.downstream_processing.sartoflow_smart.create_vf_experiment
                import plotly_integration.process_development.downstream_processing.akta.opcua_server.test_files.akta_data_import

                import plotly_integration.process_development.downstream_processing.akta.akta_app.akta_app
                import \
                    plotly_integration.process_development.downstream_processing.akta.opcua_server.test.akta_import_app
                import plotly_integration.process_development.cld_mass_check.cld_mass_check_import_app
                import protein_engineering.homepage
                import protein_engineering.sec_report_app
                import protein_engineering.create_report_app
                import plotly_integration.process_development.cell_culture.nova_flex_2.nova_data_import_app
                import plotly_integration.process_development.cell_culture.nova_flex_2.nova_create_report_app
                import plotly_integration.process_development.cell_culture.nova_flex_2.nova_report_app
                import plotly_integration.process_development.cell_culture.vicell.vicell_data_import_app
                import plotly_integration.process_development.cell_culture.vicell.vicell_create_report_app
                import plotly_integration.process_development.cell_culture.vicell.vicell_report_app

                #SEC
                import plotly_integration.dash_apps.sec_app_embedded.app
                import plotly_integration.dash_apps.sec_app.app

                #Akta
                import plotly_integration.dash_apps.akta_report_app.main_app


                #LC_MS Glycan Analysis Apps
                import plotly_integration.process_development.analytical.lc_ms.glycan_analysis.glycan_data_import_app
                import plotly_integration.process_development.analytical.lc_ms.glycan_analysis.glycan_create_report_app
                import plotly_integration.process_development.analytical.lc_ms.glycan_analysis.glycan_analysis_app

                #LC_MS Apps
                import plotly_integration.process_development.analytical.lc_ms.mass_check.mass_check_data_import_app
                import plotly_integration.process_development.analytical.lc_ms.mass_check.mass_check_create_report_app
                import plotly_integration.process_development.analytical.lc_ms.mass_check.mass_check_report_app
                import plotly_integration.process_development.analytical.lc_ms.homepage

                #CE_SDS Apps
                import plotly_integration.process_development.analytical.ce_sds.data_import_app
                import plotly_integration.process_development.analytical.ce_sds.create_report_app
                import plotly_integration.process_development.analytical.ce_sds.ce_sds_analysis_app

                #cIEF Apps
                import plotly_integration.process_development.analytical.cief.data_import_app
                import plotly_integration.process_development.analytical.cief.create_report_app
                import plotly_integration.process_development.analytical.cief.cief_sds_analysis_app

                #Lims Apps
                import plotly_integration.process_development.lims.dn_assignment_app
                import plotly_integration.process_development.lims.sample_analysis_app
                import plotly_integration.process_development.lims.upstream_samples_app
                import plotly_integration.process_development.lims.cld_samples_app
                import plotly_integration.process_development.lims.cld_sample_manager.app

                import plotly_integration.process_development.lims.cld_dashboard.CLDDashboardApp2
                import plotly_integration.cld_dashboard.main_app



                print('All Apps Loaded')


            except Exception as e:
                print(f"Error loading modules: {e}")

        # Run the delayed import in a separate thread
        thread = threading.Thread(target=delayed_import)
        thread.start()

