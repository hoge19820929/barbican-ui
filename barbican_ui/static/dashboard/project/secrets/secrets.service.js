(function() {
  'use strict';

  angular
    .module('horizon.dashboard.project')
    .factory('barbicanService', barbicanService);

  barbicanService.$inject = ['$http'];

  function barbicanService($http) {
    return {
      listSecrets: function() {
        return $http.get('/secrets/').then(function(response) {
          return response.data.secrets;
        });
      },
      createAESKey: function(keyName, keyDescription) {
        return $http.post('/secrets/create_aes_key/', {
          name: keyName,
          description: keyDescription
        }).then(function(response) {
          return response.data.message;
        });
      }
    };
  }
})();
