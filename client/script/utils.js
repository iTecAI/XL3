async function getKeyPair() {
    if (localStorage['keypair'] == undefined) {
        var keyPair = await crypto.subtle.generateKey(
            {
                name: "RSA-OAEP",
                modulusLength: 4096,
                publicExponent: new Uint8Array([1, 0, 1]),
                hash: "SHA-256"
            },
            true,
            ["encrypt", "decrypt"]
            );
            var public = await crypto.subtle.exportKey("jwk", keyPair.publicKey);
            var private = await crypto.subtle.exportKey("jwk", keyPair.privateKey);
            var pair = {
                "public":keyPair.publicKey,
                "private":keyPair.privateKey
            };
            var exp = {
                "public":public,
                "private":private
            };
            localStorage['keypair'] = JSON.stringify(exp);
            pair.private.extractable = false;
            return pair;
    } else {
        var pair = JSON.parse(localStorage['keypair']);
        pair.public = await crypto.subtle.importKey(
            "jwk",
            pair.public,
            {
                "name":"RSA-OAEP",
                "hash":"SHA-256"
            },
            true,
            ["encrypt"]
        );
        pair.private = await crypto.subtle.importKey(
            "jwk",
            pair.private,
            {
                "name":"RSA-OAEP",
                "hash":"SHA-256"
            },
            true,
            ["decrypt"]
        );
        pair.private.extractable = false;
        return pair;
    }
}

async function encrypt(publicKey,data) {
    let enc = new TextEncoder();
    var encoded = enc.encode(data);
    return await window.crypto.subtle.encrypt(
        {
            name: "RSA-OAEP"
        },
        publicKey,
        encoded
    );
}

async function decrypt(privateKey,data) {
    let dec = new TextDecoder();
    return dec.decode(await window.crypto.subtle.decrypt(
        {
            name: "RSA-OAEP"
        },
        privateKey,
        data
    ));
}