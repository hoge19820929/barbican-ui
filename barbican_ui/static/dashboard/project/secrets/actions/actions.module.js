/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @ngname horizon.dashboard.project.secrets.actions
   *
   * @description
   * Provides all of the actions for Secrets.
   */
  angular
    .module('horizon.dashboard.project.secrets.actions', [
      'horizon.framework',
      'horizon.dashboard.barbican'
    ])
    .run(registerSecretActions);

  registerSecretActions.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.dashboard.project.secrets.create.service',
    'horizon.dashboard.project.secrets.update.service',
    'horizon.dashboard.project.secrets.delete.service',
    'horizon.dashboard.project.secrets.resourceType'
  ];

  function registerSecretActions (
    registry,
    gettext,
    createSecretService,
    updateSecretService,
    deleteSecretService,
    resourceType
  ) {
    var secretsResourceType = registry.getResourceType(resourceType);
    secretsResourceType.globalActions
      .append({
        id: 'createSecretAction',
        service: createSecretService,
        template: {
          type: 'create',
          text: gettext('Create Secret')
        }
      });

    secretsResourceType.batchActions
      .append({
        id: 'batchDeleteSecretAction',
        service: deleteSecretService,
        template: {
          type: 'delete-selected',
          text: gettext('Delete Secrets')
        }
      });

    secretsResourceType.itemActions
      .append({
        id: 'updateSecretAction',
        service: updateSecretService,
        template: {
          text: gettext('Update Secret')
        }
      })
      .append({
        id: 'deleteSecretAction',
        service: deleteSecretService,
        template: {
          type: 'delete',
          text: gettext('Delete Secret')
        }
      });
  }
})();
