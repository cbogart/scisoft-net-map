/**
 * Created by nix on 7/19/14.
 */
var compare = function(){

    /* private functions */
    function getObj(key) {
        return JSON.parse(localStorage.getItem(key) || {});
    }

    function saveObj(key, obj) {
        localStorage.setItem(
            key, JSON.stringify(obj));
    }

    function count(dict){
        var count = 0;
        for (var p in dict) {
            if (dict.hasOwnProperty(p)) count++;
        }
        return count;
    }
    /* setting up */
    var COMPARE_KEY = "COMPARE_KEY";
    var counter = document.getElementById("compare-count");
    $(function(){
        //when document is ready
        counter.innerHTML = count(getObj(COMPARE_KEY));
    });

    /* public methods */
    function addApp(id){
        var dict = getObj(COMPARE_KEY);
        dict[id] = true;
        saveObj(COMPARE_KEY, dict);
        counter.innerHTML = count(dict);
    }

    function removeApp(id){
        var dict = getObj(COMPARE_KEY);
        delete dict[id];
        saveObj(COMPARE_KEY, dict);
        counter.innerHTML = count(dict);
    }

    function getCommaList(){
        var keys = [];
        var dict = getObj(COMPARE_KEY);
        for(var k in dict) keys.push(k);
        return keys.join(",");
    }

    function checkApp(id) {
        var dict = getObj(COMPARE_KEY);
        return (id in dict);
    }

   /* public methods */
   return {
       add      : addApp,
       remove   : removeApp,
       get      : getCommaList,
       check    : checkApp
   }

}();