async function getKeyPair() { // Generates or loads key pair
    if (localStorage['keypair'] == undefined || localStorage['keypair'] == 'undefined') {
        var keyPair = await crypto.subtle.generateKey(
            {
                name: "RSASSA-PKCS1-v1_5",
                modulusLength: 1024,
                publicExponent: new Uint8Array([1, 0, 1]),
                hash: "SHA-256"
            },
            true,
            ["encrypt", "decrypt"]
            );
            var public = await crypto.subtle.exportKey("jwk", keyPair.publicKey);
            var private = await crypto.subtle.exportKey("jwk", keyPair.privateKey);
            console.log('private:',await strPrivateKey(keyPair.privateKey));
            console.log('public:',await strPublicKey(keyPair.publicKey));
            var pair = {
                "public":keyPair.publicKey,
                "private":keyPair.privateKey
            };
            var exp = {
                "public":public,
                "private":private
            };
            localStorage['keypair'] = JSON.stringify(exp);
            return pair;
    } else {
        var pair = JSON.parse(localStorage['keypair']);
        pair.public = await crypto.subtle.importKey(
            "jwk",
            pair.public,
            {
                "name":"RSASSA-PKCS1-v1_5",
                "hash":"SHA-256"
            },
            true,
            ["encrypt"]
        );
        pair.private = await crypto.subtle.importKey(
            "jwk",
            pair.private,
            {
                "name":"RSASSA-PKCS1-v1_5",
                "hash":"SHA-256"
            },
            true,
            ["decrypt"]
        );
        return pair;
    }
}

async function encrypt(publicKey,data) { // Encrypts decrypted data
    let enc = new TextEncoder();
    var encoded = enc.encode(data);
    return await window.crypto.subtle.encrypt(
        {
            name: "RSASSA-PKCS1-v1_5"
        },
        publicKey,
        encoded
    );
}

async function decrypt(privateKey,data) { // Decrypts encrypted data
    let dec = new TextDecoder();
    return dec.decode(await window.crypto.subtle.decrypt(
        {
            name: "RSASSA-PKCS1-v1_5"
        },
        privateKey,
        data
    ));
}

function ab2str(buf) { // Array buffer to b64 string
    return String.fromCharCode.apply(null, new Uint8Array(buf));
}

async function strPublicKey(key) { // Turns public key into PEM format
    console.log(key);
    const exported = await window.crypto.subtle.exportKey(
        "spki",
        key
    );
    const exportedAsString = ab2str(exported);
    const exportedAsBase64 = window.btoa(exportedAsString);
    const pemExported = `-----BEGIN PUBLIC KEY-----\n${exportedAsBase64}\n-----END PUBLIC KEY-----`;
    console.log(pemExported);
    return pemExported;
}

async function strPrivateKey(key) { // Turns private key into PEM format
    console.log(key);
    const exported = await window.crypto.subtle.exportKey(
        "pkcs8",
        key
    );
    const exportedAsString = ab2str(exported);
    const exportedAsBase64 = window.btoa(exportedAsString);
    const pemExported = `-----BEGIN PRIVATE KEY-----\n${exportedAsBase64}\n-----END PRIVATE KEY-----`;
    console.log(pemExported);
    return pemExported;
}

function base64ToArrayBuffer(base64) { // Convert from urlsafe base64 to array buffer
    var binary_string = window.atob(base64.replace(/_/g, '/').replace(/-/g, '+'));
    var len = binary_string.length;
    var bytes = new Uint8Array(len);
    for (var i = 0; i < len; i++) {
        bytes[i] = binary_string.charCodeAt(i);
    }
    return bytes.buffer;
}

function getFormValues(submitSelector) {
    var inputs = $(submitSelector).attr('data-inputs').split(',');
    var data = {};
    for (var i=0;i<inputs.length;i++) {
        data[inputs[i]] = $('#'+inputs[i]).val();
    }
    return data;
}

