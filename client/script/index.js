var keyPair = null;
var fingerprint = null;

var theme = 'light';
var activating = false;

$(document).ready(async function(){
    if (Cookies.get('fingerprint') == undefined) {
        Cookies.set('fingerprint',sha256((Math.random()*Date.now()+Math.random()).toString()));
    }
    fingerprint = Cookies.get('fingerprint');

    cpost(
        '/server/connection/new/',
        {
            'fingerprint':fingerprint
        },
        false,
        function(data){
            console.log('Created connection with fingerprint '+fingerprint);
            cget(
                '/server/connection/status/'+fingerprint+'/',
                {},
                false
            );
        }
    );
    $('[theme]').hide();
    $('[theme='+theme+']').show();

    // Start status check process
    window.setInterval(function(){
        $.get({
            url: 'http://'+window.location.host+'/server/connection/status/'+fingerprint+'/',
            data: {},
            success: refresh_index,
            error: function(xhr){
                cpost(
                    '/server/connection/new/',
                    {
                        'fingerprint':fingerprint
                    },
                    false,
                    function(data){
                        console.log('Created connection with fingerprint '+fingerprint);
                    }
                );
            }
        });
    },200);

    function activateDialog(selector) {
        activating = true;
        $('#modal').toggleClass('active',true);
        $(selector).toggleClass('active',true);
        setTimeout(function(){activating=false},200);
    }

    $(document).click(function(event){
        if (!$(event.target).hasClass('transient') && !activating && $(event.target).parents('.transient').length == 0) {
            $('.transient').toggleClass('active',false);
        }
    });

    $('#modal').click(function(event){
        $('.transient').toggleClass('active',false);
    });

    $('#login').click(function(){
        activateDialog('#login-window');
    });

    $('#create-acct-ref-btn').click(function(){
        $(document).click();
        activateDialog('#sign-up-window');
    });
    $('#login-ref-btn').click(function(){
        $(document).click();
        activateDialog('#login-window');
    });

    $('#login-submit').click(function(){
        var data = getFormValues('#login-submit');
        var username = data['login-email'];
        var hashword = sha256(data['login-password']);
        cpost(
            '/server/login/',
            {
                'fingerprint':fingerprint,
                'username':username,
                'hashword':hashword
            },
            true,function(){$(document).click();bootbox.alert('Logged in.')}
        );
    });
    $('#create-acct-submit').click(function(){
        var data = getFormValues('#create-acct-submit');
        var username = data['sign-up-email'];
        var hashword = sha256(data['sign-up-password']);
        cpost(
            '/server/login/new/',
            {
                'fingerprint':fingerprint,
                'username':username,
                'hashword':hashword
            },
            true,function(){$(document).click();bootbox.alert('Logged in.')}
        );
    });

});