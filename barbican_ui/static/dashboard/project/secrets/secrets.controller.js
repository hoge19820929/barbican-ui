(function () {
  'use strict';

  angular
    .module('horizon.dashboard.project.secrets')
    .controller('BarbicanController', BarbicanController);

  BarbicanController.$inject = ['barbicanService'];

  function BarbicanController(barbicanService) {
    var ctrl = this;

    ctrl.keyData = {
      key_name: '',
      key_description: ''
    };

    ctrl.secrets = [];

    ctrl.createKey = function () {
      barbicanService.createKey(ctrl.keyData)
        .then(function () {
          alert('鍵を作成しました');
        })
        .catch(function (error) {
          console.error('鍵作成エラー', error);
        });
    };

    ctrl.listSecrets = function () {
      barbicanService.listSecrets()
        .then(function (response) {
          ctrl.secrets = response.data;
        })
        .catch(function (error) {
          console.error('鍵一覧取得エラー', error);
        });
    };

    ctrl.listSecrets(); // 初期ロード時に鍵一覧を取得
  }
})();
