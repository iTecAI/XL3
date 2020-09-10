function getmod(score) {
    var modref = {
        '1':'-5',
        '2-3':'-4',
        '4-5':'-3',
        '6-7':'-2',
        '8-9':'-1',
        '10-11':'0',
        '12-13':'+1',
        '14-15':'+2',
        '16-17':'+3',
        '18-19':'+4',
        '20-21':'+5',
        '22-23':'+6',
        '24-25':'+7',
        '26-27':'+8',
        '28-29':'+9',
        '30':'+10'
    }

    for (var k=0;k<Object.keys(modref).length;k++) {
        if (Object.keys(modref)[k].split('-').includes(score.toString())) {
            return modref[Object.keys(modref)[k]];
        }
    }
    return null;
}

function assembleMagicItems(data){
    $('.comp-cont-loading').hide();
    var converter = new showdown.Converter({tables: true, strikethrough: true});
    for (var i=0;i<data.length;i++) {
        if (data[i].requires_attunement != '') {
            var attunement = ' ('+data[i].requires_attunement+')';
        } else {
            var attunement = '';
        }
        $('<div class="magic-item-display"></div>')
        .attr('id','item_'+data[i].slug)
        .attr('data-slug',data[i].slug)
        .append(
            $('<h3></h3>')
            .css({
                color: 'var(--dnd1)',
                'font-family':'raleway-heavy'
            })
            .text(data[i].name)
            .addClass('noselect')
        ).append(
            $('<span></span>')
            .css({
                'font-family':'raleway-regular',
                'font-style':'italic',
                color:'var(--foreground2-2)'
            })
            .text(data[i].type+', '+data[i].rarity+attunement)
            .addClass('noselect')
        ).append(
            $('<div></div>')
            .css('font-family','raleway-regular')
            .html(converter.makeHtml(data[i].desc))
        ).appendTo($('#comp-content-box .compendium-subcontent'));
    }
}

function assembleSpells(data) {
    $('.comp-cont-loading').hide();
    var converter = new showdown.Converter({tables: true, strikethrough: true});
    for (var i=0;i<data.length;i++) {
        var item = data[i]
        if (item.material != '') {var material = ' ('+item.material+')';} else {var material = ''}
        if (item.ritual != 'no') {var ritual = ' (ritual)';} else {var ritual = ''}
        if (item.concentration != 'no') {var concentration = 'Concentration, ';} else {var concentration = ''}
        if (item.higher_level != '') {var higher_level = '<br>**At Higher Levels.**'+item.higher_level;} else {var higher_level = ''}
        if (item.level == 'Cantrip') {var level = '<em>'+item.school+' cantrip</em>';} else {var level = '<em>'+item.level+' '+item.school.toLowerCase()+'</em>'}

        $('<div class="spell-display"></div>')
        .attr('id','spell_'+item.slug)
        .attr('data-slug',item.slug)
        .append(
            $('<h3></h3>')
            .css({
                color: 'var(--dnd1)',
                'font-family':'raleway-heavy'
            })
            .text(item.name)
            .addClass('noselect')
        ).append(
            $('<span></span>')
            .css({
                'font-family':'raleway-regular',
                'font-style':'italic',
                color:'var(--foreground2-2)'
            })
            .html(level+ritual)
            .addClass('noselect')
        )
        .append($('<br><span><strong>Casting Time:</strong> '+item.casting_time+'</span>'))
        .append($('<br><span><strong>Range:</strong> '+item.range+'</span>'))
        .append($('<br><span><strong>Components:</strong> '+item.components+material+'</span>'))
        .append($('<br><span><strong>Duration:</strong> '+concentration+item.duration+'</span>'))
        .append($('<br><br>'+converter.makeHtml(item.desc+higher_level)))
        .appendTo($('#comp-content-box .compendium-subcontent'));
    }
}

