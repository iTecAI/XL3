var keyPair = null;
var fingerprint = null;

var theme = 'light';

$(document).ready(async function(){
    if (Cookies.get('fingerprint') == undefined) {
        Cookies.set('fingerprint',(Math.random()*Date.now()+Math.random()).toString());
    }
    fingerprint = Cookies.get('fingerprint');

    $.post(
        'http://'+window.location.host+'/server/connection/new/',
        {
            'fingerprint':fingerprint
        },
        function(data){
            console.log(data);
        }
    );
    $('[theme]').hide();
    $('[theme='+theme+']').show();

});