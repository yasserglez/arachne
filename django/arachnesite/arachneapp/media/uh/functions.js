function focusQuery() {
    var query = document.getElementById('query');
    query.focus()
}

window.onload = focusQuery;

function previous() {
    var previousform = document.getElementById('previousform');
    previousform.submit();

}

function next() {
    var nextform = document.getElementById('nextform');
    nextform.submit();
}
