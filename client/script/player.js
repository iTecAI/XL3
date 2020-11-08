var CAMPAIGN = null;
var MAP = null;
var CURSOR = 'default';
var OWNER = false;
var CMP_DATA = {};
var MAP_DATA = {};
var CMP_CHARS = {};
var CTX_TARGET = null;

// Context menu definitions
var CONTEXT = {
    '#entities': {
        dm: [
            {
                conditions: {},
                items: ['add-npc']
            },
            {
                conditions: {
                    system: {
                        has_character: true,
                        placed_character: false
                    }
                },
                items: ['add-player']
            }
        ],
        pc: [
            {
                conditions: {
                    system: {
                        has_character: true,
                        placed_character: false
                    }
                },
                items: ['add-player']
            }
        ]
    },
    '.obscure': {
        dm: [
            {
                conditions: {},
                items: ['remove-obscure']
            }
        ],
        pc: []
    }
}

var SIZES = {
    tiny: 2,
    small: 5,
    medium: 5,
    large: 10,
    huge: 15,
    gargantuan: 20
};

// Setup pan/zoom - https://stackoverflow.com/a/42777567 (with modifications)
var scale = 1,
    panning = false,
    xoff = 0,
    yoff = 0,
    _start = { x: 0, y: 0 },
    zoomMin = 0.08,
    zoomMax = 30

function setTransform() {
    $('#map').css('transform', "translate(" + xoff + "px, " + yoff + "px) scale(" + scale + ")");
}

function mPost(endpoint, data, success, options) {
    cpost(
        '/campaigns/' + fingerprint + '/player/' + CAMPAIGN + '/' + MAP + endpoint,
        data, success, options
    );
}
function mGet(endpoint, data, success, alert) {
    cget(
        '/campaigns/' + fingerprint + '/player/' + CAMPAIGN + '/' + MAP + endpoint,
        data, alert, success
    );
}

function getCID() {
    var id = null;
    for (var ch = 0; ch < CMP_DATA.characters.length; ch++) {
        if (CMP_CHARS[CMP_DATA.characters[ch]].owner == uid) {
            id = CMP_DATA.characters[ch];
            break;
        }
    }
    return id;
}

function CapFirstLetter(str) {
    return str.slice(0, 1).toUpperCase() + str.slice(1, str.length);
}

