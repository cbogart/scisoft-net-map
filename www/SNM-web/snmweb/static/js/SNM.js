/**
 * Main javascript
 * Created by nix on 7/19/14.
 */
/*
TODO: SNM.api, SNM.compare, etc. Keep global space clean
 */

var SNM = function() {

    function getParameterByName(name) {
        name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
        var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
            results = regex.exec(location.search);
        return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
    }

    return {
        getParameterByName: getParameterByName
    }
}();
