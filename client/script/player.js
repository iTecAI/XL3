var CAMPAIGN = null;
var MAP = null;

function mPost(endpoint,data,success,options) {
    cpost(
        '/campaigns/'+fingerprint+'/player/'+CAMPAIGN+'/'+MAP+endpoint,
        data,success,options
    );
}
function mGet(endpoint,data,success,alert) {
    cget(
        '/campaigns/'+fingerprint+'/player/'+CAMPAIGN+'/'+MAP+endpoint,
        data,alert,success
    );
}

function onPlayerRefresh(map) {
    console.log(map);
    $('#map-name').text(map.name);
    $('#map-dims').text(map.grid.columns+' x '+map.grid.rows+' ('+(map.grid.columns*map.grid.size)+' ft. x '+(map.grid.rows*map.grid.size)+' ft.)');
    $('#map-scale').text(map.grid.size+' ft.');
}

$(document).ready(function(){
    var p = getParams();
    if (!Object.keys(p).includes('cmp') || !Object.keys(p).includes('map')) {
        window.location = window.location.origin + '/campaigns';
    }
    CAMPAIGN = p.cmp;
    MAP = p.map;
});