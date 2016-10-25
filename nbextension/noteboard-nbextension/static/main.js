define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'base/js/events',
    'notebook/js/notebook',
    'notebook/js/outputarea',
    'notebook/js/codecell'
], function (
    jupyter, $, utils, events, notebook, oa, codecell
) {

    // No event for this, so we monkeypatch!
    // MONKEY SEE, MONKEY PATCH!
    oa.OutputArea.prototype._handle_output = oa.OutputArea.prototype.handle_output;
    oa.OutputArea.prototype.handle_output = function (msg) {
        var that = this;
        if(this.cell.metadata.answer_key) {
            send_event('cell_execute',{
                notebook_key: jupyter.notebook.metadata.notebook_key,
                answer_key: this.cell.metadata.answer_key,
                code: this.cell.get_text(),
                output: msg.content.text
            }).done(function(data) {
                handle_execute_result(that, data);
            });
        }
        return this._handle_output(msg);
    };

    function get_user_name() {
        var base_url = utils.get_body_data('baseUrl');
        if (base_url.indexOf('/user/') !== -1) {
            // We're in a hub!
            // Assume we're going to be like, /something/user/UserName/
            return base_url.split('/').pop();
        } else {
            return 'local-testing-user';
        }
    }
    function set_result_status(is_correct, output_area) {
        var sign = output_area.prompt_overlay.children('i.result-icon');
        if (sign.length == 0) {
            sign = $('<i>').addClass('result-icon fa fa-3x').appendTo(output_area.prompt_overlay);
        }
        sign.removeClass('fa-times fa-check');
        if (is_correct) {
            sign.addClass('fa-check').css('color', 'green').attr('title', 'Correct answer!');
        } else {
            sign.addClass('fa-times').css('color', 'red').attr('title', 'Wrong answer :(');
        }
    }
    function handle_execute_result(output_area, response) {
        if (response.response.status == 'correct') {
            set_result_status(true, output_area);
            output_area.cell.metadata.result = 'correct';
        } else {
            set_result_status(false, output_area);
            output_area.cell.metadata.result = 'incorrect';
        }
    }

    function send_event(event_type, payload) {
        var url = 'http://' + window.location.hostname + ':5000/receive/' + event_type;
        payload['username'] = get_user_name();
        return $.ajax({
            type: 'POST',
            url: url,
            data: JSON.stringify(payload),
            dataType: 'json'
        });
    }

    function notebook_started() {
        // Send an event out when we first start the notebook
        events.on('kernel_ready.Kernel', function() {
            send_event('notebook_opened', {
                notebook_key: jupyter.notebook.metadata['notebook_key']
            });

        });

    }

    function output_changed() {
        events.on('execute.CodeCell', function(ev, payload){
            // Output area objects don't know what cells they belong to!
            // We use this to tell them
            // We keep re-setting it, but the other option was to monkeypatch
            // CodeCell's fromJSON (for initial cell loading) and create_element
            // calls. Unfortunately nbextensions run too late to usefully
            // monkeypatch fromJSON, so this is what we gotta do.
            payload.cell.output_area.cell = payload.cell;
        });
    }

    var load_ipython_extension = function () {
        notebook_started();
        output_changed();
    };

    return {
        load_ipython_extension: load_ipython_extension,
    };
});
