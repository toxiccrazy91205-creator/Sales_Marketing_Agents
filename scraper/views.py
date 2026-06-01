from django.shortcuts import render, redirect
from django.views.generic import ListView, View
from django.contrib import messages
from .models import ScrapedLead
from ai_engine.graph import run_lead_gen

class LeadDashboardView(ListView):
    model = ScrapedLead
    template_name = 'scraper/lead_dashboard.html'
    context_object_name = 'leads'
    ordering = ['-created_at']

class LeadIngestionView(View):
    def get(self, request):
        return render(request, 'scraper/lead_form.html')

    def post(self, request):
        industry = request.POST.get('industry')
        location = request.POST.get('location')
        company_size = request.POST.get('company_size')
        target_audience = request.POST.get('target_audience')

        if not all([industry, location, company_size, target_audience]):
            messages.error(request, "All fields are required.")
            return redirect('ingest')

        try:
            # Trigger LangGraph synchronously
            result = run_lead_gen(industry, location, company_size, target_audience)
            leads_found = len(result.get('final_qualified_leads', []))
            messages.success(request, f"Successfully processed {leads_found} new leads.")
        except Exception as e:
            messages.error(request, f"An error occurred during processing: {str(e)}")

        return redirect('dashboard')
