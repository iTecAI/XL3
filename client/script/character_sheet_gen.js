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

function firstCase(str) {
    return str[0].toUpperCase() + str.slice(1);
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

function getCurCont() {
    for (var i=0;i<dat.inventory.containers.length;i++) {
        if (dat.inventory.current_container == dat.inventory.containers[i].name) {
            return i;
        }
    }
}

function getCont(name) {
    for (var i=0;i<dat.inventory.containers.length;i++) {
        if (name == dat.inventory.containers[i].name) {
            return i;
        }
    }
}

function sheet_gen(char,panel_tab) {
    $('#character-sheet-display').attr('data-id',char.cid);
    dat = char.data;
    console.log(dat);
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
    $('#inve-passive-val').text(dat.skills.investigation.value+dat.skills.investigation.mod+cond(dat.features.map(function(item){
        return item.toLowerCase() == 'feat: observant'
    }).includes(true),5,0)+cond(
        dat.skills.investigation.adv == '2d20kh1',5,0
    )+cond(
        dat.skills.investigation.adv == '2d20kl1',-5,0
    )+10);
    $('#char-init span').text(modformat(dat.init+dat.init_mod));
    $('#char-ac span').text(dat.ac.base + dat.ac.mod);
    $('#char-speed span').text((
        dat.speed.walk.value+dat.speed.walk.mod
        -cond(dat.options.variant_encumbrance && dat.inventory.current_weight > dat.inventory.variant_encumbrance.encumbered,10,0)
        -cond(dat.options.variant_encumbrance && dat.inventory.current_weight > dat.inventory.variant_encumbrance.heavily_encumbered,10,0)
    ) + ' ft.');

    $('#init-base').text(dat.init);
    $('#init-mod').val(dat.init_mod);
    $('#ac-base').text(dat.ac.base);
    $('#ac-mod').val(dat.ac.mod);
    $('#spd-base').text(dat.speed.walk.value);
    $('#spd-mod').val(dat.speed.walk.mod);

    $('#main-tabs button').removeClass('active');
    $('.panel-tab').removeClass('active');
    console.log(panel_tab);
    if (['inventory','spells','about'].includes(panel_tab)) {
        $('#'+panel_tab+'-tab').addClass('active');
        $('#tab-'+panel_tab).addClass('active');
    } else {
        $('#inventory-tab').addClass('active');
        $('#tab-inventory').addClass('active');
    }

    // Option setup
    $('#opt-public').prop('checked',dat.options.public);
    $('#opt-encumbrance').prop('checked',dat.options.variant_encumbrance);
    $('#opt-coinweight').prop('checked',dat.options.coin_weight);
    $('#opt-rollhp').prop('checked',dat.options.roll_hp);
    

    var abs = Object.keys(dat.abilities);
    $('#saves').html('<span id="save-adv-title">ADV</span><span id="save-dis-title">DIS</span><span id="save-head">SAVING THROWS</span>');
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

    $('#section-weapons-armor').html('');
    $('#section-tools-vehicles').html('');
    $('#section-languages').html('');
    var wap = [];
    for (var k=0;k<dat.weapon_profs.length;k++) {
        wap.push(dat.weapon_profs[k][0].toUpperCase()+dat.weapon_profs[k].slice(1));
    }
    for (var k=0;k<dat.armor_profs.length;k++) {
        if (dat.armor_profs[k].includes('shield')) {
            wap.push(dat.armor_profs[k][0].toUpperCase()+dat.armor_profs[k].slice(1));
        } else {
            wap.push(dat.armor_profs[k][0].toUpperCase()+dat.armor_profs[k].slice(1) + ' armor');
        }
    }
    $('#section-weapons-armor').text(wap.join(', '));
    var tvp = [];
    var opks = Object.keys(dat.other_profs);
    for (var k=0;k<opks.length;k++) {
        tvp.push(dat.other_profs[opks[k]][0].toUpperCase()+dat.other_profs[opks[k]].slice(1));
    }
    $('#section-tools-vehicles').text(tvp.join(', '));
    var lp = [];
    for (var k=0;k<dat.languages.length;k++) {
        lp.push(dat.languages[k][0].toUpperCase()+dat.languages[k].slice(1));
    }
    $('#section-languages').text(lp.join(', '));

    $('#actions-panel').html('');
    for (var a=0;a<dat.attacks.length;a++) {
        var features_desc = [];
        for (var f=0;f<dat.attacks[a].properties.length;f++) {
            if (Object.keys(dat.attacks[a].properties[f]).length == 1) {
                features_desc.push('<strong>'+dat.attacks[a].properties[f].name + '</strong>' + cond(f+1==dat.attacks[a].properties.length,'',', '));
            } else {
                var jnr = '<strong>'+dat.attacks[a].properties[f].name + ':</strong> ';
                for (var x=0;x<Object.keys(dat.attacks[a].properties[f]).length;x++) {
                    var ival = dat.attacks[a].properties[f][Object.keys(dat.attacks[a].properties[f])[x]];
                    if (Object.keys(dat.attacks[a].properties[f])[x] == 'name') {
                        continue;
                    } else {
                        jnr += Object.keys(dat.attacks[a].properties[f])[x] + '('+ival+')';
                    }
                }
                features_desc.push(cond(f>0,'<br>','')+jnr+cond(f+1==dat.attacks[a].properties.length,'','<br>'));
            }
            
        }
        features_desc = features_desc.join('');

        var damage_desc = [];
        for (var d=0;d<dat.attacks[a].damage.length;d++) {
            damage_desc.push(dat.attacks[a].damage[d].roll+' '+dat.attacks[a].damage[d].mods.join(' ')+' '+dat.attacks[a].damage[d].type+' damage');
        }
        damage_desc = damage_desc.join(' plus ');

        $('<div class="action-item"></div>')
        .attr('data-index',a)
        .append(
            $('<div class="action-item-title"></div>').text(dat.attacks[a].name)
            .on('click',function(event){
                $(event.delegateTarget).parents('.action-item').toggleClass('active');
            })
        )
        .append(
            $('<div class="action-item-sub"></div>').text((dat.attacks[a].type + ' ' + dat.attacks[a].category + ' weapon').toUpperCase())
        )
        .append(
            $('<div class="atk-info noscroll noselect"></div>')
            .append(
                $('<div class="action-item-hit_info"></div>')
                .append(
                    $('<span class="item-part-content"></span>').html([
                        '<em>To Hit:</em> ',
                        'd20'+cond(dat.attacks[a].bonus+dat.attacks[a].bonus_mod>0,'+','')+cond(dat.attacks[a].bonus+dat.attacks[a].bonus_mod==0,'',(dat.attacks[a].bonus+dat.attacks[a].bonus_mod).toString())+'<br>',
                        '<em>Hit:</em> ',
                        damage_desc + cond(dat.attacks[a].maximize_damage,' (maximized).','.')
                    ].join(''))
                )
            )
            .append(
                $('<div class="action-item-feats"></div>')
                .append(
                    $('<span class="item-part-title"></span>').text('FEATURES')
                )
                .append(
                    $('<span class="item-part-content"></span>').html(features_desc)
                )
            )
        )
        .append(
            $('<button class="action-edit"><img src="assets/icons/edit-white.png"></button>')
            .on('click',function(event){
                var index = Number($(event.delegateTarget).parents('.action-item').attr('data-index'));
                var item = dat.attacks[index];
                console.log(item);
                $('#atk-submit-btn').text('EDIT');
                $('#atk-edit-create-area').scrollTop(0);
                $('#atk-name-input').val(item.name);

                $('#atk-feat-input').val('');
                $('#atk-feat-tags').html('');
                for (var p=0;p<item.properties.length;p++) {
                    var prop = item.properties[p];
                    var propstr = firstCase(prop.name);
    
                    var ks = Object.keys(prop);
                    for (var k=0;k<ks.length;k++) {
                        if (ks[k] == 'value') {
                            propstr += ' ('+prop[ks[k]]+')';
                        } else if (ks[k] == 'name') {
                            continue;
                        } else {
                            propstr += ' ('+ks[k]+' '+prop[ks[k]]+')';
                        }
                    }
                    $('#atk-feat-input').val(propstr).trigger('change');
                }

                $('#atk-dmg-input').val('');
                $('#dmg-tags').html('');

                for (var d=0;d<item.damage.length;d++) {
                    $('#atk-dmg-input').val(item.damage[d].roll + ' ' + cond(item.damage[d].mods.length > 0,item.damage[d].mods.join(' ')+' ','') + item.damage[d].type)
                    $('#atk-dmg-input').trigger('change');
                }
                $('#atk-dmg-input').val('');
                
                $('#atk-group-input').val(item.category);
                $('#atk-type-input').val(item.type);
                $('#atk-max-input').val(cond(item.maximize_damage==true,'yes','no'));
                $('#atk-bonusmod-input').val(item.bonus_mod);
                $('#atk-submit-btn').on('click',function(event){
                    var dat = {
                        name:$('#atk-name-input').val(),
                        bonus_mod:cond(isNaN(Number($('#atk-bonusmod-input').val())),0,Number($('#atk-bonusmod-input').val())),
                        category:$('#atk-group-input').val(),
                        type:$('#atk-type-input').val(),
                        maxdmg:cond($('#atk-max-input').val()=='yes',true,false),
                        damage:$('#dmg-tags .tag-item').map(function(i,e){
                            return $(e).text();
                        }).toArray(),
                        properties:$('#atk-feat-tags .tag-item').map(function(i,e){
                            return $(e).text();
                        }).toArray(),
                        index:index
                    };
                    cpost(
                        '/characters/'+fingerprint+'/'+$('#character-sheet-display').attr('data-id')+'/modify/attacks/',
                        {
                            action: 'modify',
                            data: dat
                        },sheet_gen,
                        {
                            alert:true
                        }
                    );
                    $('#atk-edit-create-area').toggleClass('active',false);
                });
                $('#atk-edit-create-area').toggleClass('active',true);
            })
        )
        .append(
            $('<button class="action-delete"><img src="assets/icons/delete.png"></button>')
            .on('click',function(event){
                cpost(
                    '/characters/'+fingerprint+'/'+$('#character-sheet-display').attr('data-id')+'/modify/attacks/',
                    {
                        action:'remove',
                        data:{
                            index:Number($(event.delegateTarget).parents('.action-item').attr('data-index'))
                        }
                    },
                    sheet_gen,
                    {alert:true}
                );
            })
        )
        .appendTo('#actions-panel');
    }

    $('#cur-carry-wt').text(dat.inventory.current_weight + ' lb.');
    $('#max-carry-wt').text(dat.inventory.carry_capacity + ' lb.');
    if (dat.inventory.current_weight < dat.inventory.variant_encumbrance.encumbered || (!dat.options.variant_encumbrance && dat.inventory.current_weight < dat.inventory.carry_capacity)) {
        $('#encumbrance-val').text('Not Encumbered.');
        $('#encumbrance-val').css('color','rgb(17, 240, 76)');
        $('#encumbrance-val').css('background-color','rgba(0,0,0,0)');
    } else if (dat.inventory.current_weight < dat.inventory.variant_encumbrance.heavily_encumbered && dat.options.variant_encumbrance) {
        $('#encumbrance-val').text('Encumbered.');
        $('#encumbrance-val').css('color','rgb(240, 236, 17)');
        $('#encumbrance-val').css('background-color','rgba(0,0,0,0)');
    } else if (dat.inventory.current_weight < dat.inventory.carry_capacity && dat.options.variant_encumbrance) {
        $('#encumbrance-val').text('Heavily Encumbered.');
        $('#encumbrance-val').css('color','rgb(240, 140, 17)');
        $('#encumbrance-val').css('background-color','rgba(0,0,0,0)');
    } else {
        $('#encumbrance-val').text('Overencumbered.');
        $('#encumbrance-val').css({'background-color':'rgb(255, 59, 59)','color':'#ffffff'});
    }

    $('#cur-wealth').text(dat.inventory.total_wealth+' gp.');
    $('#cur-coin').text(dat.inventory.total_coin+' gp.');

    //$('#cur-cont-val').text(firstCase(dat.inventory.current_container));
    $('#cur-cont-val').html('');
    var items = dat.inventory.containers.map(function(v,i){return v.name;});
    for (var c=0;c<items.length;c++) {
        $('<option></option>')
        .attr('value',items[c])
        .text(firstCase(items[c]))
        .appendTo($('#cur-cont-val'));
    }
    $('#cur-cont-val').val(dat.inventory.current_container)
    .off('change')
    .on('change',function(event){
        modify('inventory.current_container',$(this).val());
    });
    $('#cur-cont-wt').val(dat.inventory.containers[getCurCont()].current_weight);
    $('#max-cont-wt').val(dat.inventory.containers[getCurCont()].max_weight)
    .off('change').on('change',function(event){
        modify('inventory.containers.'+getCurCont()+'.max_weight',Number($(this).val()));
        $(this).trigger('blur');
    });
    $('#cont-apply-wt').prop('checked',dat.inventory.containers[getCurCont()].apply_weight)
    .off('change').on('change',function(event){
        modify('inventory.containers.'+getCurCont()+'.apply_weight',$(this).prop('checked'));
    });
    $('#cont-coins').prop('checked',dat.inventory.containers[getCurCont()].coin_container)
    .off('change').on('change',function(event){
        modify('inventory.containers.'+getCurCont()+'.coin_container',$(this).prop('checked'));
    });

    $('#delete-container').toggle(dat.inventory.containers[getCurCont()].removable);
    $('#create-container').css('height',cond(dat.inventory.containers[getCurCont()].removable,'50%','100%'));

    $('#coins').html('');
    for (var c=0;c<dat.inventory.coin.length;c++) {
        var coin_colors = {
            cp:'#d16b00',
            sp:'#b0b0b0',
            ep:'#dbd9bf',
            gp:'#ffcc00',
            pp:'#9aede9'
        };
        $('<div class="coin-item"></div>')
        .append(
            $('<span class="coin-title"></span>')
            .append($('<span></span>').text(dat.inventory.coin[c].name.toUpperCase()))
            
        )
        .append(
            $('<input class="coin-val sheet-in" data-type="number" min="0">')
            .val(dat.inventory.coin[c].amount)
            .attr('data-path','inventory.coin.'+c+'.amount')
            .css('color',coin_colors[dat.inventory.coin[c].name])
        )
        .appendTo('#coins');
    }

    $('#items-table tbody').html('');
    cget(
        '/compendium/search/equipment/',
        {},
        true,
        function(cdata) {
            var dcd = {};
            for (var c=0;c<cdata.length;c++) {
                dcd[cdata[c].slug] = cdata[c];
            }
            console.log(dcd);
            for (var j=0;j<dat.inventory.containers[getCurCont()].items.length;j++) {
                var item = dat.inventory.containers[getCurCont()].items[j];
        
                var cselect = $('<select></select>');
                var conts = dat.inventory.containers.map(function(v,i){return v.name;});
                for (var c=0;c<conts.length;c++) {
                    $('<option></option>')
                    .attr('value',conts[c])
                    .text(firstCase(conts[c]))
                    .appendTo(cselect);
                }
                cselect.on('change',function(event){
                    var reqData = {
                        oldContainerIndex: Number(getCurCont()),
                        itemIndex: Number($(event.target).parents('.item').attr('data-index')),
                        newContainerIndex:Number(getCont($(event.target).val().toLowerCase()))
                    };
                    console.log(reqData);
                    cpost(
                        '/characters/'+fingerprint+'/'+$('#character-sheet-display').attr('data-id')+'/modify/inventory/items/move/',
                        reqData,
                        sheet_gen,
                        {
                            alert: true
                        }
                    );
                });

                var calculated_slug = item.name.toLowerCase().replace(/ /g,'-').replace(/,/g,'').replace(/\(/g,'').replace(/\)/g,'').replace(/'/g,'');

                if (Object.keys(dcd).includes(calculated_slug)) {
                    var itype = dcd[calculated_slug].type;
                } else {
                    var itype = 'gear';
                }

                $('<tr class="item"></tr>')
                .attr('id',item.name)
                .attr('data-index',j)
                .attr('data-type',itype)
                .append(
                    $('<td></td>')
                    .append(
                        $('<input class="sheet-in" min="0" data-type="number">')
                        .val(item.quantity)
                        .css('text-align','center')
                        .attr('data-path','inventory.containers.'+getCurCont()+'.items.'+j+'.quantity')
                        .on('change',function(event){
                            var path = $(this).attr('data-path');
                            var val = Number($(this).val());
                            modify(path,val);
                            $(this).trigger('blur');
                        })
                    )
                )
                .append(
                    $('<td></td>')
                    .append(
                        $('<input class="sheet-in" spellcheck="false">')
                        .val(item.name)
                        .css('text-align','left')
                        .attr('data-path','inventory.containers.'+getCurCont()+'.items.'+j+'.name')
                        .on('change',function(event){
                            var path = $(this).attr('data-path');
                            var val = $(this).val();
                            modify(path,val);
                            $(this).trigger('blur');
                        })
                    )
                )
                .append(
                    $('<td></td>')
                    .append(
                        $('<input class="sheet-in" min="0" data-type="number">')
                        .val(item.cost)
                        .attr('data-path','inventory.containers.'+getCurCont()+'.items.'+j+'.cost')
                        .css('width','69%')
                        .css('text-align','right')
                        .on('change',function(event){
                            var path = $(this).attr('data-path');
                            var val = Number($(this).val());
                            modify(path,val);
                            $(this).trigger('blur');
                        })
                    )
                    .append($('<span> gp</span>').css('width','29%'))
                )
                .append(
                    $('<td></td>')
                    .append(
                        $('<input class="sheet-in" min="0" data-type="number">')
                        .val(item.weight)
                        .attr('data-path','inventory.containers.'+getCurCont()+'.items.'+j+'.weight')
                        .css('width','69%')
                        .css('text-align','right')
                        .on('change',function(event){
                            var path = $(this).attr('data-path');
                            var val = Number($(this).val());
                            modify(path,val);
                            $(this).trigger('blur');
                        })
                    )
                    .append($('<span> lb.</span>').css('width','29%'))
                )
                .append(
                    $('<td></td>')
                    .append(
                        $(cselect).val(dat.inventory.current_container)
                        .on('change',function(event){
                            var path = $(this).attr('data-path');
                            var val = $(this).val();
                            modify(path,val);
                            $(this).trigger('blur');
                        })
                    )
                )
                .appendTo('#items-table tbody');
            }
        }
    );

    $('#new-item-cont').text(firstCase(dat.inventory.current_container));
    

    // End -- START HOOKS
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
        bootbox.confirm('Resetting this character will cause all changes you have made to be erased, except those made to your inventory. Proceed?',function(result){
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
    });
    $('#main-tabs button').off('click');
    $('#main-tabs button').on('click',function(event){
        if ($('#main-modal').hasClass('active')) {
            return;
        }
        $('#main-tabs button').removeClass('active');
        $('.panel-tab').removeClass('active');
        $(event.delegateTarget).addClass('active');
        $('#tab-'+$(event.delegateTarget).attr('data-tab')).addClass('active');
    });

    $('.tag-input').on('change',function(event){
        if ($(event.target).val().length == 0) {
            return;
        }
        $('<span class="tag-item"></span>')
        .text($(event.target).val())
        .on('click',function(_event){
            $(_event.target).animate({width:'0px','padding-left':'0px','padding-right':'0px'},500,undefined,function(){
                $(this).remove();
            });
            
        })
        .appendTo($('#'+$(event.target).attr('data-display')));
        $(event.target).val('');
    });
    $('.tag-display').off('mousewheel');
    $('.tag-display').on('mousewheel',function(event){
        event.preventDefault();
        this.scrollLeft -= (event.originalEvent.deltaY * 0.2);
    });

    $('#atk-name-input').off('keydown');
    $('#atk-name-input').on('keydown',function(event){
        if ($('#atk-name-input').val().length == 0) {
            return;
        }
        cget(
            '/compendium/search/weapons/?search='+$(event.target).val().toLowerCase().replace(/ /g,'-').replace(/,/g,'').replace(/\(/g,'').replace(/\)/g,''),
            {},
            false,function(data) {
                if (data.length > 0) {
                    $('#atk-options').html('');
                    for (var d=0;d<data.length;d++) {
                        $('<option></option>')
                        .attr('label',data[d].name.replace('-', ' '))
                        .attr('value',d)
                        .text(data[d].name.replace('-', ' '))
                        .appendTo($('#atk-options'));
                    }
                    $('#atk-options').attr('data-list',JSON.stringify(data));
                } else {
                    $('#atk-options').html('');
                }
            }
        );
    });
    $('#atk-name-input').on('change',function(event) {
        if ($('#atk-name-input').val().length == 0) {
            return;
        }
        console.log($(event.target).val());
        if (!isNaN(Number($(event.target).val()))) {
            $('#atk-name-input').trigger('blur');
            var data = JSON.parse($('#atk-options').attr('data-list'));
            var item = data[Number($(event.target).val())];
            $('#atk-name-input').val(item.name.replace(/\-/g,' '));
            $('#dmg-tags').html('');
            $('#atk-feat-tags').html('');
            $('#atk-dmg-input').val(item.damage.dice + cond(
                (item.properties.map(function(v,i){return v.name.toLowerCase()}).includes('finesse') && dat.abilities.dexterity.mod >= dat.abilities.strength.mod) || item.type == 'ranged',
                cond(dat.abilities.dexterity.mod >=0,'+','')+dat.abilities.dexterity.mod,
                cond(dat.abilities.strength.mod >=0,'+','')+dat.abilities.strength.mod
            ) + ' ' + item.damage.type).trigger('change');
            
            for (var p=0;p<item.properties.length;p++) {
                var prop = item.properties[p];
                var propstr = firstCase(prop.name);
                delete prop.name;

                var ks = Object.keys(prop);
                for (var k=0;k<ks.length;k++) {
                    if (ks[k] == 'value') {
                        propstr += ' ('+prop[ks[k]]+')';
                    } else {
                        propstr += ' ('+ks[k]+' '+prop[ks[k]]+')';
                    }
                }
                $('#atk-feat-input').val(propstr).trigger('change');
            }

            $('#atk-group-input').val(item.group);
            $('#atk-type-input').val(item.type);
            $('#atk-max-input').val('no');
        }
    });

    $('#new-atk-button').off('click');
    $('#new-atk-button').on('click',function(event){
        $('#atk-submit-btn').text('CREATE');
        $('#atk-edit-create-area').scrollTop(0);
        $('#atk-name-input').val('');
        $('#atk-dmg-input').val('');
        $('#dmg-tags').html('');
        $('#atk-feat-input').val('');
        $('#atk-feat-tags').html('');
        $('#atk-group-input').val('simple');
        $('#atk-type-input').val('melee');
        $('#atk-max-input').val('max');
        $('#atk-bonusmod-input').val('');
        $('#atk-submit-btn').on('click',function(event){
            var dat = {
                name:$('#atk-name-input').val(),
                bonus_mod:cond(isNaN(Number($('#atk-bonusmod-input').val())),0,Number($('#atk-bonusmod-input').val())),
                category:$('#atk-group-input').val(),
                type:$('#atk-type-input').val(),
                maxdmg:cond($('#atk-max-input').val()=='yes',true,false),
                damage:$('#dmg-tags .tag-item').map(function(i,e){
                    return $(e).text();
                }).toArray(),
                properties:$('#atk-feat-tags .tag-item').map(function(i,e){
                    return $(e).text();
                }).toArray()
            };
            cpost(
                '/characters/'+fingerprint+'/'+$('#character-sheet-display').attr('data-id')+'/modify/attacks/',
                {
                    action: 'add',
                    data: dat
                },sheet_gen,
                {
                    alert:true
                }
            );
            $('#atk-edit-create-area').toggleClass('active',false);
        });
        $('#atk-edit-create-area').toggleClass('active',true);
    });
    $('#atk-cancel-btn').off('click');
    $('#atk-cancel-btn').on('click',function(event){$('#atk-edit-create-area').toggleClass('active',false);});

    $('#expand-atk').off('click');
    $('#expand-atk').on('click',function(event){$('#actions').toggleClass('expanded');$('#main-modal').toggleClass('active',$('#actions').hasClass('expanded'));});

    $('#create-container').off('click').on('click',function(event){
        bootbox.prompt('Enter new container name.',function(result){
            if (!result) {
                return;
            }
            cpost(
                '/characters/'+fingerprint+'/'+$('#character-sheet-display').attr('data-id')+'/modify/inventory/containers/new/',
                {
                    name:result
                },
                sheet_gen,
                {
                    alert: true
                }
            );
        });
    });
    $('#delete-container').off('click').on('click',function(event){
        bootbox.confirm('Delete container "'+dat.inventory.current_container+'"?',function(result){
            if (!result) {
                return;
            }
            cpost(
                '/characters/'+fingerprint+'/'+$('#character-sheet-display').attr('data-id')+'/modify/inventory/containers/remove/',
                {
                    index:getCurCont()
                },
                sheet_gen,
                {
                    alert: true
                }
            );
        });
    });

    $('#new-item-name').off('keydown').on('keydown',function(event){
        if ($(this).val().length == 0) {
            $('#item-name-opts').html('');
            return;
        }
        cget(
            '/compendium/search/equipment/?search='+$(event.target).val().toLowerCase().replace(/ /g,'-').replace(/,/g,'').replace(/\(/g,'').replace(/\)/g,''),
            {},
            false,function(data) {
                if (data.length > 0) {
                    $('#item-name-opts').html('');
                    for (var d=0;d<data.length;d++) {
                        $('<option></option>')
                        .attr('value',data[d].name)
                        .text(data[d].name.replace('-', ' '))
                        .appendTo($('#item-name-opts'));
                    }
                    $('#new-item-name').attr('data-list',JSON.stringify(data));
                } else {
                    $('#item-name-opts').html('');
                }
            }
        );
    });
    $('#new-item-name').off('change').on('change',function(event){
        if ($(this).val().length == 0) {
            $('#item-name-opts').html('');
            $('#item-name-opts').html('');
            $('#new-item-qt').val('');
            $('#new-item-cost').val('');
            $('#new-item-wt').val('');
            return;
        }
        cget(
            '/compendium/search/equipment/?search='+$(event.target).val().toLowerCase().replace(/ /g,'-').replace(/,/g,'').replace(/\(/g,'').replace(/\)/g,''),
            {},
            false,function(data) {
                if (data.length == 1) {
                    console.log(data);
                    if (data[0].name == $('#new-item-name').val()) {
                        $('#item-name-opts').html('');
                        $('#new-item-qt').val(data[0].quantity);
                        $('#new-item-cost').val(data[0].cost);
                        $('#new-item-wt').val(data[0].weight);
                    }
                } else {
                    $('#item-name-opts').html('');
                    $('#new-item-qt').val('');
                    $('#new-item-cost').val('');
                    $('#new-item-wt').val('');
                }
            }
        );
    });

    $('#new-item-submit').off('click').on('click',function(event){
        cpost(
            '/characters/'+fingerprint+'/'+$('#character-sheet-display').attr('data-id')+'/modify/inventory/items/new/',
            {
                name:$('#new-item-name').val(),
                quantity:$('#new-item-qt').val(),
                cost:$('#new-item-cost').val(),
                weight:$('#new-item-wt').val(),
                containerIndex:getCurCont()
            },
            sheet_gen,
            {
                alert: true
            }
        );
        $('#new-item-name').val('');
        $('#item-name-opts').html('');
        $('#new-item-qt').val('');
        $('#new-item-cost').val('');
        $('#new-item-wt').val('');
    });
}