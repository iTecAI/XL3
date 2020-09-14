var MAX_CHARACTERS = 15;

$(document).ready(function(){
    $('#class-warning').hide();
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

    $('#new-character-btn').on('click',function(){
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

    cget(
        '/characters/'+fingerprint+'/3c2bb133cd50f78da06fada8c7c20e42177fbc17739bd1a2eb404f39b07fc72b/',
        {},true,
        sheet_gen
    );
});