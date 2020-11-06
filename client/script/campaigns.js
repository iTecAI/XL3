var MAX_CAMPAIGNS = null;
var MAX_CMP_CHARS = null;
var MAX_CMP_MAPS = null;

function loadCampaign(cmp, editing) {
    if (editing) { editing = true; } else { editing = false; }
    $('#campaign-panel').attr('data-id', cmp.id);
    $('#campaign-panel').prop('data-editing', editing);
    $('#cmp-settings-toggle').toggle(editing);
    $('#new-map-btn').toggle(editing);
    cpost(
        '/characters/' + fingerprint + '/batch/', { batch: cmp.characters },
        function(data) {
            $('#cmp-characters-list').html('');
            for (var c = 0; c < data.characters.length; c++) {
                $('#cmp-characters-list').append(buildCmpCharacter(data.characters[c], editing));
            }
        }, {
            alert: true
        }
    );
    var settings = cmp.settings;
    $('#settings-area > table tbody').html('');
    for (var s = 0; s < Object.keys(settings).length; s++) {
        var setting = settings[Object.keys(settings)[s]];
        var row = $('<tr></tr>')
            .attr('data-setting', Object.keys(settings)[s])
            .append(
                $('<td></td>').text(setting.display_name)
            );
        if (setting.type == 'bool') {
            row.append(
                $('<td></td>')
                .append(
                    $('<label class="switch small"></label>')
                    .append(
                        $('<input type="checkbox">').prop('checked', setting.value)
                        .on('change', function(event) {
                            var set = $($(this).parents('tr')[0]).attr('data-setting');
                            var value = $(this).prop('checked');
                            cpost(
                                '/campaigns/' + fingerprint + '/' + $('#campaign-panel').attr('data-id') + '/setting/', {
                                    name: set,
                                    value: value
                                },
                                function(data) {

                                }, {
                                    alert: true
                                }
                            );
                            return;
                        })
                    )
                    .append(
                        $('<span class="slider round"></span>')
                    )
                )
            );
        } else if (setting.type == 'int') {
            row.append(
                $('<td></td>')
                .append(
                    $('<input class="cmp-settings-input">')
                    .attr({
                        min: setting.min,
                        max: setting.max
                    })
                    .val(setting.value)
                    .on('change', function(event) {
                        var set = $($(this).parents('tr')[0]).attr('data-setting');
                        var value = Number($(this).val());
                        if (isNaN(value)) {
                            bootbox.alert('Value must be a number.');
                            $(this).val($(this).attr('min'));
                            return;
                        }
                        if (value <= Number($(this).attr('max')) && value >= Number($(this).attr('min'))) {
                            cpost(
                                '/campaigns/' + fingerprint + '/' + $('#campaign-panel').attr('data-id') + '/setting/', {
                                    name: set,
                                    value: value
                                },
                                function(data) {
                                    console.log(data);
                                }, {
                                    alert: true
                                }
                            );
                            return;
                        } else {
                            bootbox.alert('Value must be a number from ' + $(this).attr('min') + ' through ' + $(this).attr('max') + '.');
                            $(this).val($(this).attr('min'));
                            return;
                        }
                    })
                )
            );
        }
        row.appendTo($('#settings-area > table tbody'));
    }

    var mkeys = Object.keys(cmp.maps);
    $('#cmp-maps-list').html('');
    for (var m = 0; m < mkeys.length; m++) {
        $('<div class="map noselect"></div>')
            .attr({
                id: 'map-' + cmp.maps[mkeys[m]].image_id,
                'data-id': cmp.maps[mkeys[m]].image_id
            })
            .append(
                $('<div class="map-box noscroll"></div>').append(
                    $('<img>')
                    .attr('src', '/images/' + cmp.maps[mkeys[m]].image_id)
                )
            )
            .append($('<div class="grad-overlay"></div>'))
            .append(
                $('<div class="map-desc"></div>')
                .append(
                    $('<div></div>')
                    .append($('<span></span>').text(cmp.maps[mkeys[m]].name))
                    .append($('<span></span>').text(cmp.maps[mkeys[m]].grid.columns + ' x ' + cmp.maps[mkeys[m]].grid.rows))
                    .append($('<span></span>').text(cmp.maps[mkeys[m]].grid.size + 'ft. grid'))
                )
                .append(
                    $('<button class="delete-map" data-tooltip="Delete" data-tooltip-location="right"></button>')
                    .append($('<img src="assets/icons/delete-black.png">'))
                    .toggle(editing)
                    .on('click', function(event) {
                        cpost(
                            '/campaigns/' + fingerprint + '/' + $('#campaign-panel').attr('data-id') + '/maps/remove/' + $($(event.delegateTarget).parents('.map')[0]).attr('data-id'), {},
                            function() {}, { alert: true }
                        );
                    })
                )
                .append(
                    $('<button class="play-map" data-tooltip="Play" data-tooltip-location="right"></button>')
                    .append($('<img src="assets/icons/play.png">'))
                    .on('click', function(event) {
                        window.location = window.location.origin + '/player?cmp=' + $('#campaign-panel').attr('data-id') + '&map=' + $($(event.delegateTarget).parents('.map')[0]).attr('data-id');
                    })
                )
            )
            .appendTo($('#cmp-maps-list'));
    }

    activateitem('#campaign-panel');
}