function onPlayerRefresh(data) {
    var map = data.data;
    var owner = data.is_owner;
    var cmp = data.cmp;
    var chars = data.characters;
    CMP_DATA = data.cmp;
    MAP_DATA = data.data;
    CMP_CHARS = data.characters;
    OWNER = owner == true;
    $('#map-name').text(map.name);
    $('#map-dims').text(map.grid.columns + ' x ' + map.grid.rows + ' (' + (map.grid.columns * map.grid.size) + ' ft. x ' + (map.grid.rows * map.grid.size) + ' ft.)');
    $('#map-scale').text(map.grid.size + ' ft.');

    $('#st-name').val(map.name);
    $('#st-grid-rows').val(map.grid.rows);
    $('#st-grid-columns').val(map.grid.columns);
    $('#st-grid-size').val(map.grid.size);

    $('#map-img img').attr('src', '/images/' + map.image_id);
    $('#dm-tools').toggleClass('active', owner);
    $('#map-settings-btn').toggle(owner);
    $('#user-tools').toggleClass('active', !owner);

    $('#map').css('cursor', CURSOR);

    var eKeys = Object.keys(map.entities);
    var dummy_entities = $('<div></div>');
    for (var e = 0; e < eKeys.length; e++) {
        var ent = map.entities[eKeys[e]];
        if (ent.obscure) {
            $('<div class="entity obscure"></div>')
                .css({
                    top: ent.pos.y + 'px',
                    left: ent.pos.x + 'px',
                    width: ent.dim.w + 'px',
                    height: ent.dim.h + 'px'
                })
                .attr({
                    'id': 'entity-' + eKeys[e],
                    'data-id': eKeys[e]
                })
                .toggleClass('owned', owner)
                .appendTo(dummy_entities);
        } else if (ent.character) {
            var char = chars[ent.id];
            if (char.physical.size.length > 0) {
                if (Object.keys(SIZES).includes(char.physical.size.toLowerCase())) {
                    var size = SIZES[char.physical.size.toLowerCase()] * ($('#map').width() / (map.grid.size * map.grid.columns));
                } else {
                    var size = SIZES.medium * ($('#map').width() / (map.grid.size * map.grid.columns));
                }
            } else {
                var size = SIZES.medium * ($('#map').width() / (map.grid.size * map.grid.columns));
            }
            if (char.image.length > 0) {
                var img = char.image;
            } else {
                var img = 'assets/logo.png';
            }
            if (CMP_CHARS[ent.id].owner == uid) {
                var css = { border: '2px solid var(--em-font-color2)' };
                var cstat = CMP_CHARS[ent.id].name + ' - ' + CMP_CHARS[ent.id].hp + '/' + CMP_CHARS[ent.id].max_hp + ' hp';
            } else {
                var css = {};
                var cstat = CMP_CHARS[ent.id].name;
            }
            if (OWNER) {
                var cstat = CMP_CHARS[ent.id].name + ' - ' + CMP_CHARS[ent.id].hp + '/' + CMP_CHARS[ent.id].max_hp + ' hp';
            }
            $('<div class="entity character"></div>')
                .css({
                    top: ent.pos.y + 'px',
                    left: ent.pos.x + 'px',
                    width: size + 'px',
                    height: size + 'px',
                    'border-radius': size / 2 + 'px'
                })
                .attr({
                    'id': 'entity-' + eKeys[e],
                    'data-id': eKeys[e],
                    'data-char': ent.id
                })
                .toggleClass('owned', owner)
                .append(
                    $('<div class="img-container"></div>').append(
                        $('<img>').attr('src', img)
                    ).css({'border-radius': size / 2 + 'px'})
                )
                .append($('<div class="character-stats"></div>').text(cstat))
                .css(css)
                .appendTo(dummy_entities);
        } else if (ent.npc) {
            var data = ent.data;
            data.max_hp = data.hp + 0;
            if (data.size.length > 0) {
                if (Object.keys(SIZES).includes((data.size.toLowerCase()))) {
                    var size = SIZES[data.size.toLowerCase()] * ($('#map').width() / (map.grid.size * map.grid.columns));
                } else {
                    var size = SIZES.medium * ($('#map').width() / (map.grid.size * map.grid.columns));
                }
            } else {
                var size = SIZES.medium * ($('#map').width() / (map.grid.size * map.grid.columns));
            }
            if (data.img.length > 0) {
                var img = data.img;
            } else {
                var img = 'assets/logo.png';
            }
            if (OWNER) {
                var npc_stats = data.name + ' - ' + data.hp + '/' + data.max_hp + ' hp'
            } else {
                var npc_stats = data.name;
            }
            $('<div class="entity npc"></div>')
                .css({
                    top: ent.pos.y + 'px',
                    left: ent.pos.x + 'px',
                    width: size + 'px',
                    height: size + 'px',
                    'border-radius': size / 2 + 'px'
                })
                .attr({
                    'id': 'entity-' + eKeys[e],
                    'data-id': eKeys[e],
                    'data-npc': JSON.stringify(data)
                })
                .append(
                    $('<div class="img-container"></div>').append(
                        $('<img>').attr('src', img)
                    ).css({'border-radius': size / 2 + 'px'})
                )
                .append($('<div class="npc-stats"></div>').text(npc_stats))
                .appendTo(dummy_entities);
        }
    }
    $('#entities').html(dummy_entities.html());

    // Add event listeners
    $('.obscure').off('click');
    $('.obscure').on('click', function (event) {
        if (CURSOR != 'alias') { return; }
        mPost('/entity/remove/', { eid: $(event.delegateTarget).attr('data-id') }, function (data) { }, { alert: true });
    });
}

function getctx() {
    var ctx = CTX_TARGET;
    CTX_TARGET = null;
    $('#context-menu').hide();
    return ctx;
}

