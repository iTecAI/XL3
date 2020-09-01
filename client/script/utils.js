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