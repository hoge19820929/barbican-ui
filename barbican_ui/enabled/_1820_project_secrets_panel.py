#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'secrets'
# The slug of the panel group the PANEL is associated with.
PANEL_GROUP = 'barbican'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'project'

# Python panel class of the PANEL to be added.
ADD_PANEL = 'barbican_ui.content.secrets.panel.Secrets'

ADD_ANGULAR_MODULES = [
    'horizon.dashboard.barbican.secrets'
]

ADD_JS_FILES = [
    'horizon/lib/angular/angular-route.js',
    'dashboard/barbican/barbican.module.js',
    'dashboard/barbican/barbican.service.js',
    'dashboard/barbican/secrets/secrets.module.js',
    'dashboard/barbican/secrets/secrets.service.js',
    'dashboard/barbican/secrets/actions/actions.module.js',
    'dashboard/barbican/secrets/actions/create.service.js',
    'dashboard/barbican/secrets/actions/delete.service.js',
    'dashboard/barbican/secrets/actions/update.service.js',
    'dashboard/barbican/secrets/details/details.module.js',
    'dashboard/barbican/secrets/details/overview.controller.js',
    'dashboard/barbican/secrets/workflow/secret-model.js',
    'dashboard/barbican/secrets/workflow/workflow.service.js'
]

ADD_SCSS_FILES = [
    'horizon/lib/bootstrap_scss/scss/_bootstrap.scss',
    'horizon/lib/font_awesome/scss/font-awesome.scss',
    'dashboard/barbican/barbican.scss',
    'dashboard/barbican/secrets/secrets.scss'
]

AUTO_DISCOVER_STATIC_FILES = True