// Globals
var loggedIn = null;

function refresh_index(data) {
    var endpoints = data.endpoints;
    loggedIn = data.loggedIn;
    console.log(data.endpoints.client);
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