# offices/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Ensure all four views are imported here
from .views import FloorPlanView, OfficeViewSet, create_proposal_view, generate_pdf_view, office_statistics_view, statistics_view, download_available_offices_pdf, download_rented_offices_pdf
router = DefaultRouter()
router.register(r'offices', OfficeViewSet, basename='office')

urlpatterns = [
    path('', FloorPlanView.as_view(), name='floor-plan'),
    path('api/', include(router.urls)),
    
    # These URLs should be correct
     path('statistics/', statistics_view, name='office-stats-page'),
    path('proposal/create/<int:office_number>/', create_proposal_view, name='create-proposal'),
    path('proposal/generate-pdf/<int:office_number>/', generate_pdf_view, name='generate-pdf'),
    path('api/statistics/', office_statistics_view, name='office-statistics'),
    path('reports/available-list/', download_available_offices_pdf, name='download-available-offices'),
    path('reports/rented-list/', download_rented_offices_pdf, name='download-rented-offices'),
]