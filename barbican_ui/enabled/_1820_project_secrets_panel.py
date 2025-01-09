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
    'horizon.dashboard.project.secrets'
]

ADD_JS_FILES = [
    'horizon/lib/angular/angular-route.js',
    'dashboard/project/barbican.module.js',
    'dashboard/project/barbican.service.js',
    'dashboard/project/secrets/secrets.controller.js',
    'dashboard/project/secrets/secrets.module.js',
    'dashboard/project/secrets/secrets.service.js'
#    'dashboard/project/secrets/actions/actions.module.js',
#    'dashboard/project/secrets/actions/create.service.js',
#    'dashboard/project/secrets/actions/delete.service.js',
#    'dashboard/project/secrets/actions/update.service.js',
#    'dashboard/project/secrets/details/details.module.js',
#    'dashboard/project/secrets/details/overview.controller.js',
#    'dashboard/project/secrets/workflow/secret-model.js',
#    'dashboard/project/secrets/workflow/workflow.service.js'
]

ADD_SCSS_FILES = [
    'horizon/lib/bootstrap_scss/scss/_bootstrap.scss',
    'horizon/lib/font_awesome/scss/font-awesome.scss',
    'dashboard/project/barbican.scss',
    'dashboard/project/secrets/secrets.scss'
]

AUTO_DISCOVER_STATIC_FILES = True