from django.urls import path
from .views import ChequeDashboardView, update_cheque_status, bulk_update_cheque_status, download_report, download_leases_pdf

urlpatterns = [
    # The URL /accounting/ will go to the ChequeDashboardView
    path('', ChequeDashboardView.as_view(), name='cheque-dashboard'),
    # e.g., /accounting/cheque/5/update/ will go to the update status view for cheque #5
    path('cheque/<int:pk>/update/', update_cheque_status, name='update-cheque-status'),
    path('cheque/bulk-update/', bulk_update_cheque_status, name='bulk-update-cheque-status'),
    path('download-report/', download_report, name='download-report'),
    path('download-leases-pdf/', download_leases_pdf, name='download-leases-pdf'),
]