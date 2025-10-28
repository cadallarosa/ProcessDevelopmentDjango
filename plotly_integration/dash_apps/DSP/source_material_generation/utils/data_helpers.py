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


def format_samples_for_pooling_table(samples: List[LimsSampleAnalysis]) -> List[Dict]:
    """
    Format samples for the pooling DataTable.

    Args:
        samples: List of LimsSampleAnalysis objects

    Returns:
        List of dicts with sample info formatted for table display
    """
    SAMPLE_TYPE_MAP = {1: "UP/UPFB", 2: "FB", 3: "PD"}

    rows = []
    for sample in samples:
        row = {
            "sample_id": sample.sample_id,
            "sample_type_label": SAMPLE_TYPE_MAP.get(sample.sample_type, "Unknown"),
            "dn": f"DN{sample.dn.dn}" if sample.dn else "",
            "project_id": sample.project_id or "",
            "description": sample.description or "",
            "sample_date": sample.sample_date.strftime("%Y-%m-%d") if sample.sample_date else "",
            "a280": f"{sample.a280_result:.2f}" if sample.a280_result else "",
        }
        rows.append(row)

    return rows


def format_sm_dropdown_label(sm: LimsSourceMaterial) -> str:
    """
    Format a source material for dropdown display.

    Format: "SM123: Material Name"
    """
    name = sm.name or "Unnamed"
    return f"SM{sm.sm_id}: {name}"


def normalize_project_id(project_id: str) -> str:
    """
    Normalize project ID to standard format (e.g., SI-49T5).

    Examples:
        - "49t5" -> "SI-49T5"
        - "49T5" -> "SI-49T5"
        - "si-49t5" -> "SI-49T5"
        - "SI-49T5" -> "SI-49T5"

    Args:
        project_id: Raw project ID string

    Returns:
        Normalized project ID
    """
    if not project_id:
        return ""

    pid = project_id.strip().upper()

    # If it doesn't start with "SI-", try to add it
    if not pid.startswith("SI-"):
        # Check if it's just a number pattern like "49T5"
        if pid and (pid[0].isdigit() or len(pid) < 10):
            pid = f"SI-{pid}"

    return pid


def get_all_project_ids(order_by: str = "recent") -> List[str]:
    """
    Get all unique project IDs from sample analysis table.

    Args:
        order_by: "recent" (most recent first), "numeric" (by number), or "alpha" (alphabetical)

    Returns:
        Ordered list of normalized unique project IDs
    """
    from django.db.models import Max

    if order_by == "recent":
        # Order by most recent sample_date for each project
        project_dates = (
            LimsSampleAnalysis.objects
            .values('project_id')
            .annotate(latest_date=Max('sample_date'))
            .order_by('-latest_date')
        )
        project_ids = [p['project_id'] for p in project_dates if p['project_id']]
    elif order_by == "numeric":
        # Try to extract numeric part and sort
        all_pids = (
            LimsSampleAnalysis.objects
            .values_list('project_id', flat=True)
            .distinct()
        )
        project_ids = sorted(
            [pid for pid in all_pids if pid],
            key=lambda x: (
                # Extract number if exists, otherwise use string
                int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else 0,
                x
            ),
            reverse=True
        )
    else:  # alphabetical
        project_ids = (
            LimsSampleAnalysis.objects
            .values_list('project_id', flat=True)
            .distinct()
            .order_by('project_id')
        )
        project_ids = [pid for pid in project_ids if pid]

    # Normalize all project IDs and remove duplicates while preserving order
    normalized = []
    seen = set()
    for pid in project_ids:
        norm_pid = normalize_project_id(pid)
        if norm_pid and norm_pid not in seen:
            normalized.append(norm_pid)
            seen.add(norm_pid)

    return normalized


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