function cpost(endpoint,data,callback,options) {
    if (!options) {
        options = {};
    }
    var alert = options.alert;
    var error = options.error;
    if (!error) {
        error = function(xhr){
            if (alert) {
                bootbox.alert({
                    'title':'Error '+xhr.status,
                    'message':xhr.responseJSON.result
                });
            }
        }
    }
    $.post({
        url: 'http://'+window.location.host+endpoint,
        data: JSON.stringify(data),
        success: callback,
        error: error
    });
}

function cget(endpoint,data,alert,callback) {
    var alert = alert;
    $.get({
        url: 'http://'+window.location.host+endpoint,
        data: JSON.stringify(data),
        success: callback,
        error: function(xhr){
            console.log(xhr);
            if (alert) {
                bootbox.alert({
                    'title':'Error '+xhr.status,
                    'message':xhr.responseJSON.result
                });
            }
        }
    });
}

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

function buildCharacter(item) {
    var data = item.data;
    if (data.image.length == 0) {
        var img = 'assets/logo_med.png';
    } else {
        var img = data.image;
    }
    var element = $('<div class="character-panel"></div>')
    .attr('id','character_panel_'+item.cid)
    .attr('data-id',item.cid)
    .append(
        $('<div class="char-caption"></div>')
        .append($('<h4></h4>').text(data.name)).css('font-family','raleway-heavy')
        .append(
            $('<span class="race-class-line"></span>')
            .text(data.race+' - '+data.class_display+' (Level '+data.level+')')
            .css({
                'font-style':'italic',
                'font-family':'raleway-regular'
            })
        )
    );
    element.append(
        $('<div class="char-img"></div>').append($('<img alt="Character Image" src="'+img+'">'))
    );
    element.append(
        $('<button class="character-menu-btn"><img src="assets/icons/menu.png"></button>')
        .on('click',function(event){
            activateitem($(event.target).parent().parent().children('.character-menu'));
        })
    );
    element.append(
        $('<div class="character-menu transient"></div>')
        .append(
            $('<button></button>')
            .addClass('character-menu-edit')
            .addClass('character-menu-item')
            .attr('data-action','edit')
            .text('Edit')
            .on('click',function(event){

            })
        ).append(
            $('<button></button>')
            .addClass('character-menu-duplicate')
            .addClass('character-menu-item')
            .attr('data-action','duplicate')
            .text('Duplicate')
            .on('click',function(event){
                cpost(
                    '/characters/'+fingerprint+'/'+$(event.target).parents('.character-panel').attr('data-id')+'/duplicate/',
                    {},function(data) {
                        console.log(data);
                    },{'alert':true}
                );
                $(document).trigger('click');
            })
        ).append(
            $('<button></button>')
            .addClass('character-menu-delete')
            .addClass('character-menu-item')
            .attr('data-action','delete')
            .text('Delete')
            .on('click',function(event){
                cpost(
                    '/characters/'+fingerprint+'/'+$(event.target).parents('.character-panel').attr('data-id')+'/delete/',
                    {},function(data) {
                        console.log(data);
                    },{'alert':true}
                );
                $(document).trigger('click');
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
            })
        )
    );

    return element;
}

$(document).ready(function(){
    $('.settings-input').on('change',function(event){
        if ($(event.target).attr('type') == 'checkbox') {
            var val = $(event.target).prop('checked').toString();
        } else {
            var val = $(event.target).val();
        }
        if (val == '') {
            return;
        }
        cpost(
            '/client/'+fingerprint+'/settings/set/'+$(event.target).attr('data-setting')+'/',
            {
                value: val
            },
            function(data){
                $(event.target).toggleClass('valid',true);
                window.setTimeout(function(){$(event.target).toggleClass('valid',false)},2000);
            },
            {
                error: function(xhr) {
                    $(event.target).toggleClass('invalid',true);
                    window.setTimeout(function(){$(event.target).toggleClass('invalid',false)},2000);
                    bootbox.alert({
                        'title':'Error '+xhr.status,
                        'message':xhr.responseJSON.result
                    });
                }
            }
        );
    });
});