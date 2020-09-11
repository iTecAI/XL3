var MAX_CHARACTERS = 15;

$(document).ready(function(){
    $('#info-max-characters').text(MAX_CHARACTERS);
    cget(
        '/client/'+fingerprint+'/characters/',
        {},false,
        function(data){
            $('#info-cur-characters').text(data.owned.length);
        }
    )
});