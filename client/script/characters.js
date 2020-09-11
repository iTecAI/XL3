var MAX_CHARACTERS = 15;

$(document).ready(function(){
    $('#info-max-characters').text(MAX_CHARACTERS);
    cget(
        '/client/'+fingerprint+'/characters/',
        {},false,
        function(data){
            $('#info-cur-characters').text(data.owned.length);
            if (data.owned.length > 0) {
                cget(
                    '/characters/'+fingerprint+'/',
                    {},false,
                    function(data){
                        $('#character-list').html('');
                        console.log(data);
                        var chars = data.characters;
                        for (var c=0;c<chars.length;c++) {
                            var el = buildCharacter(chars[c]);
                            $('#character-list').append(el);
                        }
                    }
                );
            }
        }
    );

    $('#new-character-btn').click(function(){
        bootbox.prompt('Enter URL of sheet.',function(result){
            if (result) {
                cpost(
                    '/characters/'+fingerprint+'/new/',
                    {
                        url:result
                    },
                    function(data){
                        bootbox.alert('Loaded sheet.');
                        cget(
                            '/characters/'+fingerprint+'/'+data.cid+'/',
                            {},
                            true,
                            function(data) {
                                console.log(data);
                            }
                        );
                    }
                );
            }
        });
    });
});