from django.contrib import messages
from django.http.request import HttpRequest
from django.http.response import HttpResponse, FileResponse
from django.contrib.auth.decorators import login_required
from gelv.models import User, Issue
from gelv.utils import smart_redirect


@login_required
def download_view(request: HttpRequest, id) -> FileResponse | HttpResponse:
    if request.user.is_authenticated:
        user = User.get_by_email(request.user.email)
        owned_issue_ids = user.get_owned_issues().values_list('id', flat=True)

    if id in owned_issue_ids:
        try:
            return FileResponse(Issue.objects.get(pk=id).file)
        except ValueError:
            messages.error(request, 'We could not find the file. Please contact us.')
    else:
        messages.error(request, 'You do not have the right to download this.')

    return smart_redirect(request, 'owned')
