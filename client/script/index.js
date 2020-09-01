var keyPair = null;

$(document).ready(async function(){
    $.post(
        'http://'+window.location.host+'/server/connection/new/',
        {
            'fingerprint':'test'
        },
        function(data){
            console.log(data);
        }
    );
});