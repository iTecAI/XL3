// Globals
var loggedIn = null;
var start = true;

async function refresh(data) {
    var endpoints = data.endpoints;
    $('#noconn').hide();
    loggedIn = data.loggedIn;
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
                'data-id':oc[c].id
            })
            .append(
                $('<span class="cmp-title"></span>').text(oc[c].name)
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
                )
            )
            .append(
                $('<div class="cmp-info"></div>')
                .append(
                    $('<div></div>')
                    .append($('<span>Characters: </span>'))
                    .append($('<span></span>').text(oc[c].characters.length))
                )
                .append(
                    $('<div></div>')
                    .append($('<span>Maps: </span>'))
                    .append($('<span></span>').text(Object.keys(oc[c].maps).length))
                )
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
                'data-id':pc[c].id
            })
            .append(
                $('<span class="cmp-title"></span>').text(pc[c].name)
                .append(
                    $('<button></button>')
                    .append(
                        $('<img>')
                        .attr('src','assets/icons/view.png')
                    )
                    .addClass('cmp-view')
                )
            )
            .append(
                $('<div class="cmp-info"></div>')
                .append(
                    $('<div></div>')
                    .append($('<span>Characters: </span>'))
                    .append($('<span></span>').text(pc[c].characters.length))
                )
                .append(
                    $('<div></div>')
                    .append($('<span>Maps: </span>'))
                    .append($('<span></span>').text(Object.keys(pc[c].maps).length))
                )
            )
            .appendTo($('#pcb-box'));
        }
    }

    start = false;
}