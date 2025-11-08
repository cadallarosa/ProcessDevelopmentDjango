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
            time.sleep(2)  # Delay import by 2 seconds
            try:
                # Analytical Apps - General
                import plotly_integration.dash_apps.Analytical.create_report.create_report_app
                import plotly_integration.dash_apps.Analytical.titer.titer_analysis_app
                import plotly_integration.dash_apps.Analytical.titer.create_titer_report_app
                import plotly_integration.dash_apps.Analytical.plasma_stability_v4.app

                # SEC Apps
                import plotly_integration.dash_apps.Analytical.sec_app_embedded.app
                import plotly_integration.dash_apps.Analytical.sec_app.app
                import plotly_integration.dash_apps.Analytical.sec_app.create_sec_report_app
                import plotly_integration.dash_apps.Analytical.sec_app_flexible.sec_report_app_simple
                import plotly_integration.dash_apps.Analytical.sec_app_flexible.sec_report_app_simple_v2

                # Empower Apps
                import plotly_integration.process_development.downstream_processing.empower.create_report_app
                import plotly_integration.process_development.downstream_processing.empower.column_analysis_app

                # CE-SDS Apps
                import plotly_integration.process_development.analytical.ce_sds.app.create_report_app
                import plotly_integration.process_development.analytical.ce_sds.app.app

                # cIEF Apps
                import plotly_integration.process_development.analytical.cief.create_report_app
                import plotly_integration.process_development.analytical.cief.cief_analysis_app
                import plotly_integration.process_development.analytical.cief_empower.app

                # Octet Apps
                import plotly_integration.dash_apps.Analytical.octet.octet_analysis_app
                import plotly_integration.dash_apps.Analytical.octet_app.octet_analysis_app
                import plotly_integration.process_development.analytical.octet.apps.octet_analysis_app_v2
                import plotly_integration.process_development.analytical.octet.apps.kinetic_analysis.dashboard.octet_kinetics_dash_app

                # LC-MS Glycan Analysis Apps
                import plotly_integration.process_development.analytical.lc_ms.glycan_analysis.glycan_data_import_app
                import plotly_integration.process_development.analytical.lc_ms.glycan_analysis.glycan_create_report_app
                import plotly_integration.process_development.analytical.lc_ms.glycan_analysis.glycan_analysis_app

                # LC-MS Mass Check Apps
                import plotly_integration.process_development.analytical.lc_ms.mass_check.mass_check_data_import_app
                import plotly_integration.process_development.analytical.lc_ms.mass_check.mass_check_create_report_app
                import plotly_integration.process_development.analytical.lc_ms.mass_check.mass_check_report_app
                import plotly_integration.process_development.analytical.lc_ms.homepage

                # Akta Apps
                import plotly_integration.dash_apps.akta_report_app.main_app
                import plotly_integration.process_development.downstream_processing.akta.akta_app.akta_app
                import plotly_integration.process_development.downstream_processing.akta.opcua_server.test.akta_import_app

                # Sartoflow Smart Apps
                import plotly_integration.process_development.downstream_processing.sartoflow_smart.viral_filtration_app
                import plotly_integration.process_development.downstream_processing.sartoflow_smart.ufdf_app
                import plotly_integration.process_development.downstream_processing.sartoflow_smart.create_ufdf_experiment
                import plotly_integration.process_development.downstream_processing.sartoflow_smart.create_vf_experiment

                # CLD Mass Check Apps
                import plotly_integration.process_development.cld_mass_check.cld_mass_check_import_app

                # Protein Engineering Apps
                import plotly_integration.dash_apps.protein_engineering.image_arrangement.app

                # Nova Flex Apps
                import plotly_integration.process_development.cell_culture.nova_flex_2.nova_create_report_app
                import plotly_integration.process_development.cell_culture.nova_flex_2.nova_report_app
                import plotly_integration.process_development.cell_culture.nova_flex_2.nova_data_viewer

                # ViCell Apps
                import plotly_integration.process_development.cell_culture.vicell.vicell_create_report_app
                import plotly_integration.process_development.cell_culture.vicell.vicell_report_app
                import plotly_integration.process_development.cell_culture.vicell.vicell_import_monitor

                # DasGip Apps
                import plotly_integration.process_development.cell_culture.dasgip.dasgip_import_app
                import plotly_integration.process_development.cell_culture.dasgip.dasgip_report_app

                # LIMS Apps
                import plotly_integration.process_development.lims.sample_analysis_app
                import plotly_integration.process_development.lims.upstream_samples_app

                # Formulation Apps
                import plotly_integration.process_development.formulation.stability_app.formulation_stability_app_simple
                import plotly_integration.process_development.formulation.formulation_experiment_manager
                import plotly_integration.process_development.formulation.data_entry_app
                import plotly_integration.process_development.formulation.experiment_creation_app
                import plotly_integration.process_development.formulation.formulation_dashboard_app
                import plotly_integration.process_development.formulation.sample_management_app
                import plotly_integration.process_development.formulation.formulation_design_app
                import plotly_integration.process_development.formulation.formulation_visualization_app

                # CLD Project Management Apps
                import plotly_integration.cld.project_management_app
                import plotly_integration.cld.clonality_report_analyzer
                import plotly_integration.cld.vicell.vicell_report_app
                import plotly_integration.cld.nova_flex_II.nova_report_app

                # DSP Apps
                import plotly_integration.process_development.lims.dn_assignment_app
                import plotly_integration.process_development.lims.dn_assignment_app_v2
                import plotly_integration.dash_apps.DSP.experiment_set
                import plotly_integration.dash_apps.DSP.experiment_set_improved
                import plotly_integration.dash_apps.DSP.experiment_set_refined
                import plotly_integration.dash_apps.DSP.source_material_generation
                import plotly_integration.dash_apps.DSP.dn_assignment
                from plotly_integration.dash_apps.DSP.pd_samples_management import create_pd_samples_app
                create_pd_samples_app()
                from plotly_integration.dash_apps.DSP.pd_analytics_dashboard import create_pd_analytics_app
                create_pd_analytics_app()

                # USP Apps
                import plotly_integration.usp.media_tracking_app.media_tracking_app
                import plotly_integration.usp.experiment_management_app.experiment_management_app
                import plotly_integration.usp.vicell.vicell_report_app
                import plotly_integration.usp.nova_flex_2.nova_report_app
                import plotly_integration.usp.nova_flex_2.nova_data_viewer
                import plotly_integration.usp.titer.titer_report_app

                # Project Management Apps
                import plotly_integration.project_management.app

                # Deprecated Apps
                import plotly_integration.deprecated.homepage

                # PD Dashboard Apps
                try:
                    import plotly_integration.pd_dashboard.main_app
                    import plotly_integration.pd_dashboard.home_dashboard_app
                    print('PD Dashboard App loaded successfully')
                except Exception as e:
                    print(f'PD Dashboard App failed to load: {e}')





                print('All Apps Loaded')


            except Exception as e:
                print(f"Error loading modules: {e}")

        # Run the delayed import in a separate thread
        thread = threading.Thread(target=delayed_import)
        thread.start()