// Document setup & events

$(document).ready(function () {
    $('#context-menu').hide();
    $('.tool[data-cursor=' + CURSOR + ']').toggleClass('active', true);
    $('#map').css('cursor', CURSOR);
    var p = getParams();
    if (!Object.keys(p).includes('cmp') || !Object.keys(p).includes('map')) {
        window.location = window.location.origin + '/campaigns';
    }
    CAMPAIGN = p.cmp;
    MAP = p.map;

    $('#chat-expander').on('click', function () {
        $('#chat-panel').toggleClass('active');
    });

    $('#map-settings-btn').on('click', function () {
        $('#map-settings').toggleClass('active');
    });

    $('input.modifier').on('change', function (event) {
        var val = $(this).val();
        if ($(this).attr('type') == 'number') {
            val = Number(val);
            if (!isNaN(val) && val > 0) {
                mPost('/modify/', { path: $(this).attr('data-path'), value: val }, function (data) { }, { alert: true });
                return;
            }
            $(this).val('1');
        } else {
            mPost('/modify/', { path: $(this).attr('data-path'), value: val }, function (data) { }, { alert: true });
            return;
        }
    });

    $('.tool').on('click', function (event) {
        $('.tool').toggleClass('active', false);
        CURSOR = $(this).attr('data-cursor');
        $('.tool[data-cursor=' + CURSOR + ']').toggleClass('active', true);
        $('#map').css('cursor', CURSOR);
    });

    // Pan/Zoom functions - https://stackoverflow.com/a/42777567 (with modifications)
    $('#map').on('mousedown', function (e) {
        if (CURSOR != 'move') { return; }
        e.preventDefault();
        var ret = false;
        if ($(e.target).hasClass('entity') && !$(e.target).hasClass('obscure')) {
            $(e.target).toggleClass('moving', true);
            ret = true;
        }
        if ($(e.target).parents('.entity').length > 0 && !$(e.target).hasClass('obscure')) {
            var item = $(e.target).parents('.entity')[0];
            var proc = false;
            if (OWNER) {
                proc = true;
            } else if ($(item).hasClass('character') && CMP_CHARS[$(item).attr('data-char')].owner == uid) {
                proc = true;
            }

            if (proc) {
                $(item).toggleClass('moving', true);
                ret = true;
            }
        }

        if (ret) { return; }
        _start = { x: e.clientX - xoff, y: e.clientY - yoff };
        panning = true;
    });

    $(document).on('mouseup', function (e) {
        panning = false;

        if ($('#selector').hasClass('selecting')) {
            var o = {
                x: $('#selector').position().left / scale,
                y: $('#selector').position().top / scale,
                w: $('#selector').width(),
                h: $('#selector').height()
            };
            $('#selector').toggleClass('selecting', false);
            if (o.h < 10 || o.w < 10) { return; }
            mPost('/entity/add/obscure/', o, function (data) { }, { alert: true });
        }
        if ($('.entity.moving').length > 0) {
            mPost('/entity/modify/', {
                entity: $($('.entity.moving')[0]).attr('data-id'),
                batch: [
                    { path: 'pos.x', value: $($('.entity.moving')[0]).position().left / scale },
                    { path: 'pos.y', value: $($('.entity.moving')[0]).position().top / scale }
                ]
            }, function () { }, { alert: true });
            $('.entity.moving').toggleClass('moving', false);
        }
    });

    $('#map').on('mousemove', function (e) {
        if (!panning || CURSOR != 'move') {
            if ($('.entity.moving').length > 0 && CURSOR == 'move') {
                var opts = {
                    top: ((e.pageY - $('#map').offset().top) / scale - $('.entity.moving').height() / 2),
                    left: ((e.pageX - $('#map').offset().left) / scale - $('.entity.moving').width() / 2)
                };
                if (opts.top < 0) { opts.top = 0; }
                if (opts.left < 0) { opts.left = 0; }
                if (opts.top - $('.entity.moving').height() > $('#map').height()) { opts.top = $('#map').height() - $('.entity.moving').height(); }
                if (opts.left - $('.entity.moving').width() > $('#map').width()) { opts.left = $('#map').width() - $('.entity.moving').width(); }
                $('.entity.moving').css({ top: opts.top + 'px', left: opts.left + 'px' });
            }
            return;
        }
        e.preventDefault();
        xoff = (e.clientX - _start.x);
        yoff = (e.clientY - _start.y);
        setTransform();
    });

    $('#map').on('wheel', function (e) {
        if (CURSOR != 'move') { return; }
        e.preventDefault();
        // take the scale into account with the offset
        var xs = (e.clientX - xoff) / scale,
            ys = (e.clientY - yoff) / scale,
            delta = -e.originalEvent.deltaY;

        // get scroll direction & set zoom level
        (delta > 0) ? (scale *= 1.2) : (scale /= 1.2);
        if (scale < zoomMin) { scale = zoomMin; }
        if (scale > zoomMax) { scale = zoomMax; }

        // reverse the offset amount with the new scale
        xoff = e.clientX - xs * scale;
        yoff = e.clientY - ys * scale;

        setTransform();
    });

    // Selection box
    $('#map').on('mousedown', function (event) {
        if (CURSOR != 'crosshair') { return; }
        $('#selector').attr({
            'data-x': event.clientX - $('#map').offset().left,
            'data-y': event.clientY - $('#map').offset().top
        });
        $('#selector').css({
            top: $('#selector').attr('data-y') + 'px',
            left: $('#selector').attr('data-x') + 'px',
            width: '0px',
            height: '0px'
        });
        $('#selector').toggleClass('selecting', true);
    });
    $('#map').on('mousemove', function (event) {
        if (!$('#selector').hasClass('selecting')) { return; }
        var x = (event.clientX - $('#map').offset().left) / scale;
        var y = (event.clientY - $('#map').offset().top) / scale;
        var sx = Number($('#selector').attr('data-x')) / scale;
        var sy = Number($('#selector').attr('data-y')) / scale;
        if (x >= sx && y >= sy) {
            $('#selector').css({
                top: sy + 'px',
                left: sx + 'px',
                width: x - sx + 'px',
                height: y - sy + 'px'
            });
        } else if (x < sx && y >= sy) {
            $('#selector').css({
                top: sy + 'px',
                left: x + 'px',
                width: sx - x + 'px',
                height: y - sy + 'px'
            });
        } else if (x >= sx && y < sy) {
            $('#selector').css({
                top: y + 'px',
                left: sx + 'px',
                width: x - sx + 'px',
                height: sy - y + 'px'
            });
        } else if (x < sx && y < sy) {
            $('#selector').css({
                top: y + 'px',
                left: x + 'px',
                width: sx - x + 'px',
                height: sy - y + 'px'
            });
        }
    });
    $(document).on('contextmenu', function (event) {
        var ctx = null;
        for (var s = 0; s < Object.keys(CONTEXT).length; s++) {
            if ($(event.target).is(Object.keys(CONTEXT)[s])) {
                ctx = Object.keys(CONTEXT)[s];
                break;
            }
        }
        if ($(event.target).attr('id') == 'context-menu' || $(event.target).parents('#context-menu').length > 0) {
            event.preventDefault();
            return;
        }
        if (!ctx) { return; }
        event.preventDefault();
        var potential = CONTEXT[ctx][cond(OWNER, 'dm', 'pc')];
        $('#context-menu button').hide();
        var ct = 0;
        for (var p = 0; p < potential.length; p++) {
            var c = potential[p].conditions;
            var proceed = true;
            if (c.system) {
                var ks = Object.keys(c.system)
                for (var i = 0; i < ks.length; i++) {
                    if (ks[i] == 'has_character' && proceed) {
                        var found = false;
                        for (var ch = 0; ch < CMP_DATA.characters.length; ch++) {
                            if (CMP_CHARS[CMP_DATA.characters[ch]].owner == uid) {
                                found = true;
                                break;
                            }
                        }
                        proceed = found == c.system[ks[i]];
                    }
                    if (ks[i] == 'placed_character' && proceed) {
                        var found = false;
                        var id = null;
                        for (var ch = 0; ch < CMP_DATA.characters.length; ch++) {
                            if (CMP_CHARS[CMP_DATA.characters[ch]].owner == uid) {
                                found = true;
                                id = CMP_DATA.characters[ch];
                                break;
                            }
                        }
                        if (!found) {
                            proceed = !c.system[ks[i]]
                        } else {
                            var found = false;
                            for (var e = 0; e < Object.keys(MAP_DATA.entities).length; e++) {
                                if (MAP_DATA.entities[Object.keys(MAP_DATA.entities)[e]].character && MAP_DATA.entities[Object.keys(MAP_DATA.entities)[e]].id == id) {
                                    found = true;
                                    break;
                                }
                            }
                            proceed = found == c.system[ks[i]];
                        }
                    }
                }
            }
            if (c.classes) {
                var ks = Object.keys(c.classes)
                for (var i = 0; i < ks.length; i++) {
                    if ($(event.target).hasClass(ks[i]) != c.classes[ks[i]]) {
                        proceed = false;
                    }
                }
            }

            if (proceed) {
                for (var i = 0; i < potential[p].items.length; i++) {
                    $('#ctx_' + potential[p].items[i]).show();
                    ct++;
                }
            }
        }
        if (ct > 0) {
            CTX_TARGET = { el: event.target, x: (event.pageX - $('#map').offset().left) / scale, y: (event.pageY - $('#map').offset().top) / scale };
            $('#context-menu').css({
                top: event.pageY + 5 + 'px',
                left: event.pageX + 5 + 'px'
            }).show();
        }
    });
    $(document).on('click', function (event) {
        if ($(event.target).attr('id') == 'context-menu' || $(event.target).parents('#context-menu').length > 0) {
            return;
        }
        CTX_TARGET = null;
        $('#context-menu').hide();
    });

    // Context Menu Items
    $('#ctx_remove-obscure').on('click', function (event) {
        var el = getctx();
        mPost('/entity/remove/', { eid: $(el.el).attr('data-id') }, function (data) { }, { alert: true });
    });
    $('#ctx_add-player').on('click', function (event) {
        var el = getctx();
        mPost('/entity/add/player/', { charid: getCID(), x: el.x, y: el.y }, function (data) { }, { alert: true });
    });
    $('#ctx_add-npc').on('click', function (event) {
        var el = getctx();
        $('#add-npc-dialog').attr({
            'data-x': el.x,
            'data-y': el.y
        });
        $('#npc-img-con img').attr('src', 'assets/logo_med.png');
        $('#add-npc-dialog input').val('');
        $('#add-npc-dialog select').val('medium');
        $('#add-npc-dialog tbody').html('');
        $('#add-npc-dialog').toggleClass('active', true);
        $('#noclosemodal').toggleClass('active', true);
        $('#npc-cancel-btn').off('click');
        $('#npc-submit-btn').off('click');
        $('#npc-cancel-btn').on('click',function(event){
            $('#npc-img-con img').attr('src', 'assets/logo_med.png');
            $('#add-npc-dialog input').val('');
            $('#add-npc-dialog select').val('medium');
            $('#add-npc-dialog tbody').html('');
            $('#add-npc-dialog').toggleClass('active', false);
            $('#noclosemodal').toggleClass('active', false);
        });
        $('#npc-buttons button:first-child').on('click',function(event){
            console.log('click');
            var data = JSON.parse($('#add-npc-dialog').attr('data-selected'));
            data.hp = Number($('#npc-hp-input').val());
            data.ac = Number($('#npc-ac-input').val());
            data.name = $('#npc-name-input').val();
            data.size = $('#npc-size-input').val();
            data.img = $('#npc-img-con img').attr('src');
            mPost('/entity/add/npc/',{
                x:Number($('#add-npc-dialog').attr('data-x')),
                y:Number($('#add-npc-dialog').attr('data-y')),
                data:data,
            },function(data){console.log(data);},{alert:true});
            $('#npc-img-con img').attr('src', 'assets/logo_med.png');
            $('#add-npc-dialog input').val('');
            $('#add-npc-dialog select').val('medium');
            $('#add-npc-dialog tbody').html('');
            $('#add-npc-dialog').toggleClass('active', false);
            $('#noclosemodal').toggleClass('active', false);
        });
    });


    // Add NPC Dialog
    $('#npc-search input').on('change', function (event) {
        if ($(this).val().length == 0) {
            $('#npc-table tbody').html('');
            $('#no-content-icon').show();
        } else {
            mPost(
                '/creatures/search/',
                {
                    search: $(this).val().toLowerCase(),
                    limit: 100
                },
                function (data) {
                    console.log(data);
                    var dummy_body = $('<tbody></tbody>');
                    var creatures = data.creatures;
                    for (var c = 0; c < creatures.length; c++) {
                        creatures[c].hit_dice = '' + creatures[c].data.hit_dice;
                        delete creatures[c].data;

                        if (creatures[c].hit_dice != 'undefined') {
                            var hd_str = creatures[c].hp + ' - (' + creatures[c].hit_dice + ')';
                        } else {
                            var hd_str = creatures[c].hp;
                        }

                        if (creatures[c].src == 'critterdb') {
                            var hb_str = '⭐ - ';
                        } else {
                            var hb_str = '';
                        }

                        $('<tr class="npc-item"></tr>')
                            .attr('data-creature', JSON.stringify(creatures[c]))
                            .attr('data-slug', creatures[c].slug)
                            .append(
                                $('<td class="npc-cell-name"></td>').text(hb_str + CapFirstLetter(creatures[c].name))
                            )
                            .append(
                                $('<td class="npc-cell-size"></td>').text(CapFirstLetter(creatures[c].size))
                            )
                            .append(
                                $('<td class="npc-cell-type"></td>').text(CapFirstLetter(creatures[c].type))
                            )
                            .append(
                                $('<td class="npc-cell-cr"></td>').text(creatures[c].challenge_display)
                            )
                            .append(
                                $('<td class="npc-cell-hp"></td>').text(hd_str)
                            )
                            .append(
                                $('<td class="npc-cell-ac"></td>').text(creatures[c].ac)
                            )
                            .append(
                                $('<td class="npc-cell-source"></td>').text(CapFirstLetter(creatures[c].src))
                            )
                            .appendTo(dummy_body);
                    }
                    $('#npc-table tbody').html(dummy_body.html());
                    $('.npc-item').on('click', function (event) {
                        $('.npc-item.selected').removeClass('selected');
                        $(this).addClass('selected');
                        var data = JSON.parse($(this).attr('data-creature'));
                        $('#npc-name-input').val(data.name);
                        $('#npc-size-input').val(data.size.toLowerCase());
                        $('#npc-hp-input').val(data.hp);
                        $('#npc-ac-input').val(data.ac);
                        $('#add-npc-dialog').attr('data-selected',$(this).attr('data-creature'));
                        if (data.img) {
                            $('#npc-img-con img').attr('src', data.img);
                        } else {
                            cget('/static/', {}, false, function (static) {
                                if (static.includes('assets/tokens/' + data.slug + '.png')) {
                                    $('#npc-img-con img').attr('src', 'assets/tokens/' + data.slug + '.png');
                                } else {
                                    $('#npc-img-con img').attr('src', 'assets/logo_med.png');
                                }
                            });
                        }
                    });
                    if ($('#npc-table tbody').children('tr').length > 0) {
                        $('#no-content-icon').hide();
                    } else {
                        $('#no-content-icon').show();
                    }
                },
                { alert: true }
            );
        }
    });
    $('#npc-img-upload input').on('change', function (event) {
        var file = document.querySelector('#npc-img-upload input').files[0];
        var reader = new FileReader();
        reader.addEventListener("load", function () {
            console.log(reader.result);
            $('#npc-img-con img').attr('src', reader.result);
        }, false);
        if (file) {
            reader.readAsDataURL(file);
        }
    });
});