var MAX_CHARACTERS = null;

$(document).ready(async function(){
    var parameters = getParams();
    console.log(parameters);
    MAX_CHARACTERS = Number(await getConfig('CHARACTERS','max_characters'));
    $(document).tooltip({show: {effect:"fade", delay:500}});
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

    if (Object.keys(parameters).includes('char')) {
        cget(
            '/characters/'+fingerprint+'/'+parameters.char+'/',
            {},true,
            function(data){
                sheet_gen(data);
                activateitem('#character-sheet-display');
            }
        );
    }
    $('#short-rest-panel').slideUp(0);
});