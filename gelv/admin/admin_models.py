from django.contrib import admin
from django.urls import path
from django.db.models import Max
from django.http import HttpResponse
from gelv.models import User, Journal, Issue, Subscription, IssueOrder, SubscriptionOrder, Payment
from gelv.admin.admin_site import admin_site


class IssueAdmin(admin.ModelAdmin):
    category = 'store'
    fields = ('journal', 'number', 'price', 'description')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('get-next-issue-number/', self.get_next_issue_number),
        ]
        return custom_urls + urls

    def get_next_issue_number(self, request):
        journal_id = request.GET.get('journal_id')
        if journal_id:
            try:
                journal = Journal.objects.get(id=journal_id)
                last_issue = Issue.objects.filter(journal=journal).aggregate(
                    max_number=Max('number')
                )
                return HttpResponse(str((last_issue['max_number'] or 0) + 1))
            except Journal.DoesNotExist:
                pass
        return HttpResponse(str(1))

    class Media:
        js = ('gelv/admin/js/issue_admin.js',)


admin_site.register(Issue, IssueAdmin)
admin_site.register(User)
admin_site.register(Journal)
