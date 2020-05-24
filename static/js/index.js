
function onLoad() {
    document.getElementById('searchTerm').focus();

    var input = document.getElementById("searchTerm");
    input.addEventListener("keyup", function(event) {
      if (event.keyCode === 13) {
        event.preventDefault();
        document.getElementById("searchButton").click();
      }
    });
}

function onSearchBtnClick() {
    var text = document.getElementById('searchTerm').value

    if(text.length == 0) return false;

    parent.location='/search/' + text;
}
