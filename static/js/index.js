
function onLoad() {
    document.getElementById('searchTerm').focus();

    var input = document.getElementById("searchTerm");
    input.addEventListener("keyup", function(event) {
      if (event.keyCode === 13) {
        event.preventDefault();
        document.getElementById("searchButton").click();
      }
    });

    var dateInView = getDateInView();
    const myDatePicker = MCDatepicker.create({
        el: '#datepicker',
        dateFormat: 'DD.MM.YYYY',
        bodyType: 'modal',
        showCalendarDisplay: true,
        firstWeekday: 1,
        selectedDate: dateInView,
        maxDate: new Date(),
    });
    myDatePicker.onSelect((date, formatedDate) => changeDate(date));
}

function getDateInView() {
    var dateStr = document.getElementById('datepicker').value;
    var items = dateStr.split('.');
    console.log(items);
    return new Date(items[2], items[1], items[0]);
}

function changeDate(date) {
    const zeroPad = (num, places) => String(num).padStart(places, '0');
    var dateStr = date.getFullYear() + '-' + zeroPad(date.getMonth()+1, 2) + '-' + zeroPad(date.getDate(),2);
    var items = window.location.pathname.split('/');
    var url = '/' + items[1] + '/' + items[2] + '/' + dateStr;
    window.open(url, '_self');
}

function onSearchBtnClick() {
    var text = document.getElementById('searchTerm').value

    if(text.length == 0) return false;

    parent.location='/search/' + text;
}
