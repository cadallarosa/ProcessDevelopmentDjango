# Sample data - single group with 9 molecules (Real project IDs from Dash app)
SAMPLE_DATA_SINGLE_GROUP = [
    {'id': 0, 'project_id': 'SI-207X6', 'phase': 'Sequence Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'K-1 (Cetux.)', 'annotations': 'Control - Original design'},
    {'id': 1, 'project_id': 'SI-207X3', 'phase': 'Sequence Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv H-L', 'annotations': 'Modified CDR1'},
    {'id': 2, 'project_id': 'SI-207X4', 'phase': 'Sequence Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv H-L', 'annotations': 'Modified CDR2'},
    {'id': 3, 'project_id': 'SI-207X5', 'phase': 'Sequence Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv H-L', 'annotations': 'Vector control'},
    {'id': 4, 'project_id': 'SI-207X10', 'phase': 'Sequence Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv L-H', 'annotations': 'Optimized expression'},
    {'id': 5, 'project_id': 'SI-207X7', 'phase': 'Sequence Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv L-H', 'annotations': 'Optimized linker'},
    {'id': 6, 'project_id': 'SI-207X8', 'phase': 'Sequence Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv L-H', 'annotations': 'Alternative framework'},
    {'id': 7, 'project_id': 'SI-207X9', 'phase': 'Plasmid Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv L-H', 'annotations': 'Stability improved'},
    {'id': 8, 'project_id': 'SI-212X1', 'phase': 'Plasmid Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv L-H', 'annotations': 'Final candidate'}
]

# Sample data - multiple groups (4 groups, 16 molecules total)
SAMPLE_DATA_MULTI_GROUP = [
    # Group 1: K-1 EGFR (9 molecules)
    {'id': 0, 'project_id': 'SI-207X6', 'phase': 'Sequence Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'K-1 (Cetux.)', 'annotations': 'Control - Original design'},
    {'id': 1, 'project_id': 'SI-207X3', 'phase': 'Sequence Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv H-L', 'annotations': 'Modified CDR1'},
    {'id': 2, 'project_id': 'SI-207X4', 'phase': 'Sequence Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv H-L', 'annotations': 'Modified CDR2'},
    {'id': 3, 'project_id': 'SI-207X5', 'phase': 'Sequence Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv H-L', 'annotations': 'Vector control'},
    {'id': 4, 'project_id': 'SI-207X10', 'phase': 'Sequence Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv L-H', 'annotations': 'Optimized expression'},
    {'id': 5, 'project_id': 'SI-207X7', 'phase': 'Sequence Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv L-H', 'annotations': 'Optimized linker'},
    {'id': 6, 'project_id': 'SI-207X8', 'phase': 'Sequence Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv L-H', 'annotations': 'Alternative framework'},
    {'id': 7, 'project_id': 'SI-207X9', 'phase': 'Plasmid Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv L-H', 'annotations': 'Stability improved'},
    {'id': 8, 'project_id': 'SI-212X1', 'phase': 'Plasmid Design', 'group': 'K-1 EGFR (Cetux.) Alternatives', 'subset': 'Cetux, scFv L-H', 'annotations': 'Final candidate'},
    # Group 2: K-2 EGFR (2 molecules)
    {'id': 9, 'project_id': 'SI-208X1', 'phase': 'Sequence Design', 'group': 'K-2 EGFR Variants', 'subset': 'Control', 'annotations': 'K-2 reference'},
    {'id': 10, 'project_id': 'SI-208X2', 'phase': 'Sequence Design', 'group': 'K-2 EGFR Variants', 'subset': 'Modified', 'annotations': 'Enhanced binding'},
    # Group 3: K-3 EGFR (2 molecules)
    {'id': 11, 'project_id': 'SI-209X1', 'phase': 'Plasmid Design', 'group': 'K-3 EGFR Variants', 'subset': 'Control', 'annotations': 'K-3 reference'},
    {'id': 12, 'project_id': 'SI-209X2', 'phase': 'Plasmid Design', 'group': 'K-3 EGFR Variants', 'subset': 'High Affinity', 'annotations': 'Improved K_D'},
    # Group 4: K-9 EGFR (3 molecules)
    {'id': 13, 'project_id': 'SI-215X1', 'phase': 'Transfection Purification', 'group': 'K-9 EGFR Variants', 'subset': 'Control', 'annotations': 'K-9 reference'},
    {'id': 14, 'project_id': 'SI-215X2', 'phase': 'Transfection Purification', 'group': 'K-9 EGFR Variants', 'subset': 'Optimized', 'annotations': 'Production optimized'},
    {'id': 15, 'project_id': 'SI-215X3', 'phase': 'UCOE Clone', 'group': 'K-9 EGFR Variants', 'subset': 'Clone A', 'annotations': 'Stable cell line'}
]

PHASE_OPTIONS = ['Sequence Design', 'Plasmid Design', 'Transfection Purification', 'UCOE Clone', 'CLD Development']
