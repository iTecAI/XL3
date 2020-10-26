var MAX_CAMPAIGNS = null;

$(document).ready(async function(){
    MAX_CAMPAIGNS = Number(await getConfig('CAMPAIGNS','max_campaigns'));
    var current_campaigns = await $.get({
        url: 'http://' + window.location.host + '/campaigns/'+fingerprint+'/'
    });
    var owned_campaigns = current_campaigns.owned_campaigns.length;
});