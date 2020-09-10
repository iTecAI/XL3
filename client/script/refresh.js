// Globals
var loggedIn = null;

function refresh(data) {
    var endpoints = data.endpoints;
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
                console.log('update');
            }
        );
    }
}