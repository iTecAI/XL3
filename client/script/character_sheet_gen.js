var dat = {};

function modify(path,val) {
    cpost(
        '/characters/'+fingerprint+'/'+$('#character-sheet-display').attr('data-id')+'/modify/',
        {
            'path':path,
            'data':val
        },
        function(data){
            sheet_gen(data);
        },
        {
            alert: true
        }
    );
}

function charHasClass(_dat,_cls,lvl,sub) {
    for (var c=0;c<_dat.classes.length;c++) {
        if (dat.classes[c].class == _cls && (dat.classes[c].subclass == sub || sub == undefined) && (dat.classes[c].level == lvl || lvl == undefined)) {
            return true;
        }
    }
    return false;
}

function modformat(num) {
    if (num > 0) {
        return '+'+num;
    } else {
        return num.toString();
    }
}

function cond(c,t,f) {
    if (c) {return t;} else {return f;}
}

function sheet_gen(char) {
    $('#character-sheet-display').attr('data-id',char.cid);
    dat = char.data;
    $('#header-img img').attr('src',function(){
        if (dat.image == '') {
            return 'assets/logo.png';
        } else {
            return dat.image;
        }
    });
    $('#character-sheet-display input')
    .attr('autocomplete','off')
    .attr('autocorrect','off')
    .attr('autocapitalize','off')
    .attr('spellcheck','false');
    $('#char-name').val(dat.name);
    $('#char-race').val(dat.race);
    $('#char-class').val(dat.class_display);
    $('#char-level').val(dat.level);
    $('#char-xp').val(dat.xp);
    $('#ab-proficiency .ab-modifier').text(modformat(dat.proficiency_bonus));
    $('#perc-passive-val').text(dat.passive_perception);
    $('#char-init span').text(modformat(dat.init+dat.init_mod));
    $('#char-ac span').text(dat.ac.base + dat.ac.mod);
    $('#char-speed span').text((dat.speed.walk.value+dat.speed.walk.mod) + ' ft.');

    $('#init-base').text(dat.init);
    $('#init-mod').val(dat.init_mod);
    $('#ac-base').text(dat.ac.base);
    $('#ac-mod').val(dat.ac.mod);
    $('#spd-base').text(dat.speed.walk.value);
    $('#spd-mod').val(dat.speed.walk.mod);

    var abs = Object.keys(dat.abilities);
    $('#saves').html('<span id="save-adv-title">ADV</span><span id="save-dis-title">DIS</span>');
    for (var a=0;a<abs.length;a++) {
        $('#ab-'+abs[a]+' .ab-modifier').text(modformat(dat.abilities[abs[a]].mod));
        $('#ab-'+abs[a]+' .ab-score').text(dat.abilities[abs[a]].score);
        $('#ab-'+abs[a]+' .ab-base').val(dat.abilities[abs[a]].base_score).attr('placeholder','Base Score').attr('title','Base Score');
        $('#ab-'+abs[a]+' .ab-mod').val(dat.abilities[abs[a]].mod_score).attr('placeholder','Manual Mod').attr('title','Manual Modifier');
        $('#ab-'+abs[a]+' .ab-racial').val(dat.abilities[abs[a]].racial_mod).attr('placeholder','Racial Mod').attr('title','Racial Modifier');

        $('<div class="save-item"></div>')
        .attr('id','save_'+abs[a])
        .append(
            $('<label class="profmarker"></label>')
            .append(
                $('<input type="checkbox" class="sheet-in">')
                .prop('checked',dat.abilities[abs[a]].proficient)
                .attr('data-path','abilities.'+abs[a]+'.proficient')
            )
            .append('<span><span></span></span>')
            .attr('id','prof-save-'+abs[a])
        )
        .append(
            $('<span class="save-val"></span>').text(modformat(dat.abilities[abs[a]].save))
        )
        .append(
            $('<span class="save-name"></span>').text(abs[a][0].toUpperCase()+abs[a].slice(1))
        )
        .append(
            $('<label class="switch small"></label>')
            .append(
                $('<input type="checkbox" class="save-adv">')
                .attr('data-ability',abs[a])
                .on('change',function(event){
                    $($(event.target).parent().children('.save-dis')).prop('checked',false);
                    modify('abilities.'+$(event.target).attr('data-ability')+'.adv',cond($(event.target).prop('checked'),'2d20kh1','d20'));
                })
                .prop('checked',dat.abilities[abs[a]].adv=='2d20kh1')
            )
            .append(
                $('<span class="slider round"></span>')
            )
        )
        .append(
            $('<label class="switch small"></label>')
            .append(
                $('<input type="checkbox" class="save-dis">')
                .attr('data-ability',abs[a])
                .on('change',function(event){
                    $($(event.target).parent().children('.save-adv')).prop('checked',false);
                    modify('abilities.'+$(event.target).attr('data-ability')+'.adv',cond($(event.target).prop('checked'),'2d20kl1','d20'));
                })
                .prop('checked',dat.abilities[abs[a]].adv=='2d20kl1')
            )
            .append(
                $('<span class="slider round"></span>')
            )
        )
        .appendTo($('#saves'));
    }
    $('.ab-edit').off('click');
    $('.ab-edit').on('click',function(event){
        $($(event.target).parents('.ability-box')).toggleClass('editing');
    });

    $('#skills').html('<span id="skill-adv-title">ADV</span><span id="skill-dis-title">DIS</span>');
    var sks = Object.keys(dat.skills);
    for (var s=0;s<sks.length;s++) {
        $('<div class="skill-item"></div>')
        .attr('id','skill_'+sks[s])
        .append(
            $('<label class="profmarker"></label>')
            .append(
                $('<input type="checkbox" class="sheet-in">')
                .prop('checked',dat.skills[sks[s]].proficient)
                .toggleClass('expert',dat.skills[sks[s]].expert)
                .attr('data-path','skills.'+sks[s]+'.proficient')
                
            )
            .attr('data-skill','skills.'+sks[s])
            .append('<span><span></span></span>')
            .attr('id','prof-skill-'+sks[s])
            .on('contextmenu',function(event){
                event.preventDefault();
                if ($(event.delegateTarget).children('input').hasClass('expert')) {
                    modify($(event.delegateTarget).attr('data-skill')+'.expert',false);
                } else {
                    modify($(event.delegateTarget).attr('data-skill')+'.expert',true);
                }
            })
        )
        .append(
            $('<span class="skill-val"></span>').text(modformat(dat.skills[sks[s]].value+dat.skills[sks[s]].mod))
        )
        .append(
            $('<span class="skill-name"></span>').text((sks[s][0].toUpperCase()+sks[s].slice(1)).replace(/_/g,' '))
        )
        .append(
            $('<label class="switch small"></label>')
            .append(
                $('<input type="checkbox" class="skill-adv">')
                .attr('data-skill',sks[s])
                .on('change',function(event){
                    $($(event.target).parent().children('.skill-dis')).prop('checked',false);
                    modify('skills.'+$(event.target).attr('data-skill')+'.adv',cond($(event.target).prop('checked'),'2d20kh1','d20'));
                })
                .prop('checked',dat.skills[sks[s]].adv=='2d20kh1')
            )
            .append(
                $('<span class="slider round"></span>')
            )
        )
        .append(
            $('<label class="switch small"></label>')
            .append(
                $('<input type="checkbox" class="skill-dis">')
                .attr('data-skill',sks[s])
                .on('change',function(event){
                    $($(event.target).parent().children('.skill-adv')).prop('checked',false);
                    modify('skills.'+$(event.target).attr('data-skill')+'.adv',cond($(event.target).prop('checked'),'2d20kl1','d20'));
                })
                .prop('checked',dat.skills[sks[s]].adv=='2d20kl1')
            )
            .append(
                $('<span class="slider round"></span>')
            )
        )
        .appendTo($('#skills'));
    }

    $('#char-hp input').val(dat.hp);
    $('#char-hp input').attr('max',dat.max_hp);
    $('#char-maxhp input').val(dat.max_hp);
    $('#char-maxhp input').attr('disabled',dat.options.roll_hp == false);
    $('#char-thp input').val(dat.thp);

    // End
    $('input.fit').on('input',function(event){
        $(event.target).css('width',($(event.target).val().length+2)+'ch');
    })
    .each(function(index,elem){
        $(elem).css('width',($(elem).val().length+2)+'ch');
    });

    $('.sheet-in').on('change',function(event){
        if ($(event.target).attr('type') == 'checkbox') {
            var val = $(event.target).prop('checked');
        } else {
            var val = $(event.target).val();
        }
        if ($(event.target).attr('data-type') == 'number') {
            var val = Number(val);
        }
        var path = $(event.target).attr('data-path');

        if (path=='xp') {
            for (var i=0;i<LEVELXP.length;i++) {
                if (LEVELXP[i] >= val) {
                    modify('level',i+1)
                    break;
                }
            }
        }
        if (path=='level') {
            if (val <= LEVELXP.length) {
                modify('xp',LEVELXP[val-1]);
            }
        }

        modify(path,val);
        $(event.target).trigger('blur');
    });

    $('input[data-type=number]').on('input',function(event){
        var newval = '';
        for (var x=0;x<$(event.target).val().length;x++) {
            if ('-.0123456789'.includes($(event.target).val()[x])) {
                newval += $(event.target).val()[x];
            }
        }
        if ($(event.target).attr('min')) {
            var min = Number($(event.target).attr('min'));
        } else {
            var min = -10000000000000;
        }
        if ($(event.target).attr('max')) {
            var max = Number($(event.target).attr('max'));
        } else {
            var max = 10000000000000;
        }
        if (newval < min) {
            newval = min;
        }
        if (newval > max) {
            newval = max;
        }
        $(event.target).val(newval);
        if ($(event.target).hasClass('fit')) {
            $(event.target).css('width',($(event.target).val().length+2)+'ch');
        }
    });
    $('#character-settings-btn').off('click');
    $('#character-settings-btn').on('click',function(event){
        if (!activating && $('#character-settings-btn').hasClass('active')) {
            $(document).trigger('click');
            return;
        }
        activateitem('#character-settings');
        activateitem('#character-settings-btn');
        activateitem('#character-reset-btn');
        activateitem('#rest-buttons');
        
    });
    $('#character-reset-btn').off('click');
    $('#character-reset-btn').on('click',function(event){
        bootbox.confirm('Resetting this character will cause all changes you have made to be erased, except thos made to your inventory. Proceed?',function(result){
            if (result) {
                cpost(
                    '/characters/'+fingerprint+'/'+$('#character-sheet-display').attr('data-id')+'/reset/',
                    {},function(data){sheet_gen(data);},
                    {
                        alert: true
                    }
                );
            }
        });
    });
    $('#char-class').off('change');
    $('#char-class').on('change',function(event){
        var new_classes = [];
        var keys = ['subclass','class','level'];
        var index = 0;
        var parts = $(event.target).val().split(' ');
        if ((parts.length % 3) == 0) {
            var current = {};
            var lsum = 0;
            for (var p=0;p<parts.length;p++) {
                if (index == 0) {
                    current = {};
                }
                current[keys[index]] = parts[p];
                if (keys[index] == 'level') {
                    current[keys[index]] = Number(parts[p]);
                    if (isNaN(current[keys[index]])) {
                        bootbox.alert('Class levels should be numbers.');
                        cget(
                            '/characters/'+fingerprint+'/'+$('#character-sheet-display').attr('data-id')+'/',
                            {},true,
                            sheet_gen
                        );
                        $('#char-class').trigger('blur');
                        return;
                    }
                    lsum += current[keys[index]];
                }
                index++;
                if (index == 3) {
                    index = 0;
                    new_classes.push(current)
                }
            }
            modify('class_display',$(event.target).val());
            modify('classes',new_classes);
            if (lsum <= 20 && lsum > 0) {
                modify('level',lsum);
            }
            if (lsum <= LEVELXP.length && lsum > 0) {
                modify('xp',LEVELXP[lsum-1]);
            }
        } else {
            bootbox.alert('Please specify a subclass and level for each class.');
            cget(
                '/characters/'+fingerprint+'/'+$('#character-sheet-display').attr('data-id')+'/',
                {},true,
                sheet_gen
            );
        }
        $('#char-class').trigger('blur');
        
    });
    var cur_lsum = 0;
    for (var l=0;l<dat.classes.length;l++) {
        cur_lsum += dat.classes[l].level;
    }
    if (dat.level != cur_lsum) {
        $('#class-warning').show();
    } else {
        $('#class-warning').hide();
    }

    $('#important-stats-settings').off('click');
    $('#important-stats-settings').on('click',function(event){
        activateitem('#stat-settings');
    });

    $('#long-rest').off('click');
    $('#long-rest').on('click',function(event){
        modify('hp',$('#char-maxhp input').val());
        for (var hd=0;hd<dat.hit_dice.length;hd++) {
            modify('hit_dice.'+hd+'.current',dat.hit_dice[hd].max);
            dat.hit_dice[hd].current = dat.hit_dice[hd].max;
        }
        $('#short-rest').trigger('click');
    });
    $('#short-rest').off('click');
    $('#short-rest').on('click',function(event){
        $('#hit-dice-panel').html('');
        for (var hd=0;hd<dat.hit_dice.length;hd++) {
            $('<div class="hd-item"></div>')
            .attr('data-index',hd)
            .append(
                $('<span class="hd-content"></span>')
                .append(
                    $('<span class="current-hd"></span>').text(dat.hit_dice[hd].current)
                )
                .append(' / ')
                .append(
                    $('<span class="total-hd"></span>').text(dat.hit_dice[hd].raw)
                )
            )
            .append(
                $('<button class="spend-hd">SPEND</button>')
                .on('click',function(event){
                    var chd = Number($($(event.delegateTarget).parents('.hd-item')).attr('data-index'));
                    if (dat.hit_dice[chd].current > 0 && dat.hp != dat.max_hp) {
                        modify(
                            'hit_dice.'+chd+'.current',
                            dat.hit_dice[chd].current - 1
                        );
                        dat.hit_dice[chd].current -= 1;
                        var new_hp = dat.hp + Math.round(Math.random()*(dat.hit_dice[chd].die_size-1)) + 1 + dat.abilities.constitution.mod;
                        if (new_hp > dat.max_hp) {
                            new_hp = dat.max_hp;
                        }
                        modify('hp',new_hp);
                    }
                    $($(event.delegateTarget).parents('.hd-item').children('.hd-content').children('.current-hd')).text(dat.hit_dice[chd].current);
                })
            )
            .appendTo('#hit-dice-panel');
        }
        if (event.isTrigger == undefined) {
            $('#short-rest-panel').slideDown(200);
        }
    });
    $('#sr-commence').off('click');
    $('#sr-commence').on('click',function(event){
        $(document).trigger('click');
    });
    $(document).on('click',function(event){
        if ($(event.target).parents('div').find('#short-rest-panel').length == 0) {
            $('#short-rest-panel').slideUp(200);
        }
    })
}