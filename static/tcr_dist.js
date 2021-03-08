var dirNum = "";  // global variable
var interval;


// ************************************************************************* //


$(function() {
    // This function gets cookie with a given name
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');

    /*
    The functions below will create a header with csrftoken
    */

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

});


// ************************************************************************* //


// Submit post on submit
$('#mainForm').on('submit', function(event){
    event.preventDefault();
    requestDirectory();  // if successful, triggers startPipeline()
});

$('#terminateBtn').on('click', function(event){
    event.preventDefault();
    //if(dirNum != "") {
        terminateDirectory(dirNum, interval);
    //} else {
    //    console.log("no dirNum -> this does nothing")
    //}
})

// this function will not return until it gets results.
function requestDirectory() {
    console.log("request directory");
    $("#info").html( "" );
    
    // destroy old directory before making a new one.
    if(dirNum != "") {  
        terminateDirectory(dirNum, interval);
    }

    $.ajax({
        url : "request_directory/", // the endpoint
        type : "POST", //TODO: make GET instead of POST
        data : "no data",

        // handle a successful response
        success : function(json) {
	    dirNum = json["dirNum"];
            interval = setInterval( getStatus, 2000, dirNum );  // get status every two seconds
            
            console.log(dirNum);
            startPipeline(dirNum);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            $('#results').html( "<div class='alert-box alert radius' data-alert>Oops! requestDirectory encountered an error: "+errmsg+
                " </div>" );
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
};

function startPipeline(directoryNumber) {
    console.log("start pipeline");
    var formData = new FormData( document.getElementById('mainForm') );
    formData.append("dirNum", directoryNumber);
 
    /*for (var [key, value] of formData.entries()) { 
    	console.log(key, value);
    }*/
 
    $.ajax({
        url : "start_tcr_pipeline/", // endpoint
        type : "POST",
        data : formData,
	processData : false,
	contentType : false,

        success : function(response) {
            // this is the only successful response
            if(response == "started pipeline") {
                $('#results').html( "<p>Successfully started pipeline</p>" )  // empties the results area.  
            } else {
                console.log(response + " -> termination")
                terminateDirectory(directoryNumber, interval);
            }
            
            // This listens for input processing stage errors.
            if (response == "need organism"){
                $('#info').html( $('#info').html() + "<p>Please choose an organism</p>" )  
            } else if (response == "use form") {
                $('#info').html( $('#info').html() + "<p>Please use the form to submit data</p>" )  
            } else if (response == "bad dirNum") {
                $('#info').html( $('#info').html() + "<p>Your internal directory number is bad, try refreshing the page.</p>" )  
            } else if (response == "need files") {
                $('#info').html( $('#info').html() + "<p>Please sumbit the two needed files</p>" )  
            } else if (response == "file too big") {
                $('#info').html( $('#info').html() + "<p>At least one of your files is too big (over 50mb), you may ask for this value to be increased by contacting the server admin.</p>" )  
            } else if (response == "need email") {
                $('#info').html( $('#info').html() + "<p>You must submit a valid email address in order to recieve an email.</p>" )  
            }

            console.log(response);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            $('#results').html( "<div class='alert-box alert radius' data-alert>Oops! startPipeline has encountered an error: "+errmsg+
                " </div>" );
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
}


function terminateDirectory(directoryNumber, runningInterval) {
    console.log("terminating directory " + directoryNumber);
    clearInterval( runningInterval );
    if(dirNum == "") {
        return
    } else {    
        dirNum = ""
    } 
    
    $.ajax({
        url : "terminate/", // endpoint
        type : "POST",
        data : { "dirNum" : directoryNumber },

        success : function(response) {
            console.log("terminate dir -> " + response)
            $("#results").html( "<p>terminated directory</p>" );
            //$("#info").html( "" );
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            $('#results').html( "<div class='alert-box alert radius' data-alert>Oops! terminate has encountered an error: "+errmsg+
                "</div>" );
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
}

function getStatus(directoryNumber) {
    $.ajax({
        url : "get_status/", // endpoint
        type : "GET",
        data : { "dirNum" : directoryNumber },
	cache : false,

        // handle a successful response
        success : function(response) {
            if (response == "directory not assigned") {
                $('#results').html($('#results').html() + "<p>Your internal directory has not been assigned, try refreshing the page or contacting the server admin.</p>" )  
                $("#info").html( response );
            } else if( response == "request download" ) {
                // send download file request.
                downloadFile(dirNum);
                $("#info").html( "file downloaded" );
            } else if (response == "no download") {
                $('#info').html("analysis completed (file emailed)");
                clearInterval(interval);
            } else if (response == "requested status doesn't exist") {
                clearInterval(interval);
                $("#info").html( response + ". (There was likely an error with your analysis.)" );
            } else if (response.split("\n")[response.split("\n").length - 2] == "done") {
                $("#info").html( response );
                clearInterval(interval);
                console.log("done!");
            } else {
                $("#info").html( response );
            }

            console.log(response);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            $('#results').html( "<div class='alert-box alert radius' data-alert>Oops! getStatus has encountered an error: "+errmsg+
                " <a href='#' class='close'>&times;</a></div>" );
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });

}

// If the site adddress changes, this will break.
function downloadFile(directoryNumber) {
    clearInterval(interval);
    // redirect to "download_file/"
    var url = "https://bblab-hivresearchtools.ca/django/tools/tcr_distance/download_file/"
    var form = $( '<form action="' + url + '" method="post">' +
                  '<input type="hidden" name="csrfmiddlewaretoken" value="' + $( "#mainForm > input" ).val() + '">' + 
                  '<input type="hidden" name="dirNum" value="' + directoryNumber + '" />' + 
                  '</form>' );
    $('body').append(form);
    form.submit();

    dirNum = "";
}
