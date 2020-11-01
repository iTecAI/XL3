// Globals
var loggedIn = null;

async function refresh(data) {
    var endpoints = data.endpoints;
    $('#noconn').hide();
    loggedIn = data.loggedIn;
    if (loggedIn) {
        $('#characters-nav').show(250);
        $('#campaigns-nav').show(250);
    } else {
        $('#characters-nav').hide(250);
        $('#campaigns-nav').hide(250);
    }
    
    if (endpoints.client) {
        cget(
            '/client/'+fingerprint+'/settings/',
            {},
            true,
            function(data) {
                var settings = Object.keys(data.settings);
                for (var s=0;s<settings.length;s++) {
                    $('#client-settings-'+settings[s]).attr('placeholder','Current: '+data.settings[settings[s]]);
                }
            }
        );
    }
    if (endpoints.characters && window.location.pathname.contains('characters')) {
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
    }
    if (endpoints.campaigns && window.location.pathname.contains('campaigns')) {
        var current_campaigns = await $.get({
            url: 'http://' + window.location.host + '/campaigns/'+fingerprint+'/'
        });
        var oc = current_campaigns.owned_campaigns;
        var pc = current_campaigns.participating_campaigns;
        $('#ocb-box').html('');
        for (var c=0;c<oc.length;c++) {

        }
    }
}