function buildCmpCharacter(item, editable) {
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
            .on('click', function(event) {
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
                .on('click', function(event) {
                    window.location.href = window.origin + '/characters?char=' + $($(event.delegateTarget).parents('.character-panel')[0]).attr('data-id');
                })
            ).append(
                $('<button></button>')
                .addClass('character-menu-delete')
                .addClass('character-menu-item')
                .attr('data-action', 'delete')
                .text('Remove from Campaign')
                .on('click', function(event) {
                    cpost(
                        '/campaigns/' + fingerprint + '/' + $('#campaign-panel').attr('data-id') + '/remove_character/', {
                            charid: $($(event.delegateTarget).parents('.character-panel')[0]).attr('data-id')
                        },
                        function(data) {
                            console.log(data);
                        }, { 'alert': true }
                    );
                    $(document).trigger('click');
                    loadCampaign($('#campaign-panel').attr('data-id'), $('#campaign-panel').prop('data-editing'));
                })
            )
        );
    }


    return element;
}

$(document).ready(async function() {
    var parameters = getParams();
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

    $('#new-campaign-button').on('click', function() {
        $('#new-campaign-dialog .form input').val('');
        activateDialog('#new-campaign-dialog');
    });
    $('#new-campaign-submit').on('click', function() {
        var data = getFormValues('#new-campaign-submit');
        var name = data['campaign-name'];
        var psw = data['campaign-password'];
        var cpsw = data['campaign-password-confirm'];
        if (name.length > 0 && psw == cpsw) {
            cpost(
                '/campaigns/' + fingerprint + '/new/', {
                    name: name,
                    password: psw
                },
                function(data) {
                    console.log(data);
                    $('#modal').trigger('click');
                    bootbox.alert('Created new campaign with name ' + data.new_campaign.name + ' and ID ' + data.new_campaign.id + '.');
                }, {
                    alert: true
                }
            );
        }
    });
    if (Object.keys(parameters).includes('cmpid')) {
        var dat = await $.post({
            url: 'http://' + window.location.host + '/campaigns/' + fingerprint + '/batch/',
            data: JSON.stringify({ batch: [parameters.cmpid] })
        });
        if (dat.owned_campaigns.length == 1) {
            loadCampaign(dat.owned_campaigns[0], true);
        } else if (dat.participating_campaigns.length == 1) {
            loadCampaign(dat.participating_campaigns[0], false);
        } else {
            window.location.href = window.location.origin + window.location.pathname;
        }
    }

    $('#cmp-settings-toggle').on('click', function() {
        $('#cmp-settings').toggleClass('active');
        $('#cmp-modal').toggleClass('active');
    });
    $('#cmp-modal').on('click', function() {
        $('#cmp-settings').toggleClass('active', false);
        $('#cmp-modal').toggleClass('active', false);
    });
    $('#new-map-btn input').on('change', function() {
        var file = document.querySelector('#new-map-btn input').files[0];
        var reader = new FileReader();
        reader.addEventListener("load", function() {
            if (reader.result.includes('image/png') || reader.result.includes('image/jpg') || reader.result.includes('image/jpeg')) {
                console.log(reader.result);
                var path = $('#new-map-btn input').val().replace(/\\/g, '/').split('fakepath/')[1];
                $('#map-path').text(path);
                $('#new-map-dialog input').val('');
                $('#new-map-dialog').attr('data-uri', reader.result);
                $('#new-map-dialog').addClass('active');
                $('#cmp-modal').addClass('active');
            } else {
                bootbox.alert('Image must be a .png or .jpeg.');
                return;
            }

        }, false);

        if (file) {
            reader.readAsDataURL(file);
        }
    });
    $('#new-map-submit').on('click', function() {
        var data = getFormValues('#new-map-submit');
        var mname = data['map-name'];
        var rows = data['map-rows'];
        var cols = data['map-columns'];
        var gsize = data['map-grid-size'];
        if (mname.length > 0 && rows.length > 0 && cols.length > 0 && gsize.length > 0) {
            rows = Number(rows);
            cols = Number(cols);
            gsize = Number(gsize);
            if (isNaN(rows) || isNaN(cols) || isNaN(gsize)) {
                bootbox.alert('Rows, Columns, and Grid Size must be whole numbers.');
                return;
            }
            rows = Math.round(rows);
            cols = Math.round(cols);
            gsize = Math.round(gsize);
            if (rows < 1 || cols < 1 || gsize < 1) {
                bootbox.alert('Rows, Columns, and Grid Size must be greater than 0.');
                return;
            }
            var dat = {
                data: $('#new-map-dialog').attr('data-uri'),
                rows: rows,
                columns: cols,
                name: mname,
                gridsize: gsize
            };
            cpost(
                '/campaigns/' + fingerprint + '/' + $('#campaign-panel').attr('data-id') + '/maps/add/',
                dat,
                console.log, {
                    alert: true
                }
            );
            $('#cmp-modal').trigger('click');
        } else {
            bootbox.alert('Please fill in all inputs.');
            return;
        }
    });

    $('#join-campaign-button').on('click', function(event) {
        var cmp = null;
        bootbox.prompt('Enter campaign ID (Check with your DM)', function(result) {
            if (!result) { return; }
            cmp = result;
            cpost('/campaigns/' + fingerprint + '/check_password_protected/' + result + '/', {}, function(data) {
                if (data.password_protected) {
                    bootbox.prompt({
                        title: 'Campaign is password-protected. Please enter password.',
                        inputType: 'password',
                        'callback': function(result) {
                            cpost(
                                '/campaigns/' + fingerprint + '/join/', {
                                    campaign: cmp,
                                    passhash: sha256(result)
                                },
                                function(data) {}, { alert: true }
                            );
                        }
                    })
                } else {
                    cpost(
                        '/campaigns/' + fingerprint + '/join/', {
                            campaign: cmp
                        },
                        function(data) {}, { alert: true }
                    );
                }
            }, { alert: true });
        });
    });
});