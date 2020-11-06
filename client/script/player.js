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

    $('#st-name').val(map.name);
    $('#st-grid-rows').val(map.grid.rows);
    $('#st-grid-columns').val(map.grid.columns);
    $('#st-grid-size').val(map.grid.size);

    $('#map-img img').attr('src','/images/'+map.image_id);
}

$(document).ready(function(){
    var p = getParams();
    if (!Object.keys(p).includes('cmp') || !Object.keys(p).includes('map')) {
        window.location = window.location.origin + '/campaigns';
    }
    CAMPAIGN = p.cmp;
    MAP = p.map;

    $('#chat-expander').on('click',function(){
        $('#chat-panel').toggleClass('active');
    });

    $('#map-settings-btn').on('click',function(){
        $('#map-settings').toggleClass('active');
    });

    $('input.modifier').on('change',function(event){
        var val = $(this).val();
        if ($(this).attr('type') == 'number') {
            val = Number(val);
            if (!isNaN(val) && val > 0) {
                mPost('/modify/',{path:$(this).attr('data-path'),value:val},function(data){},{alert:true});
                return;
            }
            $(this).val('1');
        } else {
            mPost('/modify/',{path:$(this).attr('data-path'),value:val},function(data){},{alert:true});
            return;
        }
    });
});