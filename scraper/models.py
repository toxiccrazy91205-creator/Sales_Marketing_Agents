from django.db import models

class ScrapedLead(models.Model):
    SCORE_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    
    STATUS_CHOICES = [
        ('New', 'New'),
        ('Contacted', 'Contacted'),
        ('Rejected', 'Rejected'),
    ]

    company_name = models.CharField(max_length=255)
    website_url = models.URLField(max_length=500, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=255)
    description_summary = models.TextField()
    qualification_score = models.CharField(max_length=10, choices=SCORE_CHOICES)
    pipeline_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    reasoning = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name
