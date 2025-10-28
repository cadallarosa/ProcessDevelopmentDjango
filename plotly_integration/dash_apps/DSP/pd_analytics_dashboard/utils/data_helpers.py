"""Data helpers for PD Analytics Dashboard."""
from typing import List
from plotly_integration.models import LimsSampleAnalysis
import pandas as pd


def get_all_analytics_data() -> List[dict]:
    """
    Get all PD samples with joined analytical results.

    Returns:
        List of dictionaries with sample and analytical data
    """
    samples = LimsSampleAnalysis.objects.filter(
        sample_type=3  # PD type
    ).select_related(
        'sec_result',
        'titer_result',
        'mass_check_result',
        'glycan_result',
        'ce_sds_result',
        'cief_result',
        'hcp_result',
        'proa_result',
        'dn'
    ).all()

    data = []
    for s in samples:
        row = {
            "sample_id": s.sample_id,
            "project_id": s.project_id or "",
            "dn": f"DN{s.dn.dn}" if s.dn else "",
            "sample_date": s.sample_date.strftime("%Y-%m-%d") if s.sample_date else "",
            "a280": f"{s.a280_result:.2f}" if s.a280_result else "",
            "analyst": s.analyst or "",
            "status": s.status or "",
        }

        # SEC Results
        if s.sec_result:
            row["sec_main_peak"] = f"{s.sec_result.main_peak:.1f}" if s.sec_result.main_peak else ""
            row["sec_hmw"] = f"{s.sec_result.hmw:.1f}" if s.sec_result.hmw else ""
            row["sec_lmw"] = f"{s.sec_result.lmw:.1f}" if s.sec_result.lmw else ""
            row["sec_qc"] = "Pass" if s.sec_result.qc_pass else "Fail"
        else:
            row["sec_main_peak"] = ""
            row["sec_hmw"] = ""
            row["sec_lmw"] = ""
            row["sec_qc"] = ""

        # Titer Results
        if s.titer_result:
            row["titer"] = f"{s.titer_result.titer:.2f}" if s.titer_result.titer else ""
            row["titer_qc"] = "Pass" if s.titer_result.qc_pass else "Fail"
        else:
            row["titer"] = ""
            row["titer_qc"] = ""

        # Mass Check Results
        if s.mass_check_result:
            row["mass_expected"] = f"{s.mass_check_result.expected_mass:.0f}" if s.mass_check_result.expected_mass else ""
            row["mass_observed"] = f"{s.mass_check_result.observed_mass:.0f}" if s.mass_check_result.observed_mass else ""
        else:
            row["mass_expected"] = ""
            row["mass_observed"] = ""

        # Other assays - just indicate presence
        row["glycan"] = "Yes" if s.glycan_result else ""
        row["ce_sds"] = "Yes" if s.ce_sds_result else ""
        row["cief"] = "Yes" if s.cief_result else ""
        row["hcp"] = "Yes" if s.hcp_result else ""
        row["proa"] = "Yes" if s.proa_result else ""

        data.append(row)

    # Sort by sample_id descending
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values(by="sample_id", ascending=False)
        return df.to_dict("records")

    return []


def get_unique_projects() -> List[str]:
    """Get unique project IDs."""
    projects = LimsSampleAnalysis.objects.filter(
        sample_type=3,
        project_id__isnull=False
    ).exclude(project_id="").values_list("project_id", flat=True).distinct()
    return sorted(list(projects))
