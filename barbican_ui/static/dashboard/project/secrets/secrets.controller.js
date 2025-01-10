(function() {
    'use strict';
  
    angular
      .module('horizon.dashboard.project')
      .controller('SecretsController', SecretsController);
  
    SecretsController.$inject = ['barbicanService'];
  
    function SecretsController(barbicanService) {
      var ctrl = this;
  
      ctrl.secrets = [];
      ctrl.createKeyMessage = '';
      ctrl.keyName = ''; // ユーザ入力用
      ctrl.keyDescription = ''; // ユーザ入力用
  
      ctrl.loadSecrets = function() {
        barbicanService.listSecrets().then(function(data) {
          ctrl.secrets = data;
        });
      };
  
      ctrl.createAESKey = function() {
        barbicanService.createAESKey(
          ctrl.keyName,
          ctrl.keyDescription
        ).then(function(message) {
          ctrl.createKeyMessage = message;
          ctrl.keyName = ''; // 入力クリア
          ctrl.keyDescription = ''; // 入力クリア
          ctrl.loadSecrets(); // 鍵リストを更新
        });
      };
  
      // コントローラー初期化時に鍵一覧をロード
      ctrl.loadSecrets();
    }
  })();
  