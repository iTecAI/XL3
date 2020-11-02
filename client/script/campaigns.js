var MAX_CAMPAIGNS = null;

$(document).ready(async function(){
    MAX_CAMPAIGNS = Number(await getConfig('CAMPAIGNS','max_campaigns'));
    var current_campaigns = await $.get({
        url: 'http://' + window.location.host + '/campaigns/'+fingerprint+'/'
    });
    console.log(current_campaigns);
    var owned_campaigns = current_campaigns.owned_campaigns.length;

    $('#cur-owned').text(owned_campaigns);
    $('#max-ownable').text(MAX_CAMPAIGNS);

    $('#new-campaign-button').on('click',function(){
        $('#new-campaign-dialog .form input').val('');
        activateDialog('#new-campaign-dialog');
    });
    $('#new-campaign-submit').on('click',function(){
        var data = getFormValues('#new-campaign-submit');
        var name = data['campaign-name'];
        var psw = data['campaign-password'];
        var cpsw = data['campaign-password-confirm'];
        if (name.length > 0 && psw == cpsw) {
            cpost(
                '/campaigns/'+fingerprint+'/new/',
                {
                    name: name,
                    password: psw
                },
                function(data){
                    console.log(data);
                    $('#modal').trigger('click');
                    bootbox.alert('Created new campaign with name '+data.new_campaign.name+' and ID '+data.new_campaign.id+'.');
                },
                {
                    alert: true
                }
            );
        }
    });
});