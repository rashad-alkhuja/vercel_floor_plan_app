# offices/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View
from django.conf import settings
from pathlib import Path
import datetime 

from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response



from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test

# --- THIS IS THE ONLY MODEL IMPORT IN THIS FILE. IT IS CORRECT. ---
from .models import Office
# -----------------------------------------------------------------

from .serializers import OfficeSerializer
from .forms import ProposalForm

# --- HELPER FUNCTIONS ---
def is_manager(user):
    return user.is_superuser or user.groups.filter(name__iexact='Manager').exists()

def is_receptionist_or_manager(user):
    return user.is_superuser or user.groups.filter(name__iregex=r'^(Manager|Reception)$').exists()

# --- VIEWS FOR THE OFFICES APP ---

class FloorPlanView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = '/login/'
    def test_func(self):
        return is_receptionist_or_manager(self.request.user)
    def handle_no_permission(self):
        return redirect('dashboard')
    def get(self, request, *args, **kwargs):
        return render(request, 'offices/index.html')

@login_required(login_url='/login/')
@user_passes_test(is_manager, login_url='/dashboard/')
def statistics_view(request):
    return render(request, 'offices/statistics.html')

@login_required(login_url='/login/')
@user_passes_test(is_manager, login_url='/dashboard/')
def create_proposal_view(request, office_number):
    office = get_object_or_404(Office, pk=office_number)
    form = ProposalForm(initial={'annual_rent': office.annual_rent})
    context = {'form': form, 'office': office}
    return render(request, 'offices/create_proposal.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_manager, login_url='/dashboard/')
def generate_pdf_view(request, office_number):
    office = get_object_or_404(Office, pk=office_number)
    if request.method == 'POST':
        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal_data = form.cleaned_data
            logo_path_obj = Path(settings.STATICFILES_DIRS[0]) / 'offices/images/Rahet-Logo.png'
            logo_uri = logo_path_obj.as_uri()
            context = {
                'office': office,
                'proposal': proposal_data,
                'proposal_date': proposal_data.get('proposal_date').strftime("%d/%m/%Y"),
                'logo_path': logo_uri,
            }
            html_string = render_to_string('offices/proposal_pdf_template.html', context)
            from weasyprint import HTML
            pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Lease-Proposal-Office-{office.office_number}.pdf"'
            return response
    return create_proposal_view(request, office_number)

# --- API VIEWS FOR THE OFFICES APP ---

class OfficeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Office.objects.all().order_by('office_number')
    serializer_class = OfficeSerializer

@api_view(['GET'])
def office_statistics_view(request):
    available_count = Office.objects.filter(status='available').count()
    rented_count = Office.objects.filter(status='rented').count()
    data = {'available_count': available_count, 'rented_count': rented_count}
    return Response(data)

@login_required(login_url='/login/')
@user_passes_test(is_manager, login_url='/dashboard/')
def download_available_offices_pdf(request):
    # 1. Fetch only available offices
    available_offices = Office.objects.filter(status='available').order_by('office_number')
    
    # 2. Prepare the logo path (Windows-safe)
    logo_path_obj = Path(settings.STATICFILES_DIRS[0]) / 'offices/images/Rahet-Logo.png'
    logo_uri = logo_path_obj.as_uri()
    
    # 3. Prepare context
    context = {
        'offices': available_offices,
        'logo_path': logo_uri,
        'generation_date': datetime.date.today().strftime("%d/%m/%Y"),
    }

    # 4. Render HTML
    html_string = render_to_string('offices/available_offices_pdf.html', context)
    
    # 5. Generate PDF
    from weasyprint import HTML
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    # 6. Return response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Available-Offices-List.pdf"'
    return response

@login_required(login_url='/login/')
@user_passes_test(is_manager, login_url='/dashboard/')
def download_rented_offices_pdf(request):
    # 1. Fetch rented offices
    rented_offices = Office.objects.filter(status='rented').order_by('office_number')
    
    # 2. Prepare the logo path (Windows-safe)
    logo_path_obj = Path(settings.STATICFILES_DIRS[0]) / 'offices/images/Rahet-Logo.png'
    logo_uri = logo_path_obj.as_uri()
    
    # 3. Prepare context
    context = {
        'offices': rented_offices,
        'logo_path': logo_uri,
        'generation_date': datetime.date.today().strftime("%d/%m/%Y"),
    }

    # 4. Render HTML
    html_string = render_to_string('offices/rented_offices_pdf.html', context)
    
    # 5. Generate PDF
    from weasyprint import HTML
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    # 6. Return response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Rented-Offices-List.pdf"'
    return response