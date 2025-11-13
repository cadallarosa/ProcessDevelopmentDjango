from django.db import models


class EmpowerReport(models.Model):
    """
    Report model for Empower-based analytical data (SEC, Titer, etc.)
    Replaces the old Report model in plotly_integration with a cleaner structure
    """
    REPORT_TYPE_CHOICES = [
        ('SEC', 'Size Exclusion Chromatography'),
        ('TITER', 'Titer Analysis'),
        ('CE-SDS', 'Capillary Electrophoresis SDS'),
        ('CIEF', 'Capillary Isoelectric Focusing'),
    ]

    report_id = models.AutoField(primary_key=True)
    report_name = models.CharField(max_length=255, help_text="User-friendly report name")
    project_id = models.CharField(max_length=100, help_text="Project identifier (e.g., SI-54X1)")
    user_initials = models.CharField(max_length=10, help_text="Creator's initials")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default='SEC')

    # Sample data stored as JSON: [{"result_id": 123, "sample_name": "FB1429", "group": "Control"}]
    sample_data = models.JSONField(
        help_text="Array of sample objects with result_id, sample_name, and group"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'empower_report'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['report_type']),
            models.Index(fields=['project_id']),
        ]

    def __str__(self):
        return f"{self.report_name} ({self.report_type}) - {self.report_id}"

    def get_result_ids(self):
        """Extract list of result IDs from sample_data"""
        if not self.sample_data:
            return []
        return [sample['result_id'] for sample in self.sample_data]

    def get_groups(self):
        """Get unique group names from sample_data"""
        if not self.sample_data:
            return []
        groups = set()
        for sample in self.sample_data:
            if 'group' in sample and sample['group']:
                groups.add(sample['group'])
        return sorted(list(groups))
