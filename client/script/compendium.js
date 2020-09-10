function assembleMagicItems(data){
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

$(document).ready(function(){
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
        $('#comp-content-box').append($(
            '<input id="search-magic-items" placeholder="Search" class="comp-search">'
        ).change(function(event){
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
        $('#comp-content-box').append($(
            '<input id="search-spells" placeholder="Search" class="comp-search">'
        ).change(function(event){
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
});