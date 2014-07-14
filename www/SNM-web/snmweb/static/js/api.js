/**
 * Created by nix on 7/1/14.
 */
initAPI = function(base) {
    var api = {
        base: base,
        stat: "stat"
    }

    $.ajaxSetup({
        async: false
    });

    function getStat(id, args, callback) {
        var url = [api.base, api.stat, id].join("/");
        $.getJSON(url, args, function(r) {
            if (r.status == "ERROR") {
                console.log(url + ": " + r.data);
                return;
            }
            callback(r);
        });
    }

    return {
        getStat: getStat,
        getBase: function() { return api.base; }
    }
}
