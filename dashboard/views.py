from django.shortcuts import render
from .models import NavigationSection


def index(request):
    """
    Dashboard homepage view
    """
    # Get all active navigation sections with their items
    navigation_sections = NavigationSection.objects.filter(is_active=True).prefetch_related('items')
    
    context = {
        'navigation_sections': navigation_sections,
    }
    
    return render(request, 'dashboard/index.html', context)
