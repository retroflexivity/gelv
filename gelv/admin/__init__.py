from .admin_site import CustomAdminSite
from . import admin_models as am
from gelv.models import User, Journal, Issue, Subscription, IssueOrder, SubscriptionOrder, Payment, Post, Ad

apps = {
    "store": (Journal, Issue, Subscription),
    "users": (User,),
    "orders": (Payment, SubscriptionOrder, IssueOrder),
    "content": (Post, Ad),
}

admin_site = CustomAdminSite(name="customadmin", apps=apps)

admin_site.register(Journal, am.JournalAdmin)
admin_site.register(Issue, am.IssueAdmin)
admin_site.register(Subscription, am.SubscriptionAdmin)
admin_site.register(User)
admin_site.register(Payment)
admin_site.register(SubscriptionOrder, am.SubscriptionOrderAdmin)
admin_site.register(IssueOrder)
admin_site.register(Post, am.PostAdmin)
admin_site.register(Ad, am.AdAdmin)
