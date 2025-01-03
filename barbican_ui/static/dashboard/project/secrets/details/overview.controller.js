/*
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function() {
  "use strict";

  angular
    .module('horizon.dashboard.project.secrets')
    .controller('horizon.dashboard.project.secrets.OverviewController', controller);

  controller.$inject = [
    '$scope'
  ];

  function controller(
    $scope
  ) {
    var ctrl = this;
    ctrl.secret = {};

    $scope.context.loadPromise.then(onGetSecret);

    function onGetSecret(secret) {
      ctrl.secret = secret.data;
    }
  }
})();
