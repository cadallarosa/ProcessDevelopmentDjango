from django.contrib import admin
from .models import NavigationSection, NavigationItem


class NavigationItemInline(admin.TabularInline):
    """Inline admin for navigation items within a section"""
    model = NavigationItem
    extra = 1
    fields = ('name', 'url', 'icon', 'order', 'is_active')
    ordering = ['order', 'name']


@admin.register(NavigationSection)
class NavigationSectionAdmin(admin.ModelAdmin):
    """Admin interface for navigation sections"""
    list_display = ('title', 'icon', 'order', 'is_collapsible', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'is_collapsible')
    search_fields = ('title',)
    ordering = ['order', 'title']
    inlines = [NavigationItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'icon', 'order')
        }),
        ('Configuration', {
            'fields': ('is_collapsible', 'url', 'is_active')
        }),
    )


@admin.register(NavigationItem)
class NavigationItemAdmin(admin.ModelAdmin):
    """Admin interface for individual navigation items"""
    list_display = ('name', 'section', 'url', 'icon', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('section', 'is_active')
    search_fields = ('name', 'url', 'description')
    ordering = ['section__order', 'order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('section', 'name', 'url', 'icon', 'order')
        }),
        ('Additional Options', {
            'fields': ('description', 'is_active')
        }),
    )
