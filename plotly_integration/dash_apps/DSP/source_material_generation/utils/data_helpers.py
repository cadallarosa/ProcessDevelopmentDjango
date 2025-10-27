"""Database query helpers for Source Material Generation."""
from typing import List, Dict, Optional
from django.db.models import Q
from plotly_integration.models import (
    LimsSourceMaterial,
    LimsSampleAnalysis,
    LimsDnAssignment,
    LimsSourceMaterialStep
)


def get_source_materials_by_project(project_id: str) -> List[LimsSourceMaterial]:
    """Get all source materials for a given project."""
    return list(
        LimsSourceMaterial.objects.filter(project_id__iexact=project_id.strip())
        .order_by("sm_id")
    )


def get_samples_by_project_and_type(
    project_id: str,
    sample_type: int
) -> List[LimsSampleAnalysis]:
    """
    Get samples filtered by project and type.

    Args:
        project_id: Project identifier
        sample_type: 1=UP (includes UP* and UPFB*), 2=FB, 3=PD

    Returns:
        List of LimsSampleAnalysis objects
    """
    # Special handling for UP type - include both UP* and UPFB* samples
    if sample_type == 1:
        samples = LimsSampleAnalysis.objects.filter(
            Q(project_id__iexact=project_id.strip()) &
            (Q(sample_id__startswith='UP') | Q(sample_id__startswith='UPFB')) &
            Q(sample_type=1)
        ).order_by("sample_id")
    else:
        samples = LimsSampleAnalysis.objects.filter(
            project_id__iexact=project_id.strip(),
            sample_type=sample_type
        ).order_by("sample_id")

    result = list(samples)
    print(f"[DEBUG] get_samples_by_project_and_type: project={project_id}, type={sample_type}, found={len(result)}")
    return result


def get_source_material_by_id(sm_id: int) -> Optional[LimsSourceMaterial]:
    """Get a specific source material by ID."""
    return LimsSourceMaterial.objects.filter(sm_id=sm_id).first()


def get_source_material_steps(sm_id: int) -> List[Dict]:
    """
    Get process steps for a source material.

    Returns:
        List of dicts with keys: step, process, notes
    """
    sm = get_source_material_by_id(sm_id)
    if not sm:
        return []

    steps = LimsSourceMaterialStep.objects.filter(
        source_material=sm
    ).order_by("step_number")

    return [
        {
            "step": step.step_number,
            "process": step.process,
            "notes": step.notes
        }
        for step in steps
    ]


def get_pooled_sample_ids(sm_id: int) -> List[str]:
    """Get list of sample IDs pooled in a source material."""
    sm = get_source_material_by_id(sm_id)
    if not sm:
        return []

    return list(sm.samples.values_list("sample_id", flat=True))


def get_next_pd_number() -> int:
    """Get the next available PD sample number."""
    last_pd = (
        LimsSampleAnalysis.objects.filter(sample_id__startswith="PD")
        .order_by("-sample_id")
        .first()
    )

    if last_pd and last_pd.sample_id[2:].isdigit():
        return int(last_pd.sample_id[2:]) + 1

    return 1


def format_sample_dropdown_label(sample: LimsSampleAnalysis) -> str:
    """
    Format a sample for dropdown display.

    Format: "PD123 — Description (2024-01-15)"
    """
    desc = sample.description or "No description"
    date_str = ""
    if sample.sample_date:
        date_str = f" ({sample.sample_date.strftime('%Y-%m-%d')})"

    return f"{sample.sample_id} — {desc}{date_str}"


def format_sm_dropdown_label(sm: LimsSourceMaterial) -> str:
    """
    Format a source material for dropdown display.

    Format: "SM123: Material Name"
    """
    name = sm.name or "Unnamed"
    return f"SM{sm.sm_id}: {name}"


def get_all_project_ids() -> List[str]:
    """
    Get all unique project IDs from sample analysis table.

    Returns:
        Sorted list of unique project IDs
    """
    project_ids = (
        LimsSampleAnalysis.objects
        .values_list('project_id', flat=True)
        .distinct()
        .order_by('project_id')
    )
    return [pid for pid in project_ids if pid]  # Filter out empty/None


def get_next_dn_number() -> int:
    """
    Get the next available DN number.

    Returns:
        Next DN number (integer)
    """
    last_dn = LimsDnAssignment.objects.order_by('-dn').first()

    if last_dn:
        return int(last_dn.dn) + 1

    return 1


def get_all_source_materials(
    project_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict]:
    """
    Get all source materials with optional filters.

    Args:
        project_id: Filter by project ID
        start_date: Filter by created date (ISO format)
        end_date: Filter by created date (ISO format)

    Returns:
        List of dicts formatted for table display
    """
    from django.db.models import Q
    from datetime import datetime

    qs = LimsSourceMaterial.objects.select_related(
        'resulting_sample',
        'resulting_sample__dn'
    ).all()

    # Apply filters
    if project_id:
        qs = qs.filter(project_id__iexact=project_id.strip())

    # Note: LimsSourceMaterial doesn't have created_at in current model
    # If you want date filtering, you'd need to add that field or filter by PD sample date

    source_materials = []
    for sm in qs.order_by('-sm_id'):
        row = {
            'sm_id': sm.sm_id,
            'name': sm.name or 'Unnamed',
            'project_id': sm.project_id or '',
            'dn': sm.resulting_sample.dn.dn if sm.resulting_sample and sm.resulting_sample.dn else None,
            'pd_sample': sm.resulting_sample.sample_id if sm.resulting_sample else 'N/A',
            'final_ph': sm.final_pH,
            'final_conductivity': sm.final_conductivity,
            'final_concentration': sm.final_concentration,
            'final_volume': sm.final_total_volume,
            'created_date': sm.resulting_sample.created_at.strftime('%Y-%m-%d') if sm.resulting_sample else 'N/A',
            'status': 'Active'  # Can add status field to model later
        }
        source_materials.append(row)

    return source_materials


def get_all_dn_assignments(project_id: Optional[str] = None) -> List[Dict]:
    """
    Get all DN assignments for dropdown selection.

    Args:
        project_id: Optionally filter by project

    Returns:
        List of dicts with label and value for dropdown
    """
    qs = LimsDnAssignment.objects.all()

    if project_id:
        qs = qs.filter(project_id__iexact=project_id.strip())

    dn_list = []
    for dn in qs.order_by('-dn')[:100]:  # Limit to last 100 DNs
        label = f"DN{dn.dn} - {dn.project_id} - {dn.unit_operation or 'N/A'}"
        dn_list.append({"label": label, "value": dn.dn})

    # Add "None" option
    dn_list.insert(0, {"label": "None (Unlink)", "value": None})

    return dn_list
