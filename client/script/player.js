var CAMPAIGN = null;
var MAP = null;
var CURSOR = 'default';
var OWNER = false;
var CMP_DATA = {};
var MAP_DATA = {};
var CMP_CHARS = {};
var CTX_TARGET = null;
var NPC_SCROLLS = {};

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
    '.entity, .entity .img-container, .entity img': {
        dm: [
            {
                conditions: {},
                items: ['remove-entity']
            }
        ],
        pc: []
    },
    '.character, .character .img-container, .character img': {
        dm: [
            {
                conditions: {},
                items: ['edit-character']
            },
            {
                conditions: {
                    parent_classes: {
                        'initiative': false
                    }
                },
                items: ['roll-initiative']
            },
            {
                conditions: {
                    parent_classes: {
                        'initiative': true
                    }
                },
                items: ['remove-initiative']
            }
            
        ],
        pc: [
            {
                conditions: {
                    system: {
                        owns_character: true
                    }
                },
                items: ['edit-character']
            },
            {
                conditions: {
                    parent_classes: {
                        'initiative': false
                    },
                    system: {
                        running_initiative: true,
                        owns_character: true
                    }
                },
                items: ['roll-initiative']
            },
            {
                conditions: {
                    parent_classes: {
                        'initiative': true
                    },
                    system: {
                        running_initiative: true,
                        owns_character: true
                    }
                },
                items: ['remove-initiative']
            }
        ]
    },
    '.npc, .npc .img-container, .npc img': {
        dm: [
            {
                conditions: {
                    parent_classes: {
                        'showing-stats': false
                    }
                },
                items: ['show-stats']
            },
            {
                conditions: {
                    parent_classes: {
                        'showing-stats': true
                    }
                },
                items: ['hide-stats']
            },
            {
                conditions: {
                    parent_classes: {
                        'initiative': false
                    }
                },
                items: ['roll-initiative']
            },
            {
                conditions: {
                    parent_classes: {
                        'initiative': true
                    }
                },
                items: ['remove-initiative']
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

function statIn(cur, path, notfit) {
    return $('<input class="stat-in" spellcheck="false">')
        .attr('data-path', path)
        .toggleClass('fit', !notfit)
        .val(cur.toString());
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

    $('#init-tools').toggle(owner && map.initiative.running);
    $('#start-initiative').toggle(!map.initiative.started);
    $('#stop-initiative').toggle(map.initiative.started);
    $('#proceed-initiative').toggle(map.initiative.started);

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
                .toggleClass('initiative',(map.initiative.running && Object.values(map.initiative.order).includes(eKeys[e])))
                .append(
                    $('<div class="img-container"></div>').append(
                        $('<img>').attr('src', img)
                    ).css({ 'border-radius': size / 2 + 'px' })
                )
                .append($('<div class="character-stats"></div>').text(cstat))
                .css(css)
                .appendTo(dummy_entities);
        } else if (ent.npc) {
            var data = ent.data;
            if (data.size.length > 0) {
                if (Object.keys(SIZES).includes((data.size.toLowerCase()))) {
                    var size = SIZES[data.size.toLowerCase()] * ($('#map').width() / (map.grid.size * map.grid.columns));
                } else {
                    var size = SIZES.medium * ($('#map').width() / (map.grid.size * map.grid.columns));
                    data.size = 'medium';
                }
            } else {
                var size = SIZES.medium * ($('#map').width() / (map.grid.size * map.grid.columns));
                data.size = 'medium';
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
                    ).css({ 'border-radius': size / 2 + 'px' })
                )
                .append($('<div class="npc-stats"></div>').text(npc_stats))
                .toggleClass('showing-stats', ent.displaying_statblock)
                .toggleClass('initiative',(map.initiative.running && Object.values(map.initiative.order).includes(eKeys[e])))
                .appendTo(dummy_entities);
        }
    }
    $('#entities').html(dummy_entities.html());

    if (MAP_DATA.initiative.started) {
        $('.entity[data-id='+MAP_DATA.initiative.order[MAP_DATA.initiative.current]+']').append($('<div class="init-notifier noselect">Initiative</div>'));
    }
    

    // Add event listeners
    $('.entity').off('click');
    $('.entity').on('click', function (event) {
        if (CURSOR != 'alias') { return; }
        mPost('/entity/remove/', { eid: $(event.delegateTarget).attr('data-id') }, function (data) { }, { alert: true });
    });

    if (OWNER) {
        if (MAP_DATA.initiative.running) {
            var dummy_init = $('<div></div>');
            var ikeys = Object.keys(MAP_DATA.initiative.order);
            ikeys.sort(function(a, b){return b-a});
            for (var i=0;i<ikeys.length;i++) {
                var el = $('<div class="init-item"></div>');
                el.attr({
                    'data-roll':ikeys[i],
                    'data-eid':MAP_DATA.initiative.order[ikeys[i]]
                });
                el.append(
                    $('<span class="init-roll"></span>').text(Math.round(ikeys[i]))
                );
                if (MAP_DATA.entities[MAP_DATA.initiative.order[ikeys[i]]].npc == true) {
                    el.append(
                        $('<span class="init-name"></span>').text(MAP_DATA.entities[MAP_DATA.initiative.order[ikeys[i]]].data.name)
                    );
                } else {
                    el.append(
                        $('<span class="init-name"></span>').text(chars[MAP_DATA.entities[MAP_DATA.initiative.order[ikeys[i]]].id].name)
                    );
                }
                if (MAP_DATA.initiative.current == ikeys[i]) {
                    el.addClass('cur');
                }
                dummy_init.append(el);
            }
            $('#init-list').html(dummy_init.html());
        }

        $('.npc.showing-stats').each(function (i, e) {
            var data = JSON.parse($(e).attr('data-npc'));
            var stats = $('<div class="npc-stats-main noselect"></div>');
            stats.append(
                $('<div class="title"></div>').append(statIn(data.name, 'name', true).css({width:'100%'}))
            );
            stats.append(
                $('<div class="sub"></div>').append([statIn(CapFirstLetter(data.size), 'size'), data.type, ', ', data.alignment])
            );
            stats.append($('<div class="horiz-sep"></div>'));
            stats.append(
                $('<div></div>').append($('<span></span>').css({ color: 'var(--dnd1)', 'font-weight': 'bold', 'font-family': 'raleway-heavy' }).text('Armor Class: '), statIn(data.ac, 'ac'))
            );
            stats.append(
                $('<div></div>').append($('<span></span>').css({ color: 'var(--dnd1)', 'font-weight': 'bold', 'font-family': 'raleway-heavy' }).text('Hit Points: '), statIn(data.hp, 'hp'), ' / ', statIn(data.max_hp, 'max_hp'))
            );
            stats.append($('<div class="horiz-sep"></div>'));
            stats.append(
                $('<table class="class-stats"><thead><tr><th>STR</th><th>DEX</th><th>CON</th><th>INT</th><th>WIS</th><th>CHA</th></tr></thead></table>')
                    .append(
                        $('<tbody></tbody>')
                            .append($('<tr></tr>')
                                .append(
                                    $('<td></td>')
                                        .text(data.abilities.strength.score + ' (' + cond(data.abilities.strength.modifier < 1, '', '+') + data.abilities.strength.modifier + ')')
                                )
                                .append(
                                    $('<td></td>')
                                        .text(data.abilities.dexterity.score + ' (' + cond(data.abilities.dexterity.modifier < 1, '', '+') + data.abilities.dexterity.modifier + ')')
                                )
                                .append(
                                    $('<td></td>')
                                        .text(data.abilities.constitution.score + ' (' + cond(data.abilities.constitution.modifier < 1, '', '+') + data.abilities.constitution.modifier + ')')
                                )
                                .append(
                                    $('<td></td>')
                                        .text(data.abilities.intelligence.score + ' (' + cond(data.abilities.intelligence.modifier < 1, '', '+') + data.abilities.intelligence.modifier + ')')
                                )
                                .append(
                                    $('<td></td>')
                                        .text(data.abilities.wisdom.score + ' (' + cond(data.abilities.wisdom.modifier < 1, '', '+') + data.abilities.wisdom.modifier + ')')
                                )
                                .append(
                                    $('<td></td>')
                                        .text(data.abilities.charisma.score + ' (' + cond(data.abilities.charisma.modifier < 1, '', '+') + data.abilities.charisma.modifier + ')')
                                )
                            )
                    )
            )
            stats.append($('<div class="horiz-sep"></div>'));
            var savesEl = $('<span></span>');
            var abs = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'];
            for (var k = 0; k < abs.length; k++) {
                if (data.abilities[abs[k]].save >= data.abilities[abs[k]].modifier + data.proficiency_bonus || data.abilities[abs[k]].save < data.abilities[abs[k]].modifier) {
                    $(savesEl).append(CapFirstLetter(abs[k]).slice(0, 3) + ' ' + cond(data.abilities[abs[k]].save < 1, '', '+') + data.abilities[abs[k]].save + ', ');
                }
            }
            stats.append(
                $('<div></div>')
                    .append($('<span></span>').css({ color: 'var(--dnd1)', 'font-weight': 'bold', 'font-family': 'raleway-heavy' }).text('Saving Throws: '))
                    .append(savesEl)
            );
            var skillsEl = $('<span></span>');
            var sks = Object.keys(data.skills);
            for (var k = 0; k < sks.length; k++) {
                if (data.skills[sks[k]] >= data.abilities[SKILLS[sks[k]]].modifier + data.proficiency_bonus || data.skills[sks[k]] < data.abilities[SKILLS[sks[k]]].modifier) {
                    $(skillsEl).append(CapFirstLetter(sks[k]) + ' ' + cond(data.skills[sks[k]] < 1, '', '+') + data.skills[sks[k]] + ', ');
                }
            }
            stats.append(
                $('<div></div>')
                    .append($('<span></span>').css({ color: 'var(--dnd1)', 'font-weight': 'bold', 'font-family': 'raleway-heavy' }).text('Skills: '))
                    .append(skillsEl)
            );
            if (Object.keys(data.immune).length > 0) {
                stats.append(
                    $('<div></div>')
                        .append($('<span></span>').css({ color: 'var(--dnd1)', 'font-weight': 'bold', 'font-family': 'raleway-heavy' }).text('Damage Immunities: '))
                        .append(Object.keys(data.immune).map(function (v) {
                            return data.immune[v].damage_condition.join(' ') + ' ' + v;
                        }).join(', '))
                );
            }
            if (Object.keys(data.resist).length > 0) {
                stats.append(
                    $('<div></div>')
                        .append($('<span></span>').css({ color: 'var(--dnd1)', 'font-weight': 'bold', 'font-family': 'raleway-heavy' }).text('Damage Resistances: '))
                        .append(Object.keys(data.resist).map(function (v) {
                            return data.resist[v].damage_condition.join(' ') + ' ' + v;
                        }).join(', '))
                );
            }
            if (Object.keys(data.vuln).length > 0) {
                stats.append(
                    $('<div></div>')
                        .append($('<span></span>').css({ color: 'var(--dnd1)', 'font-weight': 'bold', 'font-family': 'raleway-heavy' }).text('Damage Vulnerabilities: '))
                        .append(Object.keys(data.vuln).map(function (v) {
                            return data.vuln[v].damage_condition.join(' ') + ' ' + v;
                        }).join(', '))
                );
            }
            if (Object.keys(data.condition_immunities).length > 0) {
                stats.append(
                    $('<div></div>')
                        .append($('<span></span>').css({ color: 'var(--dnd1)', 'font-weight': 'bold', 'font-family': 'raleway-heavy' }).text('Condition Immunities: '))
                        .append(data.condition_immunities.join(', '))
                );
            }
            stats.append(
                $('<div></div>')
                    .append($('<span></span>').css({ color: 'var(--dnd1)', 'font-weight': 'bold', 'font-family': 'raleway-heavy' }).text('Challenge: '))
                    .append(data.challenge_display)
            );
            stats.append($('<div class="horiz-sep"></div>'));

            for (var a = 0; a < data.special_abilities.length; a++) {
                if (data.special_abilities[a].name.toLowerCase().includes('spellcasting')) {
                    continue;
                }
                if (Object.keys(data.special_abilities[a]).includes('description')) {
                    data.special_abilities[a].desc = data.special_abilities[a].description;
                }
                $('<div></div>')
                    .append($('<span></span>').css({ color: 'var(--dnd1)', 'font-weight': 'bold', 'font-family': 'raleway-heavy', 'font-style': 'italic' }).text(data.special_abilities[a].name + '. '))
                    .append($('<span></span>').html(data.special_abilities[a].desc.replace(/\n/g, '<br>')))
                    .appendTo(stats);
            }
            if (Object.keys(data.spellcasting).length > 0) {
                var sk = Object.keys(data.spellcasting);
                for (var k = 0; k < sk.length; k++) {
                    var spi = data.spellcasting[sk[k]];
                    if (spi.automated) {
                        var auto = 'Automated. Components: ' + spi.components.join(', ') + '. Attack bonus: +' + spi.bonus + ', Save DC: ' + spi.dc + '. Ability: ' + CapFirstLetter(spi.ability) + '.';
                        var _spells = {};
                        var desc = '';
                        if (spi.type == 'innate') {
                            for (var s = 0; s < spi.spells.length; s++) {
                                if (Object.keys(_spells).includes(spi.spells[s].per_day)) {
                                    _spells[spi.spells[s].per_day].push(spi.spells[s].spell);
                                } else {
                                    _spells[spi.spells[s].per_day] = [spi.spells[s].spell];
                                }
                            }
                            var spells = $('<div></div>');
                            for (var l = 0; l < Object.keys(_spells).length; l++) {
                                $(spells).append(
                                    $('<div></div>').html('<strong>' + Object.keys(_spells)[l] + ': </strong><em>' + _spells[Object.keys(_spells)[l]].join(', ') + '.</em><br>')
                                );
                            }
                        } else {
                            for (var s = 0; s < spi.spells.length; s++) {
                                if (Object.keys(_spells).includes(spi.spells[s].level.toString())) {
                                    _spells[spi.spells[s].level].push({ spell: spi.spells[s].spell, slots: spi.spells[s].slots });
                                } else {
                                    _spells[spi.spells[s].level] = [{ spell: spi.spells[s].spell, slots: spi.spells[s].slots }];
                                }
                            }
                            var spells = $('<div></div>');
                            if (Object.keys(_spells).includes('Cantrip')) {
                                _spells['Cantrips'] = _spells['Cantrip'];
                            }
                            $(spells).append(
                                $('<div></div>').html('<strong>Cantrips</strong> (At Will): ' + _spells['Cantrips'].map(function (a) { return a.spell; }).join(', '), '.<br>')
                            );
                            for (var l = 0; l < Object.keys(_spells).length; l++) {
                                if (Object.keys(_spells)[l].toLowerCase() == 'cantrips' || Object.keys(_spells)[l].toLowerCase() == 'cantrip') {
                                    continue;
                                } else {
                                    $(spells).append(
                                        $('<div></div>').append('<strong>Level ' + Object.keys(_spells)[l] + '</strong>', ' (', statIn(spi.slots[Number(Object.keys(_spells)[l])], 'spellcasting.' + sk[k] + '.slots.' + Object.keys(_spells)[l]), '/', _spells[Object.keys(_spells)[l]][0].slots, '): ', _spells[Object.keys(_spells)[l]].map(function (a) { return a.spell; }).join(', '), '.<br>')
                                    );
                                }
                            }
                        }
                    } else {
                        var auto = 'Not Automated.';
                        var spells = '<br>';
                        var desc = '<br>' + spi.desc.replace(/\n/g, '<br>');
                    }
                    var sel = $('<div></div>')
                        .append($('<span></span>').css({ color: 'var(--dnd1)', 'font-weight': 'bold', 'font-family': 'raleway-heavy', 'font-style': 'italic' }).html(sk[k] + '.<br>'))
                        .append($('<span class="sub"></span>').html(auto))
                        .append(spells)
                        .append($('<div></div>').html(desc));


                    stats.append(sel);
                }
            }
            stats.append('<br>');
            stats.append($('<div class="title">Actions</div>').css({ 'font-size': '2.5vh' }))
            stats.append($('<div class="horiz-sep"></div>'));
            for (var a = 0; a < data.actions.length; a++) {
                if (Object.keys(data.actions[a]).includes('description')) {
                    data.actions[a].desc = data.actions[a].description;
                }
                $('<div></div>')
                    .append($('<span></span>').css({ color: 'var(--dnd1)', 'font-weight': 'bold', 'font-family': 'raleway-heavy', 'font-style': 'italic' }).text(data.actions[a].name + '. '))
                    .append($('<span></span>').html(data.actions[a].desc.replace(/\n/g, '<br>')))
                    .appendTo(stats);
            }

            if (data.legendary_actions.length > 0) {
                stats.append('<br>');
                stats.append($('<div class="title">Legendary Actions</div>').css({ 'font-size': '2.5vh' }))
                stats.append($('<div class="horiz-sep"></div>'));
                for (var a = 0; a < data.legendary_actions.length; a++) {
                    if (Object.keys(data.legendary_actions[a]).includes('description')) {
                        data.legendary_actions[a].desc = data.legendary_actions[a].description;
                    }
                    $('<div></div>')
                        .append($('<span></span>').css({ color: 'var(--dnd1)', 'font-weight': 'bold', 'font-family': 'raleway-heavy', 'font-style': 'italic' }).text(data.legendary_actions[a].name + '. '))
                        .append($('<span></span>').html(data.legendary_actions[a].desc.replace(/\n/g, '<br>')))
                        .appendTo(stats);
                }
            }

            stats.appendTo($(e));
            if (Object.keys(NPC_SCROLLS).includes($(e).attr('data-id'))) {
                $($(e).children('.npc-stats-main')[0]).scrollTop(NPC_SCROLLS[$(e).attr('data-id')]);
            }
        });
        $('.npc.showing-stats .stat-in.fit').on('input', function (event) {
            $(event.target).css('width', ($(event.target).val().length + 1) + 'ch');
        }).each(function (index, elem) {
            $(elem).css('width', ($(elem).val().length + 1) + 'ch');
        });
        $('.npc.showing-stats .stat-in').on('change',function(event){
            var val = $(event.target).val();
            if (!isNaN(Number(val))) {
                val = Number(val);
            }
            mPost('/entity/modify/',{
                entity: $($(event.target).parents('.npc')[0]).attr('data-id'),
                batch:[
                    {path:'data.'+$(event.target).attr('data-path'),value:val}
                ]
            },function(data){},{alert:true});
        });
    }
    $('.npc.showing-stats .npc-stats-main').on('scroll', function (event) {
        var nid = $($(event.target).parents('.npc')[0]).attr('data-id');
        NPC_SCROLLS[nid] = $(event.target).scrollTop();
    });

    var converter = new showdown.Converter({tables: true, strikethrough: true});
    var dummy_chat = $('<div></div>')
    for (var c=0;c<map.chat.length;c++) {
        if (OWNER || map.chat[c].uid == uid) {
            var delete_btn = $('<button class="chat-delete"></button>')
            .append($('<img>').attr('src','assets/icons/delete.png'));
        } else {
            var delete_btn = '';
        }

        $('<div class="chat"></div>')
        .attr({
            'data-id':map.chat[c].iid,
            'data-owner':map.chat[c].uid
        })
        .append($('<div class="chat-meta noselect"></div>').text(map.chat[c].author + ' - ' + map.chat[c].time))
        .append($('<div class="chat-content"></div>').html(converter.makeHtml(map.chat[c].content)))
        .append(delete_btn)
        .appendTo(dummy_chat);
    }
    $('#chat-area').html(dummy_chat.html());
    $('#chat-area .chat-delete').on('click',function(e){
        mPost('/chat/delete/',{iid:$($(e.target).parents('.chat')[0]).attr('data-id')},function(data){},{alert:true});
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
    $('#init-tools').hide();
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
        if ($(e.target).parents('.npc-stats-main').length > 0 || $(e.target).is('.npc-stats-main')) { return; }
        e.preventDefault();
        var ret = false;
        if ($(e.target).hasClass('entity') && !$(e.target).hasClass('obscure') && $(e.target).parents('.npc-stats-main').length == 0 && !$(e.target).is('.npc-stats-main') && !$(e.target).is('.init-notifier')) {
            $(e.target).toggleClass('moving', true);
            ret = true;
        }
        if ($(e.target).parents('.entity').length > 0 && !$(e.target).hasClass('obscure') && $(e.target).parents('.npc-stats-main').length == 0 && !$(e.target).is('.npc-stats-main') && !$(e.target).is('.init-notifier')) {
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
        if ($(e.target).parents('.npc-stats-main').length > 0 || $(e.target).is('.npc-stats-main')) { return; }
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
        var ctxs = [];
        for (var s = 0; s < Object.keys(CONTEXT).length; s++) {
            if ($(event.target).is(Object.keys(CONTEXT)[s])) {
                ctxs.push(Object.keys(CONTEXT)[s]);
            }
        }
        if ($(event.target).attr('id') == 'context-menu' || $(event.target).parents('#context-menu').length > 0) {
            event.preventDefault();
            return;
        }
        if (ctxs.length == 0) { return; }
        event.preventDefault();
        $('#context-menu button').hide();
        for (var n = 0; n < ctxs.length; n++) {
            var ctx = ctxs[n];
            var potential = CONTEXT[ctx][cond(OWNER, 'dm', 'pc')];
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
                        if (ks[i] == 'owns_character' && proceed) {
                            if ($(event.target).is('[data-char]')) {
                                var _el = event.target;
                            } else {
                                var _el = $(event.target).parents('[data-char]')[0];
                            }
                            var char = CMP_CHARS[$(_el).attr('data-char')];
                            proceed = (char.owner == uid) == c.system[ks[i]];
                        }
                        if (ks[i] == 'running_initiative' && proceed) {
                            proceed = MAP_DATA.initiative.running == c.system[ks[i]];
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
                if (c.parent_classes) {
                    var ks = Object.keys(c.parent_classes)
                    for (var i = 0; i < ks.length; i++) {
                        if (($(event.target).parents('.' + ks[i]).length == 0) == c.parent_classes[ks[i]]) {
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
    $('#ctx_remove-entity').on('click', function (event) {
        var el = getctx();
        console.log(el.el);
        if (!$(el.el).hasClass('entity')) {
            el.el = $(el.el).parents('.entity')[0];
        }
        mPost('/entity/remove/', { eid: $(el.el).attr('data-id') }, function (data) { }, { alert: true });
    });
    $('#ctx_add-player').on('click', function (event) {
        var el = getctx();
        mPost('/entity/add/player/', { charid: getCID(), x: el.x, y: el.y }, function (data) { }, { alert: true });
    });
    $('#ctx_edit-character').on('click', function (event) {
        var el = getctx();
        if ($(el.el).is('[data-char]')) {
            window.open(window.location.origin + '/characters?char=' + $(el.el).attr('data-char'), '_blank');
        } else {
            window.open(window.location.origin + '/characters?char=' + $($(el.el).parents('[data-char]')[0]).attr('data-char'), '_blank');
        }
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
        $('#npc-cancel-btn').on('click', function (event) {
            $('#npc-img-con img').attr('src', 'assets/logo_med.png');
            $('#add-npc-dialog input').val('');
            $('#add-npc-dialog select').val('medium');
            $('#add-npc-dialog tbody').html('');
            $('#add-npc-dialog').toggleClass('active', false);
            $('#noclosemodal').toggleClass('active', false);
        });
        $('#npc-buttons button:first-child').on('click', function (event) {
            console.log('click');
            var data = JSON.parse($('#add-npc-dialog').attr('data-selected'));
            data.hp = Number($('#npc-hp-input').val());
            data.max_hp = Number($('#npc-hp-input').val())
            data.ac = Number($('#npc-ac-input').val());
            data.name = $('#npc-name-input').val();
            data.size = $('#npc-size-input').val();
            data.img = $('#npc-img-con img').attr('src');
            mPost('/entity/add/npc/', {
                x: Number($('#add-npc-dialog').attr('data-x')),
                y: Number($('#add-npc-dialog').attr('data-y')),
                data: data,
            }, function (data) { console.log(data); }, { alert: true });
            $('#npc-img-con img').attr('src', 'assets/logo_med.png');
            $('#add-npc-dialog input').val('');
            $('#add-npc-dialog select').val('medium');
            $('#add-npc-dialog tbody').html('');
            $('#add-npc-dialog').toggleClass('active', false);
            $('#noclosemodal').toggleClass('active', false);
        });
    });

    $('#ctx_show-stats').on('click', function (event) {
        var el = getctx();
        if ($(el.el).is('.npc')) {
            mPost('/entity/modify/', {
                entity: $(el.el).attr('data-id'),
                batch: [
                    { path: 'displaying_statblock', value: true }
                ]
            }, function (data) { }, { alert: true });
        } else {
            mPost('/entity/modify/', {
                entity: $($(el.el).parents('.npc')[0]).attr('data-id'),
                batch: [
                    { path: 'displaying_statblock', value: true }
                ]
            }, function (data) { }, { alert: true });
        }
    });
    $('#ctx_hide-stats').on('click', function (event) {
        var el = getctx();
        if ($(el.el).is('.npc')) {
            mPost('/entity/modify/', {
                entity: $(el.el).attr('data-id'),
                batch: [
                    { path: 'displaying_statblock', value: false }
                ]
            }, function (data) { }, { alert: true });
        } else {
            mPost('/entity/modify/', {
                entity: $($(el.el).parents('.npc')[0]).attr('data-id'),
                batch: [
                    { path: 'displaying_statblock', value: false }
                ]
            }, function (data) { }, { alert: true });
        }
    });

    $('#ctx_roll-initiative').on('click',function(event){
        var el = getctx();
        if ($(el.el).is('.entity')) {
            mPost('/initiative/add/', {
                eid: $(el.el).attr('data-id')
            }, function (data) { }, { alert: true });
        } else {
            mPost('/initiative/add/', {
                eid: $($(el.el).parents('.entity')[0]).attr('data-id')
            }, function (data) { }, { alert: true });
        }
    });
    $('#ctx_remove-initiative').on('click',function(event){
        var el = getctx();
        if ($(el.el).is('.entity')) {
            mPost('/initiative/remove/', {
                eid: $(el.el).attr('data-id')
            }, function (data) { }, { alert: true });
        } else {
            mPost('/initiative/remove/', {
                eid: $($(el.el).parents('.entity')[0]).attr('data-id')
            }, function (data) { }, { alert: true });
        }
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
                        $('#add-npc-dialog').attr('data-selected', $(this).attr('data-creature'));
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

    $('#send-btn').on('click',function(event){
        mPost('/chat/',{value:$('#chat-input textarea').val()},function(data){$('#chat-input textarea').val('');},{alert:true});
    });

    // Init tools
    $('#expand-initiative').on('click',function(data){$('#init-tools').toggleClass('active')});
    $('#start-initiative').on('click',function(data){
        mPost('/initiative/start/',{},function(data){},{alert:true});
    });
    $('#stop-initiative').on('click',function(data){
        bootbox.confirm('Are you sure you want to end initiative?',function(res){
            if (res) {
                mPost('/initiative/stop/',{},function(data){},{alert:true});
            }
        });
    });
    $('#proceed-initiative').on('click',function(data){
        mPost('/initiative/next/',{},function(data){},{alert:true});
    });
});