/**
 * Created by nix on 7/1/14.
 */
initAPI = function(base) {
    var api = {
        url: base,
        stat: "stat"
    }

    function getStat(id, args, callback) {
        var url = [api.base, api.stat, id].join("/");
        $.getJSON(url, args, callback)
    }

    return {
        getStat: getStat,
        getBase: function() {return api.base;}
    }
}