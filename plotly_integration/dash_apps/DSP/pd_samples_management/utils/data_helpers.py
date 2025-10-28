"""Database query helpers for PD Samples Management app."""
from typing import List, Optional
from plotly_integration.models import LimsSampleAnalysis, LimsDnAssignment
import pandas as pd


def get_all_pd_samples() -> List[dict]:
    """
    Get all PD samples with related data for table display.

    Returns:
        List of PD sample dictionaries
    """
    samples = LimsSampleAnalysis.objects.filter(
        sample_type=3  # PD type
    ).select_related("dn").all()

    df = pd.DataFrame([{
        "sample_id": s.sample_id,
        "project_id": s.project_id or "",
        "dn": f"DN{s.dn.dn}" if s.dn else "",
        "description": s.description or "",
        "sample_date": s.sample_date.strftime("%Y-%m-%d") if s.sample_date else "",
        "a280": s.a280_result if s.a280_result else "",
        "analyst": s.analyst or "",
        "status": s.status or "In Progress",
        "notes": s.notes or "",
    } for s in samples])

    if df.empty:
        return []

    # Sort by sample_id descending
    df = df.sort_values(by="sample_id", ascending=False)
    return df.to_dict("records")


def get_next_pd_number() -> int:
    """
    Get the next available PD sample number.

    Returns:
        Next PD number
    """
    last = LimsSampleAnalysis.objects.filter(
        sample_id__startswith="PD"
    ).order_by("-sample_id").first()

    if last and last.sample_id[2:].isdigit():
        return int(last.sample_id[2:])
    return 0


def get_available_dns() -> List[dict]:
    """
    Get all DNs for dropdown options.

    Returns:
        List of DN option dictionaries
    """
    dns = LimsDnAssignment.objects.all().order_by("-dn")[:100]  # Last 100 DNs
    return [
        {
            "label": f"DN{dn.dn} - {dn.project_id or 'No Project'} - {dn.unit_operation or 'N/A'}",
            "value": dn.dn
        }
        for dn in dns
    ]


def get_pd_sample_by_id(sample_id: str) -> Optional[LimsSampleAnalysis]:
    """
    Get a specific PD sample by ID.

    Args:
        sample_id: Sample ID to query

    Returns:
        LimsSampleAnalysis object or None
    """
    try:
        return LimsSampleAnalysis.objects.get(sample_id=sample_id)
    except LimsSampleAnalysis.DoesNotExist:
        return None


def get_unique_project_ids() -> List[str]:
    """
    Get unique project IDs from PD samples.

    Returns:
        List of unique project IDs
    """
    projects = LimsSampleAnalysis.objects.filter(
        sample_type=3,
        project_id__isnull=False
    ).exclude(project_id="").values_list("project_id", flat=True).distinct()

    return sorted(list(projects))


def get_unique_dn_numbers() -> List[dict]:
    """
    Get unique DN numbers from PD samples.

    Returns:
        List of DN option dictionaries
    """
    samples = LimsSampleAnalysis.objects.filter(
        sample_type=3,
        dn__isnull=False
    ).select_related("dn").distinct()

    dn_set = set()
    for sample in samples:
        if sample.dn:
            dn_set.add(sample.dn.dn)

    dns = LimsDnAssignment.objects.filter(dn__in=dn_set).order_by("-dn")

    return [
        {
            "label": f"DN{dn.dn}",
            "value": f"DN{dn.dn}"
        }
        for dn in dns
    ]


