var SELECTED_PAGE = 'about';
var Converter = new showdown.Converter();

function CapFirstLetter(str) {
    return str.slice(0, 1).toUpperCase() + str.slice(1, str.length);
}

function load_list(){
    cget(
        '/server/help/',
        {},false,function(data){
            var pages = data.pages;
            console.log(data);
            $('#pages-list').html('');
            var dummy_list = $('<div></div>');
            for (var p=0;p<pages.length;p++) {
                if (pages[p] == SELECTED_PAGE) {
                    var selected = true;
                } else {
                    var selected = false;
                }
                $('<div class="page-item"></div>')
                .append($('<span></span>').text(pages[p].split('_').map(function(e){return CapFirstLetter(e)}).join(' ')))
                .toggleClass('selected',selected)
                .attr('data-page',pages[p])
                .appendTo(dummy_list);
            }
            $('#pages-list').html(dummy_list.html());
            $('.page-item').on('click',function(event){
                console.log(event.delegateTarget);
                if ($(event.delegateTarget).attr('data-page') != SELECTED_PAGE) {
                    $('.page-item').toggleClass('selected',false);
                    $(event.delegateTarget).toggleClass('selected',true);
                    SELECTED_PAGE = $(event.delegateTarget).attr('data-page');
                    $('#help-title span').text($(event.delegateTarget).text());
                    cget(
                        '/server/help/'+SELECTED_PAGE+'/',{},true,function(data){
                            $('#help-content').html(Converter.makeHtml(data.page));
                        }
                    );
                }
            });
        }
    );
}

$(document).ready(function(){
    window.setInterval(load_list,20000);
    load_list();
    $('#help-title span').text(SELECTED_PAGE.split('_').map(function(e){return CapFirstLetter(e)}).join(' '));
    cget(
        '/server/help/'+SELECTED_PAGE+'/',{},true,function(data){
            $('#help-content').html(Converter.makeHtml(data.page));
        }
    );
});