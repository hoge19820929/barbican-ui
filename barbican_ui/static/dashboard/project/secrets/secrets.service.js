(function () {
  'use strict';

  angular
    .module('horizon.dashboard.project.secrets')
    .factory('barbicanService', barbicanService);

  barbicanService.$inject = ['$http'];

  function barbicanService($http) {
    var service = {
      createKey: createKey,
      listSecrets: listSecrets
    };

    function createKey(data) {
      return $http.post('/dashboard/barbican_ui/create-key/', data);
    }

    function listSecrets() {
      return $http.get('/dashboard/barbican_ui/list-secrets/');
    }

    return service;
  }
})();
