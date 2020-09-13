function sheet_gen(char) {
    console.log(char);
    $('#character-sheet-display').attr('data-id',char.cid);
    var dat = char.data;
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
    $('#char-class').text(dat.class_display);
    $('#char-level').val(dat.level);
    $('#char-xp').val(dat.xp);


    // End
    $('input.fit').on('input',function(event){
        $(event.target).css('width',($(event.target).val().length+2)+'ch');
    })
    .each(function(index,elem){
        $(elem).css('width',($(elem).val().length+2)+'ch');
    });

    $('.sheet-in').on('change',function(event){
        cpost(
            '/characters/'+fingerprint+'/'+$('#character-sheet-display').attr('data-id')+'/modify/',
            {
                'path':$(event.target).attr('data-path'),
                'data':$(event.target).val()
            },
            function(data){
                console.log(data);
            },
            {
                alert: true
            }
        );
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
        $(event.target).css('width',($(event.target).val().length+2)+'ch');
    });
}