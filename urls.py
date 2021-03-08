from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    #path('results/', views.results, name='results'),
    path('request_directory/', views.request_directory, name='request_directory'),
    path('start_tcr_pipeline/', views.start_tcr_pipeline, name='start_tcr_pipeline'),
    path('get_status/', views.get_status, name='get_status'),
    path('terminate/', views.terminate, name='terminate'),
    path('download_file/', views.download_file, name='download_file')
]