function assembleMonsters(data) {
    $('.comp-cont-loading').hide();
    var converter = new showdown.Converter({tables: true, strikethrough: true});
    for (var r=0;r<data.length;r++) {
        var item = data[r];

        var speed = '';
        for (var i=0;i<Object.keys(item.speed).length;i++) {
            speed += Object.keys(item.speed)[i]+' '+item.speed[Object.keys(item.speed)[i]]+' ft. ';
        }

        var saves = [];
        var abilities = ['strength','dexterity','constitution','intelligence','wisdom','charisma'];
        for (var i=0;i<abilities.length;i++) {
            if (item[abilities[i]+'_save'] == null) {
                saves.push(abilities[i].slice(0,3).toUpperCase()+' '+getmod(item[abilities[i]]));
            } else {
                if (item[abilities[i]+'_save'] > 0) {
                    saves.push(abilities[i].slice(0,3).toUpperCase()+' +'+item[abilities[i]+'_save']);
                } else {
                    saves.push(abilities[i].slice(0,3).toUpperCase()+' '+item[abilities[i]+'_save']);
                }
            }
        }
        saves = saves.join(', ');

        var skills = [];
        for (var i=0;i<Object.keys(item.skills).length;i++) {
            if (item.skills[Object.keys(item.skills)[i]] > 0) {
                skills.push(Object.keys(item.skills)[i]+' +'+item.skills[Object.keys(item.skills)[i]]);
            } else {
                skills.push(Object.keys(item.skills)[i]+' '+item.skills[Object.keys(item.skills)[i]]);
            }
        } 
        skills = skills.join(', ');

        var spec_abilities = [];
        for (var i=0;i<item.special_abilities.length;i++) {
            spec_abilities.push('<p><strong>'+item.special_abilities[i].name+'.</strong> '+item.special_abilities[i].desc+'</p>');
        }
        spec_abilities = spec_abilities.join('');

        var actions = [];
        for (var i=0;i<item.actions.length;i++) {
            actions.push('<p><strong>'+item.actions[i].name+'.</strong> '+item.actions[i].desc+'</p>');
        }
        actions = actions.join('');

        if (item.legendary_actions == '') {
            var legendary_actions = $('');
        } else {
            var lactions = [];
            for (var i=0;i<item.legendary_actions.length;i++) {
                lactions.push('<p><strong>'+item.legendary_actions[i].name+'.</strong> '+item.legendary_actions[i].desc+'</p>');
            }
            lactions = lactions.join('');
            var legendary_actions = $('<h3>Legendary Actions</h3><div class="horiz-sep"></div>'+lactions);
        }

        if (item.reactions == '') {
            var reactions = $('');
        } else {
            var reactions = [];
            for (var i=0;i<item.reactions.length;i++) {
                reactions.push('<p><strong>'+item.reactions[i].name+'.</strong> '+item.reactions[i].desc+'</p>');
            }
            reactions = reactions.join('');
            var reactions = $('<h3>Reactions</h3><div class="horiz-sep"></div>'+reactions);
        }

        if (r == 0) {
            var itable = '<table class="monster-basic-info"><tr><th>Name</th><th>Type</th><th>CR</th><th>Size</th><th>HP</th></tr></table>';
        } else {
            var itable = '<table class="monster-basic-info"></table>';
        }

        $('<div class="monster-display"></div>')
        .attr('id','monster_'+item.slug)
        .attr('data-slug',item.slug)
        .append(
            $(itable)
            .append(
                $('<tr></tr>')
                .append(
                    $('<td></td>').text(item.name).css('font-family','raleway-heavy')
                ).append(
                    $('<td></td>').text(item.type)
                ).append(
                    $('<td></td>').text(item.challenge_rating)
                ).append(
                    $('<td></td>').text(item.size)
                ).append(
                    $('<td></td>').text(item.hit_points)
                )
            )
            .attr('data-slug',item.slug)
            .click(function(event){
                $('#expanded_'+$(event.delegateTarget).attr('data-slug')).slideToggle(1);
            })
        )
        .append(
            $('<div class="monster-expanded"></div>')
            .attr('id','expanded_'+item.slug)
            .append(
                $('<h1></h1>').text(item.name)
                .css({'color':'var(--dnd1)','font-family':'raleway-heavy'})
            )
            .append(
                $('<span></span>')
                .css({'font-family':'raleway-regular','font-style':'italic'})
                .text(item.size+' '+item.type+', '+item.alignment)
            )
            .append($('<div class="horiz-sep"></div>'))
            .append($('<strong>Armor Class</strong> '+item.armor_class+'<br>'))
            .append($('<strong>Hit Points</strong> '+item.hit_points+' ('+item.hit_dice+')<br>'))
            .append($('<strong>Speed</strong> '+speed+'<br>'))
            .append($('<div class="horiz-sep"></div>'))
            .append(
                $('<table class="class-stats"><thead><tr><th>STR</th><th>DEX</th><th>CON</th><th>INT</th><th>WIS</th><th>CHA</th></tr></thead></table>')
                .append(
                    $('<tbody><tr></tr></tbody>')
                    .append(
                        $('<td></td>')
                        .append(item.strength+' ('+getmod(item.strength)+')')
                    ).append(
                        $('<td></td>')
                        .append(item.dexterity+' ('+getmod(item.dexterity)+')')
                    ).append(
                        $('<td></td>')
                        .append(item.constitution+' ('+getmod(item.constitution)+')')
                    ).append(
                        $('<td></td>')
                        .append(item.intelligence+' ('+getmod(item.intelligence)+')')
                    ).append(
                        $('<td></td>')
                        .append(item.wisdom+' ('+getmod(item.wisdom)+')')
                    ).append(
                        $('<td></td>')
                        .append(item.charisma+' ('+getmod(item.charisma)+')')
                    )
                )
            )
            .append($('<div class="horiz-sep"></div>'))
            .append($('<strong>Saving Throws</strong> '+saves+'<br>'))
            .append($('<strong>Skills</strong> '+skills+'<br>'))
            .append($('<strong>Senses</strong> '+item.senses+'<br>'))
            .append($('<strong>Languages</strong> '+item.languages+'<br>'))
            .append($('<strong>Challenge</strong> '+item.challenge_rating+'<br>'))
            .append($('<div class="horiz-sep"></div>'))
            .append($('<div class="special-abilities"></div>').html(spec_abilities))
            .append($('<h3>Actions</h3>'))
            .append($('<div class="horiz-sep"></div>'))
            .append($('<div class="actions"></div>').html(actions))
            .append(reactions)
            .append(legendary_actions)
            .slideUp(0)
        )
        .appendTo($('#comp-content-box .compendium-subcontent'));
    }
}

