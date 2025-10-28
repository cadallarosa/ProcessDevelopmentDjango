"""Database query helpers for DN Assignment app."""
from typing import List, Optional
from difflib import get_close_matches
from django.contrib.auth.models import User
from plotly_integration.models import LimsDnAssignment, LimsSampleAnalysis
import pandas as pd


def fuzzy_match_username(input_name: str) -> Optional[str]:
    """
    Use fuzzy matching to find closest username.

    Args:
        input_name: The username input to match

    Returns:
        Closest matching username or None
    """
    all_usernames = list(User.objects.values_list("username", flat=True))
    matches = get_close_matches(input_name.strip(), all_usernames, n=1, cutoff=0.6)
    return matches[0] if matches else None


def get_all_dn_assignments() -> List[dict]:
    """
    Get all DN assignments with related data for table display.

    Returns:
        List of DN assignment dictionaries
    """
    assignments = LimsDnAssignment.objects.select_related("source_material", "source_material__resulting_sample").all()
    df = pd.DataFrame([{
        "dn": a.dn,
        "project_id": a.project_id,
        "unit_operation": a.unit_operation,
        "scouting_details": a.scouting_details,
        "created_by": a.created_by.username if a.created_by else "",
        "assigned_to": a.assigned_to.username if a.assigned_to else "",
        "notes": a.notes,
        "status": a.status,
        "sm_id": f"SM{a.source_material.sm_id}" if a.source_material else "",
        "resulting_pd": a.source_material.resulting_sample.sample_id if (a.source_material and a.source_material.resulting_sample) else "",
        "date_created": a.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "date_updated": a.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        "link": f'[📊 View](/plotly_integration/dash-app/app/AktaChromatogramApp/?dn={a.dn})'
    } for a in assignments])

    if df.empty:
        return []

    # Sort by DN number (descending)
    try:
        df["dn_numeric"] = pd.to_numeric(df["dn"], errors="coerce")
        df = df.sort_values(by="dn_numeric", ascending=False).drop(columns="dn_numeric")
    except Exception:
        df = df.sort_values(by="dn", ascending=False)

    return df.to_dict("records")


def get_dn_table_style_conditional() -> List[dict]:
    """
    Get conditional styling for DN table.

    Returns:
        List of conditional style rules
    """
    return [
        {
            "if": {"filter_query": '{status} = "Completed"', "column_id": "dn"},
            "backgroundColor": "#d4edda",
            "color": "#155724"
        },
        {
            "if": {"filter_query": '{status} = "Pending"', "column_id": "dn"},
            "backgroundColor": "#fff3cd",
            "color": "#856404"
        }
    ]


def get_next_dn_number() -> int:
    """
    Get the next available DN number.

    Returns:
        Next DN number
    """
    last = LimsDnAssignment.objects.order_by("-dn").first()
    if last and isinstance(last.dn, int):
        return last.dn
    elif last and last.dn.isdigit():
        return int(last.dn)
    return 0


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
        "dn": s.dn.dn if s.dn else "",
        "description": s.description or "",
        "sample_date": s.sample_date.strftime("%Y-%m-%d") if s.sample_date else "",
        "a280": s.a280_result if s.a280_result else "",
        "analyst": s.analyst or "",
        "notes": s.notes or "",
        "status": s.status or "in_progress"
    } for s in samples])

    if df.empty:
        return []

    # Sort by sample_id descending
    df = df.sort_values(by="sample_id", ascending=False)
    return df.to_dict("records")


def get_pd_table_style_conditional() -> List[dict]:
    """
    Get conditional styling for PD sample table.

    Returns:
        List of conditional style rules
    """
    return [
        {
            "if": {"filter_query": '{status} = "complete"', "column_id": "sample_id"},
            "backgroundColor": "#d4edda",
            "color": "#155724"
        },
        {
            "if": {"filter_query": '{status} = "in_progress"', "column_id": "sample_id"},
            "backgroundColor": "#fff3cd",
            "color": "#856404"
        },
        {
            "if": {"filter_query": '{status} = "review"', "column_id": "sample_id"},
            "backgroundColor": "#d1ecf1",
            "color": "#0c5460"
        },
    ]


def get_samples_for_dn(dn_number: int, sample_type: Optional[int] = None) -> List[LimsSampleAnalysis]:
    """
    Get samples linked to a specific DN.

    Args:
        dn_number: DN number to query
        sample_type: Optional sample type filter

    Returns:
        List of LimsSampleAnalysis objects
    """
    dn_obj = LimsDnAssignment.objects.filter(dn=dn_number).first()
    if not dn_obj:
        return []

    query = LimsSampleAnalysis.objects.filter(dn=dn_obj)
    if sample_type is not None:
        query = query.filter(sample_type=sample_type)

    return list(query.order_by("sample_id"))


def get_user_options() -> List[dict]:
    """
    Get all usernames for dropdown options.

    Returns:
        List of user option dictionaries
    """
    users = User.objects.all().values_list("username", flat=True)
    return [{"label": u, "value": u} for u in users]
