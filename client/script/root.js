var theme = 'light';
var activating = false;

var keyPair = null;
var fingerprint = null;

$(document).ready(function(){
    $('#noconn').hide();
    $('#top-bar .top-nav').toggleClass('active',false);
    if (window.location.pathname == '/') {
        $('#compendium-nav').toggleClass('active',true);
    } else if (window.location.pathname == '/campaigns.html') {
        $('#campaigns-nav').toggleClass('active',true);
    } else if (window.location.pathname == '/characters.html') {
        $('#characters-nav').toggleClass('active',true);
    } else if (window.location.pathname == '/help.html') {
        $('#help-nav').toggleClass('active',true);
    }

    if (Cookies.get('fingerprint') == undefined) {
        Cookies.set('fingerprint',sha256((Math.random()*Date.now()+Math.random()).toString()));
    }
    fingerprint = Cookies.get('fingerprint');

    // Start status check process
    window.setInterval(function(){
        $.get({
            url: 'http://'+window.location.host+'/server/connection/status/'+fingerprint+'/',
            data: {},
            success: refresh,
            error: function(xhr){
                if (xhr.status == 0) {
                    $('#noconn').show();
                } else {
                    cpost(
                        '/server/connection/new/',
                        {
                            'fingerprint':fingerprint
                        },
                        function(data){
                            console.log('Created connection with fingerprint '+fingerprint);
                        }
                    );
                }
            }
        });
    },200);

    cpost(
        '/server/connection/new/',
        {
            'fingerprint':fingerprint
        },
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

    function activateDialog(selector) {
        activating = true;
        $('#modal').toggleClass('active',true);
        $(selector).toggleClass('active',true);
        setTimeout(function(){activating=false},200);
    }

    function activateitem(selector) {
        activating = true;
        $(selector).toggleClass('active',true);
        setTimeout(function(){activating=false},200);
    }

    $(document).on('click',function(event){
        if (!$(event.target).hasClass('transient') && !activating && $(event.target).parents('.transient').length == 0) {
            $('.transient').toggleClass('active',false);
        }
    });

    $('#modal').on('click',function(event){
        $('.transient').toggleClass('active',false);
    });

    $('#login').on('click',function(){
        if (loggedIn) {
            activateitem('#user-actions');
        } else {
            activateDialog('#login-window');
        }
    });
    $('#login').on('mouseenter',function(){
        if (loggedIn) {
            $('#login').attr('data-tooltip','Account');
        } else {
            $('#login').attr('data-tooltip','Login or Create Account');
        }
    });

    $('#create-acct-ref-btn').on('click',function(){
        $(document).on('click',);
        activateDialog('#sign-up-window');
    });
    $('#login-ref-btn').on('click',function(){
        $(document).on('click',);
        activateDialog('#login-window');
    });

    $('#login-submit').on('click',function(){
        $(document).on('click',);
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
            true,function(){$(document).on('click',);bootbox.alert('Logged in.')},
            {
                alert: true
            }
        );
    });
    $('#create-acct-submit').on('click',function(){
        $(document).on('click',);
        var data = getFormValues('#create-acct-submit');
        var username = data['sign-up-email'];
        var hashword = sha256(data['sign-up-password']);
        var displayName = data['sign-up-name'];
        cpost(
            '/server/login/new/',
            {
                'fingerprint':fingerprint,
                'username':username,
                'hashword':hashword,
                'name':displayName
            },
            function(){$(document).on('click',);bootbox.alert('Logged in.')},
            {
                alert: true
            }
        );
    });

    $('#logout-btn').on('click',function(){
        if (loggedIn) {
            $(document).on('click',);
            bootbox.confirm('Log out?',function(confirmed){
                if (confirmed) {
                    cpost(
                        '/server/login/exit/',
                        {
                            'fingerprint':fingerprint
                        },
                        undefined,
                        {
                            alert: true
                        }
                    );
                }
            });
        }
    });

    $('.tab').on('click',function(event){
        $('.tab').toggleClass('active',false);
        $(event.target).toggleClass('active',true);
        $('.page').toggleClass('active',false);
        $('#'+$(event.target).attr('data-tab')).toggleClass('active',true);

    });

    $('#user-settings-btn').on('click',function(){
        $('#user-settings-window input').val('');
        $(document).on('click',);

        cget(
            '/client/'+fingerprint+'/settings/',
            {},
            true,
            function(data) {
                var settings = Object.keys(data.settings);
                for (var s=0;s<settings.length;s++) {
                    $('#client-settings-'+settings[s]).attr('placeholder','Display Name: '+data.settings[settings[s]]);
                }
                console.log('update');
            }
        );

        activateDialog('#user-settings-window');
    });

    $('#client-password-current').on('change',function(event){
        if ($(event.target).val() != '') {
            cpost(
                '/client/'+fingerprint+'/password/check/',
                {
                    hashword: sha256($(event.target).val())
                },
                function(data) {
                    $('#client-password-current').toggleClass('valid',data.match);
                    $('#client-password-current').toggleClass('invalid',!data.match);
                    if (data.match) {
                        window.setTimeout(function(){$(event.target).toggleClass('valid',false)},2000);
                    } else {
                        window.setTimeout(function(){$(event.target).toggleClass('invalid',false)},2000);
                    }
                }
            );
        }
    });

    $('#change-psw-btn').on('click',function(){
        if ($('#client-password-current').val() != '' && $('#client-password-new').val() != '') {
            bootbox.confirm('Are you sure you want to change your password?',function(confirmed){
                cpost(
                    '/client/'+fingerprint+'/password/check/',
                    {
                        hashword: sha256($('#client-password-current').val())
                    },
                    function(data) {
                        $('#client-password-current').toggleClass('valid',data.match);
                        $('#client-password-current').toggleClass('invalid',!data.match);
                        if (data.match) {
                            window.setTimeout(function(){$('#client-password-current').toggleClass('valid',false)},2000);
                            cpost(
                                '/client/'+fingerprint+'/password/change/',
                                {
                                    hashword: sha256($('#client-password-current').val()),
                                    new_hashword: sha256($('#client-password-new').val())
                                },
                                function(data) {
                                    bootbox.alert('Password changed.');
                                },
                                {
                                    alert: true
                                }
                            );
                        } else {
                            window.setTimeout(function(){$('#client-password-current').toggleClass('invalid',false)},2000);
                        }
                    }
                );
            });
        } else {
            bootbox.alert('Please fill both inputs.');
        }
    });
});