from django.urls import path
from .views import image_arrangement

app_name = 'development'

urlpatterns = [
    # Table Comparison Demo
    path('table-comparison/', image_arrangement.table_comparison, name='table_comparison'),

    # Image Arrangement App
    path('image-arrangement/', image_arrangement.index, name='image_arrangement'),
    path('image-arrangement/add-row/', image_arrangement.add_row, name='img_add_row'),
    path('image-arrangement/load-sample/', image_arrangement.load_sample, name='img_load_sample'),
    path('image-arrangement/load-multi-group/', image_arrangement.load_multi_group, name='img_load_multi'),
    path('image-arrangement/clear-all/', image_arrangement.clear_all, name='img_clear'),
    path('image-arrangement/save-table/', image_arrangement.save_table, name='img_save_table'),
    path('image-arrangement/generate/', image_arrangement.generate_layout, name='img_generate'),
    path('image-arrangement/export/', image_arrangement.export_ppt, name='img_export'),
    path('image-arrangement/preview/<str:project_id>/', image_arrangement.preview_image, name='img_preview'),
]
