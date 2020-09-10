$(document).ready(function(){
    $('.ep-section-content > button').click(function(event){
        cget(
            '/compendium/section/'+$(event.target).attr('data-endpoint')+'/',
            {},true,
            function(data){
                $('#comp-content-box').html(data.content);
                $('#comp-title-box span').text($(event.target).text());
            }
        )
    });
});