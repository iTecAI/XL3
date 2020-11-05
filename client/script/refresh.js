// Globals
var loggedIn = null;
var start = true;
var uid = null;

async function refresh(data) {
    var endpoints = data.endpoints;
    $('#noconn').hide();
    loggedIn = data.loggedIn;
    uid = data.userId;
    if (loggedIn) {
        $('#characters-nav').show(250);
        $('#campaigns-nav').show(250);
    } else {
        $('#characters-nav').hide(250);
        $('#campaigns-nav').hide(250);
    }
    
    if (endpoints.client || start) {
        cget(
            '/client/'+fingerprint+'/settings/',
            {},
            true,
            function(data) {
                var settings = Object.keys(data.settings);
                for (var s=0;s<settings.length;s++) {
                    $('#client-settings-'+settings[s]).attr('placeholder','Current: '+data.settings[settings[s]]);
                }
            }
        );
    }
    if ((endpoints.characters || start) && window.location.pathname.includes('characters')) {
        $('#info-max-characters').text(MAX_CHARACTERS);
        cget(
            '/client/'+fingerprint+'/characters/',
            {},false,
            function(data){
                $('#info-cur-characters').text(data.owned.length);
                if (data.owned.length > 0) {
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
                }
            }
        );
    }
    if ((endpoints.campaigns || start) && window.location.pathname.includes('campaigns')) {
        var current_campaigns = await $.get({
            url: 'http://' + window.location.host + '/campaigns/'+fingerprint+'/'
        });
        MAX_CAMPAIGNS = Number(await getConfig('CAMPAIGNS','max_campaigns'));
        var owned_campaigns = current_campaigns.owned_campaigns.length;
        $('#cur-owned').text(owned_campaigns);
        $('#max-ownable').text(MAX_CAMPAIGNS);

        var oc = current_campaigns.owned_campaigns;
        console.log(oc);
        var pc = current_campaigns.participating_campaigns;
        $('#ocb-box').html('');
        for (var c=0;c<oc.length;c++) {
            $('<div></div>')
            .addClass('owned-campaign')
            .addClass('campaign')
            .attr({
                id:'cbox-'+oc[c].id,
                'data-id':oc[c].id,
                'data-cmp':JSON.stringify(oc[c])
            })
            .append(
                $('<span class="cmp-title noselect"></span>').text(oc[c].name)
                .append(
                    $('<button></button>')
                    .append(
                        $('<img>')
                        .attr('src','assets/icons/delete.png')
                    )
                    .addClass('cmp-delete')
                    .attr('data-id',oc[c].id)
                    .on('click',function(event){
                        var path = '/campaigns/'+fingerprint+'/'+$(this).attr('data-id')+'/delete/';
                        console.log(path);
                        cpost(
                            path,
                            {},function(data){
                                console.log(data);
                            },{
                                alert:true
                            }
                        );
                    })
                )
                .append(
                    $('<button></button>')
                    .append(
                        $('<img>')
                        .attr('src','assets/icons/edit-white.png')
                    )
                    .addClass('cmp-edit')
                    .on('click',function(){
                        loadCampaign(JSON.parse($(this).parents('.campaign').attr('data-cmp')),true);
                    })
                )
            )
            .append(
                $('<div class="cmp-info noselect"></div>')
                .append(
                    $('<div></div>')
                    .append($('<span>Characters: </span>'))
                    .append($('<span></span>').text(oc[c].characters.length))
                    .append($('<span> / </span>'))
                    .append($('<span></span>').text(cond(oc[c].settings.max_characters.value <= MAX_CMP_CHARS,oc[c].settings.max_characters.value,MAX_CMP_CHARS)))
                )
                .append(
                    $('<div></div>')
                    .append($('<span>Maps: </span>'))
                    .append($('<span></span>').text(Object.keys(oc[c].maps).length))
                    .append($('<span> / </span>'))
                    .append($('<span></span>').text(MAX_CMP_MAPS))
                )
            )
            .append(
                $('<div class="cmp-id-box"></div>')
                .append($('<span class="noselect">ID: </span>'))
                .append($('<span></span>').text(oc[c].id))
            )
            .appendTo($('#ocb-box'));
        }
        $('#pcb-box').html('');
        for (var c=0;c<pc.length;c++) {
            $('<div></div>')
            .addClass('participating-campaign')
            .addClass('campaign')
            .attr({
                id:'pcbox-'+pc[c].id,
                'data-id':pc[c].id,
                'data-cmp':JSON.stringify(pc[c])
            })
            .append(
                $('<span class="cmp-title noselect"></span>').text(pc[c].name)
                .append(
                    $('<button></button>')
                    .append(
                        $('<img>')
                        .attr('src','assets/icons/view.png')
                    )
                    .addClass('cmp-view')
                    .on('click',function(){
                        loadCampaign(JSON.parse($(this).parents('.campaign').attr('data-cmp')),false);
                    })
                )
            )
            .append(
                $('<div class="cmp-info noselect"></div>')
                .append(
                    $('<div></div>')
                    .append($('<span>Characters: </span>'))
                    .append($('<span></span>').text(pc[c].characters.length))
                    .append($('<span> / </span>'))
                    .append($('<span></span>').text(cond(pc[c].settings.max_characters.value <= MAX_CMP_CHARS,pc[c].settings.max_characters.value,MAX_CMP_CHARS)))
                )
                .append(
                    $('<div></div>')
                    .append($('<span>Maps: </span>'))
                    .append($('<span></span>').text(Object.keys(pc[c].maps).length))
                    .append($('<span> / </span>'))
                    .append($('<span></span>').text(MAX_CMP_MAPS))
                )
            )
            .append(
                $('<div class="cmp-id-box"></div>')
                .append($('<span class="noselect">ID: </span>'))
                .append($('<span></span>').text(pc[c].id))
            )
            .appendTo($('#pcb-box'));
        }
        if ($('#campaign-panel').hasClass('active')) {
            var ind = null;
            for (var c=0;c<oc.length;c++) {
                if (oc[c].id == $('#campaign-panel').attr('data-id')) {
                    ind = c;
                    break;
                }
            }
            if (ind != null) {
                loadCampaign(oc[ind],$('#campaign-panel').prop('data-editing'));
            }
        }
    }
    if ((endpoints.campaigns || start) && window.location.pathname.includes('player')) {
        var current_map = await $.get({
            url: 'http://' + window.location.host + '/campaigns/'+fingerprint+'/player/'+CAMPAIGN+'/'+MAP+'/'
        });
        onPlayerRefresh(current_map.data);
    }

    start = false;
}