$(document).ready(function(){
    $('.comp-cont-loading').hide();
    $('.ep-section-content > button').click(function(event){
        cget(
            '/compendium/section/'+$(event.target).attr('data-endpoint')+'/',
            {},true,
            function(data){
                $('#comp-content-box').html(data.content);
                $('#comp-title-box span').text($(event.target).text());
            }
        );
    });

    $('#magic-items-side').click(function(){
        $('#comp-title-box span').text('Magic Items');
        $('#comp-content-box').html('');
        $('#comp-content-box .compendium-subcontent').html('');
        $('.comp-cont-loading').show();
        $('#comp-content-box').append($(
            '<input id="search-magic-items" placeholder="Search" class="comp-search">'
        ).change(function(event){
            $('.comp-cont-loading').show();
            $('#comp-content-box .compendium-subcontent').html('');
            cget(
                '/compendium/search/magicitems/?search='+$(event.target).val(),
                {},false,
                assembleMagicItems
            );
        }));
        $('#comp-content-box').append($(
            '<div class="compendium-subcontent"></div>'
        ));
        cget(
            '/compendium/search/magicitems/',
            {},false,
            assembleMagicItems
        );
    });
    $('#spells-side').click(function(){
        $('#comp-title-box span').text('Spells');
        $('#comp-content-box').html('');
        $('.comp-cont-loading').show();
        $('#comp-content-box').append($(
            '<input id="search-spells" placeholder="Search" class="comp-search">'
        ).change(function(event){
            $('.comp-cont-loading').show();
            $('#comp-content-box .compendium-subcontent').html('');
            cget(
                '/compendium/search/spells/?search='+$(event.target).val(),
                {},false,
                assembleSpells
            );
        }));
        $('#comp-content-box').append($(
            '<div class="compendium-subcontent"></div>'
        ));
        cget(
            '/compendium/search/spells/',
            {},false,
            assembleSpells
        );
    });
    $('#monsters-side').click(function(){
        $('#comp-title-box span').text('Monsters');
        $('#comp-content-box').html('');
        $('.comp-cont-loading').show();
        $('#comp-content-box').append($(
            '<input id="search-monsters" placeholder="Search" class="comp-search">'
        ).change(function(event){
            $('.comp-cont-loading').show();
            $('#comp-content-box .compendium-subcontent').html('');
            cget(
                '/compendium/search/monsters/?limit=300&search='+$(event.target).val(),
                {},false,
                assembleMonsters
            );
        }));
        $('#comp-content-box').append($(
            '<div class="compendium-subcontent"></div>'
        ));
        cget(
            '/compendium/search/monsters/?limit=300',
            {},false,
            assembleMonsters
        );
    });
});