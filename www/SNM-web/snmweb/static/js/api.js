/**
 * Created by nix on 7/1/14.
 */
initAPI = function(base) {
    var api = {
        base: base,
        stat: "stat",
        apps: "apps"
    }

    $.ajaxSetup({
        async: false
    });

    function getStat(id, args, callback) {
        console.log("1")
        var url = [api.base, api.stat, id].join("/");
        console.log(url)
        $.getJSON(url, args, function(r) {
            if (r.status == "ERROR") {
                console.log(url + ": " + r.data);
                return;
            }
            callback(r);
        });
    }

    function getApps(id, callback) {
      var url = "";
      if (id == null)
        url = [api.base, api.apps].join("/");
      else
        url = [api.base, api.apps].join("/") + "?ids=" + id;

      console.log(url);

      $.getJSON(url, function(r) {
          if (r.status == "ERROR") {
              console.log(url + ": " + r.data);
              return;
          }
          callback(r);
      });
    }

    return {
        getStat: getStat,
        getApps: getApps,
        getBase: function() { return api.base; }
    }
}
