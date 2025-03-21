import collections
from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from . import api

class AutoRotateSecretForm(forms.SelfHandlingForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = collections.OrderedDict([
            (
                'key_id',
                forms.CharField(
                    max_length=255,
                    label=_('Key ID'),
                    initial=self.request.GET.get('key_id', '')
                )
            ),
            (
                'pattern',
                forms.CharField(
                    max_length=255,
                    label=_('Cron Pattern'),
                    initial='* * * * *'
                )
            )
        ])

    def handle(self, request, data):
        try:
            api.auto_rotate_key(data['key_id'], data['pattern'])
            messages.success(request, _("Successfully set auto rotation: %s") % data['key_id'])
            return True
        except Exception:
            exceptions.handle(request)
            return False