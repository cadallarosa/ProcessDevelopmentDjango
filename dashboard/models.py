from django.db import models


class NavigationSection(models.Model):
    """
    Represents a collapsible section in the sidebar navigation.
    Example: 'Analytical', 'Development', 'Process Development'
    """
    title = models.CharField(max_length=100, help_text="Display name for the navigation section")
    icon = models.CharField(
        max_length=50,
        help_text="Font Awesome icon class (e.g., 'fa-microscope', 'fa-flask')",
        blank=True
    )
    order = models.IntegerField(default=0, help_text="Display order (lower numbers appear first)")
    is_collapsible = models.BooleanField(
        default=True,
        help_text="If False, this section acts as a direct link (no sub-items)"
    )
    url = models.CharField(
        max_length=200,
        blank=True,
        help_text="URL for non-collapsible sections (direct links)"
    )
    is_active = models.BooleanField(default=True, help_text="Show/hide this section")

    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Navigation Section"
        verbose_name_plural = "Navigation Sections"

    def __str__(self):
        return self.title


class NavigationItem(models.Model):
    """
    Individual menu items within a navigation section.
    Example: 'SEC', 'CE-SDS', 'Plasma Stability' under 'Analytical' section
    """
    section = models.ForeignKey(
        NavigationSection,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Parent section for this menu item"
    )
    name = models.CharField(max_length=100, help_text="Display name for the menu item")
    url = models.CharField(max_length=200, help_text="URL path for this menu item")
    icon = models.CharField(
        max_length=50,
        help_text="Font Awesome icon class (e.g., 'fa-chart-area')",
        blank=True
    )
    order = models.IntegerField(default=0, help_text="Display order within the section")
    is_active = models.BooleanField(default=True, help_text="Show/hide this menu item")
    description = models.TextField(blank=True, help_text="Optional description for the menu item")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Navigation Item"
        verbose_name_plural = "Navigation Items"

    def __str__(self):
        return f"{self.section.title} > {self.name}"
