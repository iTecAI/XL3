$(document).ready(function(){
    getKeyPair().then(async function(data){
        console.log(data);
        var enc = await encrypt(data.public,'potat');
        console.log(await decrypt(data.private,enc));
    });
});