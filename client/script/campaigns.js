var MAX_CAMPAIGNS = null;
var MAX_CMP_CHARS = null;
var MAX_CMP_MAPS = null;

function loadCampaign(cmp,editing) {
    if(editing){editing = true;}else{editing = false;}
    $('#cmp-characters-list').html('');
    $('#campaign-panel').attr('data-id',cmp.id);
    $('#campaign-panel').prop('data-editing',editing);
    cpost(
        '/characters/'+fingerprint+'/batch/',
        {batch:cmp.characters},
        function(data){
            for (var c=0;c<data.characters.length;c++) {
                $('#cmp-characters-list').append(buildCmpCharacter(data.characters[c],editing));
            }
        },
        {
            alert:true
        }
    );
    activateitem('#campaign-panel');
}

function buildCmpCharacter(item,editable) {
    var data = item.data;
    if (data.image.length == 0) {
        var img = 'assets/logo_med.png';
    } else {
        var img = data.image;
    }
    var element = $('<div class="character-panel"></div>')
        .attr('id', 'character_panel_' + item.cid)
        .attr('data-id', item.cid)
        .append(
            $('<div class="char-caption"></div>')
                .append($('<h4></h4>').text(data.name)).css('font-family', 'raleway-heavy')
                .append(
                    $('<span class="race-class-line"></span>')
                        .text(data.race + ' - ' + data.class_display + ' (Level ' + data.level + ')')
                        .css({
                            'font-style': 'italic',
                            'font-family': 'raleway-regular'
                        })
                )
        );
    element.append(
        $('<div class="char-img"></div>').append($('<img alt="Character Image" src="' + img + '">'))
    );
    if (editable || item.owner == uid) {
        element.append(
            $('<button class="character-menu-btn"><img src="assets/icons/menu.png"></button>')
                .on('click', function (event) {
                    activateitem($(event.target).parent().parent().children('.character-menu'));
                })
        );
        element.append(
            $('<div class="character-menu transient"></div>')
                .append(
                    $('<button></button>')
                        .addClass('character-menu-edit')
                        .addClass('character-menu-item')
                        .attr('data-action', 'edit')
                        .text('Edit')
                        .on('click', function (event) {
                            window.location.href = window.origin +'/characters?char='+$($(event.delegateTarget).parents('.character-panel')[0]).attr('data-id');
                        })
                ).append(
                    $('<button></button>')
                        .addClass('character-menu-delete')
                        .addClass('character-menu-item')
                        .attr('data-action', 'delete')
                        .text('Remove from Campaign')
                        .on('click', function (event) {
                            cpost(
                                '/campaigns/' + fingerprint + '/' + $('#campaign-panel').attr('data-id') + '/remove_character/',
                                {
                                    charid: $($(event.delegateTarget).parents('.character-panel')[0]).attr('data-id')
                                }, function (data) {
                                    console.log(data);
                                }, { 'alert': true }
                            );
                            $(document).trigger('click');
                            loadCampaign($('#campaign-panel').attr('data-id'),$('#campaign-panel').prop('data-editing'));
                        })
                )
        );
    }
    

    return element;
}

$(document).ready(async function () {
    var cmp_config = (await getBatchConfig({
        CAMPAIGNS: [
            'max_campaigns',
            'characters_per_campaign',
            'maps_per_campaign'
        ]
    })).CAMPAIGNS;

    MAX_CAMPAIGNS = Number(cmp_config.max_campaigns);
    MAX_CMP_CHARS = Number(cmp_config.characters_per_campaign);
    MAX_CMP_MAPS = Number(cmp_config.maps_per_campaign);
    var current_campaigns = await $.get({
        url: 'http://' + window.location.host + '/campaigns/' + fingerprint + '/'
    });
    console.log(current_campaigns);
    var owned_campaigns = current_campaigns.owned_campaigns.length;

    $('#cur-owned').text(owned_campaigns);
    $('#max-ownable').text(MAX_CAMPAIGNS);

    $('#new-campaign-button').on('click', function () {
        $('#new-campaign-dialog .form input').val('');
        activateDialog('#new-campaign-dialog');
    });
    $('#new-campaign-submit').on('click', function () {
        var data = getFormValues('#new-campaign-submit');
        var name = data['campaign-name'];
        var psw = data['campaign-password'];
        var cpsw = data['campaign-password-confirm'];
        if (name.length > 0 && psw == cpsw) {
            cpost(
                '/campaigns/' + fingerprint + '/new/',
                {
                    name: name,
                    password: psw
                },
                function (data) {
                    console.log(data);
                    $('#modal').trigger('click');
                    bootbox.alert('Created new campaign with name ' + data.new_campaign.name + ' and ID ' + data.new_campaign.id + '.');
                },
                {
                    alert: true
                }
            );
        }
    });
});