/**
 * This class that provides methods to interact with API 
 *
 * base - is the url of api, e.g. /api
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

    function getStat(id, args, callback, failcallback) {
        var url = [api.base, api.stat, id].join("/");
        $.getJSON(url, args, function(r) {
            if (r.status == "ERROR") {
                console.log(url + ": " + r.data);
                if (typeof failcallback !== 'undefined') {failcallback();}
                return;
            }
            callback(r);
        }).fail(function() { console.log("Internal failure"); if (typeof failcallback !== 'undefined') {failcallback();}} );
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
