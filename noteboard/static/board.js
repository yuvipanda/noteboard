$(function(){
    $('#get-scoreboard').click(function(){
        fetch_and_display_board();
        return false;
    });
});

var last_timer_key = null;
function fetch_and_display_board() {
    var notebook_key = $('#notebook').val();
    var url = '/board/' + notebook_key;
    $.get(url).done(display_board);
    if (last_timer_key != null) {
        clearInterval(last_timer_key);
    }
    last_timer_key = setInterval(fetch_and_display_board, 5000);
}

function display_board(raw_data) {
    var data = JSON.parse(raw_data);
    var scoreboard = [];
    _.each(data, function(results, username) {
        scoreboard.push({
            username: username,
            solved: _.values(results).length,
            longest: _.max(_.values(results))
        });
    });
    scoreboard = _.sortBy(scoreboard, function(item) {
        return -(item.solved * 1000000 + item.longest);
    });
    $('#scoreboard tbody').empty();
    var rank = 0;
    _.each(scoreboard, function(item){
        rank += 1;
        $('#scoreboard tbody').append(
            $('<tr>').append(
                $('<td>').text(rank),
                $('<td>').text(item.username),
                $('<td>').text(item.solved),
                $('<td>').text(item.longest.toFixed(2))
            )
        );
    });

}
