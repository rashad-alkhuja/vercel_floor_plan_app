# accounting/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Cheque
from django.utils import timezone
from dateutil.relativedelta import relativedelta

# This is a helper function to check permissions
def is_accountant_or_manager(user):
    return user.is_superuser or user.groups.filter(name__iregex=r'^(Accountant|Manager)$').exists()



# This view handles the form submission when an accountant changes a single cheque's status
@login_required
@user_passes_test(is_accountant_or_manager)
def update_cheque_status(request, pk):
    cheque = get_object_or_404(Cheque, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        # Check that the submitted status is a valid choice
        if new_status in [choice[0] for choice in Cheque.STATUS_CHOICES]:
            cheque.status = new_status
            cheque.last_updated_by = request.user
            cheque.save()
            
    return redirect('cheque-dashboard')

@login_required
@user_passes_test(is_accountant_or_manager)
def bulk_update_cheque_status(request):
    if request.method == 'POST':
        valid_statuses = [choice[0] for choice in Cheque.STATUS_CHOICES]
        for key, value in request.POST.items():
            if key.startswith('status_'):
                cheque_id = key.split('_')[1]
                try:
                    cheque = Cheque.objects.get(pk=cheque_id)
                    if value in valid_statuses and cheque.status != value:
                        cheque.status = value
                        cheque.last_updated_by = request.user
                        cheque.save()
                except Cheque.DoesNotExist:
                    pass
    return redirect('cheque-dashboard')

class ChequeDashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = '/login/'
    def test_func(self):
        return is_accountant_or_manager(self.request.user)
    def handle_no_permission(self):
        return redirect('dashboard')
    
    def get(self, request):
        from django.db.models import Sum, Count
        from django.db.models.functions import TruncMonth, ExtractYear
        from .models import Lease
        from offices.models import Office
        import json
        from django.core.serializers.json import DjangoJSONEncoder

        # --- YEAR FILTER PREPARATION ---
        # 1. Get all available years from the cheques
        # values_list returns a list of tuples, flat=True makes it a list of values
        available_years = Cheque.objects.annotate(
            year=ExtractYear('due_date')
        ).values_list('year', flat=True).distinct().order_by('-year')
        
        # 2. Determine selected year
        current_year = timezone.now().year
        selected_year_param = request.GET.get('year')
        
        try:
            selected_year = int(selected_year_param) if selected_year_param else current_year
        except ValueError:
            selected_year = current_year

        # If no cheques exist at all, we might have an empty list of years. 
        # Ensure at least the current year is available for UI.
        if not available_years:
            available_years = [current_year]

        # --- FILTERED QUERIES ---
        # Base Query: All cheques for the selected year
        cheques_for_year = Cheque.objects.filter(
            due_date__year=selected_year
        )

        # 1. Active/Detailed List for the Table
        # We show ALL cheques for that year so the accountant can see history (Cleared/Bounced) too.
        # Ordered by due_date.
        detailed_cheques = cheques_for_year.select_related(
            'lease__office', 
            'last_updated_by'
        ).order_by('due_date')

        # --- DASHBOARD METRICS (Scoped to Selected Year) ---

        # 1. Total Rented Value (This remains ALL active leases regardless of year, 
        # as it's a current state metric, not historical)
        total_rented_value = Lease.objects.filter(is_active=True).aggregate(
            total=Sum('annual_rent')
        )['total'] or 0

        # 2. Cash Flow for Selected Year (Sum of Pending & Due for that year)
        # Note: If looking at a past year, this might be 0 if everything is cleared.
        # This metric might change meaning slightly: "Amount Outstanding for [Year]" vs "Total Flow for [Year]"
        # Let's keep it as "Pending + Due" to see what's left to collect for that year.
        upcoming_cashflow = cheques_for_year.filter(
            status__in=['Pending', 'Due']
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        # 3. Occupancy Rate (Current state, not historical)
        total_offices = Office.objects.count()
        rented_offices = Office.objects.filter(status='rented').count()
        if total_offices > 0:
            occupancy_rate = (rented_offices / total_offices) * 100
        else:
            occupancy_rate = 0

        # --- CHARTS DATA PREPARATION ---

        # A. Status Distribution (Pie Chart) for Selected Year
        status_counts = cheques_for_year.values('status').annotate(count=Count('status'))
        status_data = {item['status']: item['count'] for item in status_counts}
        
        # B. Monthly Cash Flow (Bar Chart) for Selected Year
        monthly_cashflow = cheques_for_year.annotate(
            month=TruncMonth('due_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')

        # Format for Chart.js: labels (Month YYYY) and data (amounts)
        cashflow_labels = []
        cashflow_data = []
        
        # We want to show all months of the selected year potentially, or just months with data?
        # Usually easier to just show months with data or fill gaps. 
        # For simplicity, we stick to existing logic: iterating the query result.
        for entry in monthly_cashflow:
            if entry['month']:
                cashflow_labels.append(entry['month'].strftime('%b %Y'))
                cashflow_data.append(float(entry['total']))
        
        # Also add context for our PDF filter modal
        all_offices = Office.objects.all().order_by('office_number')
        
        context = {
            'active_cheques': detailed_cheques, # Renaming variable in template might be clearer, but keeping 'active_cheques' for min diff
            'total_rented_value': total_rented_value,
            'upcoming_cashflow': upcoming_cashflow,
            'occupancy_rate': round(occupancy_rate, 1),
            'rented_offices_count': rented_offices,
            'total_offices_count': total_offices,
            # For Filter UI
            'available_years': available_years,
            'selected_year': selected_year,
            # For PDF Filter Modal
            'all_offices': all_offices,
            'cheque_statuses': Cheque.STATUS_CHOICES,
            # Serialize for JS
            'status_data_json': json.dumps(status_data, cls=DjangoJSONEncoder),
            'cashflow_labels_json': json.dumps(cashflow_labels, cls=DjangoJSONEncoder),
            'cashflow_data_json': json.dumps(cashflow_data, cls=DjangoJSONEncoder),
        }
        return render(request, 'accounting/cheque_dashboard.html', context)

import csv
from django.http import HttpResponse

@login_required
@user_passes_test(is_accountant_or_manager)
def download_report(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="cheques_report.csv"'},
    )

    writer = csv.writer(response)
    # Write the header row
    writer.writerow(['Office', 'Lease ID', 'Due Date', 'Amount', 'Status', 'Cheque Number', 'Bank Name'])

    # Get the data (same query as the dashboard)
    cheques = Cheque.objects.exclude(status='Cleared').select_related('lease__office').order_by('due_date')

    for cheque in cheques:
        writer.writerow([
            str(cheque.lease.office),
            cheque.lease.id,
            cheque.due_date,
            cheque.amount,
            cheque.status,
            cheque.cheque_number,
            cheque.bank_name
        ])

    return response

from django.template.loader import render_to_string

@login_required
@user_passes_test(is_accountant_or_manager)
def download_leases_pdf(request):
    from .models import Lease, Cheque
    from django.db.models import Prefetch

    office_num = request.GET.get('office')
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    cheques_query = Cheque.objects.all().order_by('due_date')
    if status:
        cheques_query = cheques_query.filter(status=status)
    if start_date:
        cheques_query = cheques_query.filter(due_date__gte=start_date)
    if end_date:
        cheques_query = cheques_query.filter(due_date__lte=end_date)

    leases = Lease.objects.select_related('office').order_by('office__office_number')

    if office_num:
        leases = leases.filter(office__office_number=office_num)
        
    if status or start_date or end_date:
        leases = leases.filter(cheques__in=cheques_query).distinct()
        
    leases = leases.prefetch_related(
        Prefetch('cheques', queryset=cheques_query)
    )
    
    html_string = render_to_string('accounting/leases_pdf.html', {'leases': leases})
    
    from weasyprint import HTML
    pdf_file = HTML(string=html_string).write_pdf()
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="leases_report.pdf"'
    return response