def get_sample_genealogy(sample_id: str) -> dict:
    """
    Get the full genealogy/lineage for a PD sample.

    Args:
        sample_id: PD sample ID to trace

    Returns:
        Dictionary containing nodes and edges for flowchart visualization
    """
    from plotly_integration.models import LimsSourceMaterial, LimsUpstreamSamples, USPBioreactorRun

    nodes = []
    edges = []

    try:
        # Get the PD sample
        pd_sample = get_pd_sample_by_id(sample_id)
        if not pd_sample:
            return {"nodes": [], "edges": []}

        # Add PD sample node
        nodes.append({
            "id": f"pd_{sample_id}",
            "label": sample_id,
            "type": "PD",
            "data": {
                "Project": pd_sample.project_id or "N/A",
                "Description": pd_sample.description or "",
                "Date": pd_sample.sample_date.strftime("%Y-%m-%d") if pd_sample.sample_date else "",
                "A280": f"{pd_sample.a280_result} mg/mL" if pd_sample.a280_result else "N/A",
                "Analyst": pd_sample.analyst or "",
                "Status": pd_sample.status or ""
            }
        })

        # Trace back to DN experiment
        if pd_sample.dn:
            dn = pd_sample.dn
            nodes.append({
                "id": f"dn_{dn.dn}",
                "label": f"DN{dn.dn}",
                "type": "DN",
                "data": {
                    "Project": dn.project_id or "",
                    "Unit Operation": dn.unit_operation or "",
                    "Created By": dn.created_by.username if dn.created_by else "",
                    "Assigned To": dn.assigned_to.username if dn.assigned_to else "",
                    "Status": dn.status or "",
                    "Notes": dn.notes or ""
                }
            })
            edges.append({"source": f"dn_{dn.dn}", "target": f"pd_{sample_id}", "label": "Processed"})

            # Trace back to Source Material (SM is linked to DN, not PD directly)
            sm = dn.source_material  # Use the FK from DN to SM
            if sm:
                nodes.append({
                    "id": f"sm_{sm.sm_id}",
                    "label": f"SM{sm.sm_id}",
                    "type": "SM",
                    "data": {
                        "Name": sm.name or "",
                        "Project": sm.project_id or "",
                        "Description": sm.source_description or "",
                        "Volume": f"{sm.source_volume} mL" if sm.source_volume else "N/A",
                        "Concentration": f"{sm.final_concentration} mg/mL" if sm.final_concentration else "N/A",
                        "pH": str(sm.final_pH) if sm.final_pH else "N/A",
                        "Conductivity": f"{sm.final_conductivity} mS/cm" if sm.final_conductivity else "N/A",
                        "Created By": sm.created_by.username if sm.created_by else ""
                    }
                })
                edges.append({"source": f"sm_{sm.sm_id}", "target": f"dn_{dn.dn}", "label": "Pooled"})

                # Trace to input samples (UP/FB samples used in SM)
                input_samples = sm.samples.all()
                for idx, input_sample in enumerate(input_samples):
                    nodes.append({
                        "id": f"input_{input_sample.sample_id}",
                        "label": input_sample.sample_id,
                        "type": "UP" if input_sample.sample_type == 1 else ("FB" if input_sample.sample_type == 2 else "Other"),
                        "data": {
                            "Project": input_sample.project_id or "",
                            "Description": input_sample.description or "",
                            "Date": input_sample.sample_date.strftime("%Y-%m-%d") if input_sample.sample_date else "",
                            "Analyst": input_sample.analyst or "",
                            "A280": f"{input_sample.a280_result} mg/mL" if input_sample.a280_result else "N/A"
                        }
                    })
                    edges.append({"source": f"input_{input_sample.sample_id}", "target": f"sm_{sm.sm_id}", "label": f"Input {idx+1}"})

                    # Trace UP samples to bioreactor runs
                    if input_sample.up:
                        up_sample = input_sample.up
                        nodes.append({
                            "id": f"up_{up_sample.sample_id}",
                            "label": up_sample.sample_id,
                            "type": "USP",
                            "data": {
                                "Vessel": up_sample.vessel or "",
                                "Volume": f"{up_sample.volume} L" if up_sample.volume else "N/A",
                                "VCD": f"{up_sample.vcd:.2e} cells/mL" if up_sample.vcd else "N/A",
                                "Viability": f"{up_sample.viability}%" if up_sample.viability else "N/A",
                                "Titer": f"{up_sample.titer} g/L" if up_sample.titer else "N/A",
                                "Analyst": up_sample.operator or ""
                            }
                        })
                        edges.append({"source": f"up_{up_sample.sample_id}", "target": f"input_{input_sample.sample_id}", "label": "Harvest"})

        # Add analytical results for PD sample
        analytical_results = []
        if pd_sample.sec_result:
            analytical_results.append(("SEC", f"sec_{pd_sample.sec_result.sample_id.sample_id}", {
                "Main Peak": f"{pd_sample.sec_result.main_peak}%" if pd_sample.sec_result.main_peak else "N/A",
                "HMW": f"{pd_sample.sec_result.hmw}%" if pd_sample.sec_result.hmw else "N/A",
                "LMW": f"{pd_sample.sec_result.lmw}%" if pd_sample.sec_result.lmw else "N/A",
                "QC Pass": "Yes" if pd_sample.sec_result.qc_pass else "No"
            }))
        if pd_sample.titer_result:
            analytical_results.append(("Titer", f"titer_{pd_sample.titer_result.sample_id.sample_id}", {
                "Titer": f"{pd_sample.titer_result.titer} g/L" if pd_sample.titer_result.titer else "N/A",
                "QC Pass": "Yes" if pd_sample.titer_result.qc_pass else "No"
            }))
        if pd_sample.ce_sds_result:
            analytical_results.append(("CE-SDS", f"cesds_{pd_sample.ce_sds_result.sample_id.sample_id}", {}))
        if pd_sample.cief_result:
            analytical_results.append(("cIEF", f"cief_{pd_sample.cief_result.sample_id.sample_id}", {}))
        if pd_sample.mass_check_result:
            analytical_results.append(("Mass Check", f"mass_{pd_sample.mass_check_result.sample_id.sample_id}", {
                "Expected": f"{pd_sample.mass_check_result.expected_mass} Da" if pd_sample.mass_check_result.expected_mass else "N/A",
                "Observed": f"{pd_sample.mass_check_result.observed_mass} Da" if pd_sample.mass_check_result.observed_mass else "N/A"
            }))
        if pd_sample.glycan_result:
            analytical_results.append(("Glycan", f"glycan_{pd_sample.glycan_result.sample_id.sample_id}", {}))
        if pd_sample.hcp_result:
            analytical_results.append(("HCP", f"hcp_{pd_sample.hcp_result.sample_id.sample_id}", {}))
        if pd_sample.proa_result:
            analytical_results.append(("ProA", f"proa_{pd_sample.proa_result.sample_id.sample_id}", {}))

        for assay_name, node_id, data in analytical_results:
            nodes.append({
                "id": node_id,
                "label": assay_name,
                "type": "Analytical",
                "data": data
            })
            edges.append({"source": f"pd_{sample_id}", "target": node_id, "label": "Analyzed"})

        return {"nodes": nodes, "edges": edges}

    except Exception as e:
        print(f"Error tracing genealogy for {sample_id}: {e}")
        return {"nodes": [], "edges": []}
