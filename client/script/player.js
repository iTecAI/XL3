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
    '#entities':{
        dm:[
            {
                conditions:{},
                items:['add-npc']
            },
            {
                conditions:{
                    system:{
                        has_character:true,
                        placed_character:false
                    }
                },
                items:['add-player']
            }
        ],
        pc:[
            {
                conditions:{
                    system:{
                        has_character:true,
                        placed_character:false
                    }
                },
                items:['add-player']
            }
        ]
    },
    '.obscure':{
        dm:[
            {
                conditions:{},
                items:['remove-obscure']
            }
        ],
        pc:[]
    }
}

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

function onPlayerRefresh(map, cmp, chars, owner) {
    console.log(map, cmp, chars, owner);
    CMP_DATA = cmp;
    MAP_DATA = map;
    CMP_CHARS = chars;
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
        if (ent.type = 'obscure') {
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
        if ($(e.target).hasClass('entity') && !$(e.target).hasClass('obscure')) { return; }
        e.preventDefault();
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
    });

    $('#map').on('mousemove', function (e) {
        if (!panning || CURSOR != 'move') {
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
    $(document).on('contextmenu',function(event){
        var ctx = null;
        for (var s=0;s<Object.keys(CONTEXT).length;s++) {
            if ($(event.target).is(Object.keys(CONTEXT)[s])) {
                ctx = Object.keys(CONTEXT)[s];
                break;
            }
        }
        if ($(event.target).attr('id')=='context-menu' || $(event.target).parents('#context-menu').length > 0) {
            event.preventDefault();
            return;
        }
        if (!ctx) { return; }
        event.preventDefault();
        var potential = CONTEXT[ctx][cond(OWNER,'dm','pc')];
        $('#context-menu button').hide();
        var ct = 0;
        for (var p=0;p<potential.length;p++) {
            var c = potential[p].conditions;
            var proceed = true;
            if (c.system) {
                var ks = Object.keys(c.system)
                for (var i=0;i<ks.length;i++) {
                    if (ks[i] == 'has_character' && proceed) {
                        var found = false;
                        for (var ch=0;ch<CMP_DATA.characters.length;ch++) {
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
                        for (var ch=0;ch<CMP_DATA.characters.length;ch++) {
                            if (CMP_CHARS[CMP_DATA.characters[ch]].owner == uid) {
                                found = true;
                                id = CMP_DATA.characters[ch];
                                break;
                            }
                        }
                        if (!found) {
                            proceed = !c.system[ks[i]]
                        } else {
                            proceed = ($('.entity.character[data-id='+id+']').length > 0) == c.system[ks[i]];
                        }
                    }
                }
            }
            if (c.classes) {
                var ks = Object.keys(c.classes)
                for (var i=0;i<ks.length;i++) {
                    if ($(event.target).hasClass(ks[i]) != c.classes[ks[i]]) {
                        proceed = false;
                    }
                }
            }
            
            if (proceed) {
                for (var i=0;i<potential[p].items.length;i++) {
                    $('#ctx_'+potential[p].items[i]).show();
                    ct++;
                }
            }
        }
        if (ct > 0) {
            CTX_TARGET = event.target;
            $('#context-menu').css({
                top:event.pageY+5+'px',
                left:event.pageX+5+'px'
            }).show();
        }
    });
    $(document).on('click',function(event){
        if ($(event.target).attr('id')=='context-menu' || $(event.target).parents('#context-menu').length > 0) {
            return;
        }
        CTX_TARGET = null;
        $('#context-menu').hide();
    });

    // Context Menu Items
    $('#ctx_remove-obscure').on('click',function(event){
        var el = getctx();
        mPost('/entity/remove/', { eid: $(el).attr('data-id') }, function (data) { }, { alert: true });
    })
});