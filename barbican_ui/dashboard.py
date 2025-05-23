from django.utils.translation import gettext_lazy as _
import horizon

class BarbicanDashboard(horizon.Dashboard):
    name = _("KMS")
    slug = "kms"
    panels = (
        'secrets',
        'aws',
        'oracle',
        'azure',
        'google',
    )
    default_panel = 'secrets'

horizon.register(BarbicanDashboard)