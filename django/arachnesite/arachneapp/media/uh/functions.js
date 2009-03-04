function focusQuery() {
    var query = document.getElementById("query");
    query.focus()
}

window.onload = focusQuery;

function previous() {
    var previousform = document.getElementById("previousform");
    previousform.submit();
}

function next() {
    var nextform = document.getElementById("nextform");
    nextform.submit();
}

function changeSites(action) {
    var container = document.getElementById("sites");
    var checkboxes = container.getElementsByTagName("input");
    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].type == "checkbox") {
            if (action < 0) {
                checkboxes[i].checked = !checkboxes[i].checked;
            } else {
                checkboxes[i].checked = action;
            }
        }
    }
}
