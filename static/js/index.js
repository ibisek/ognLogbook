
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
    if (dateInView != null) {
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
}

function getDateInView() {
    const datePicker = document.getElementById('datepicker');
    if (datePicker != null) {
        var dateStr = datePicker.value;
        var items = dateStr.split('.');
        console.log(items);
        return new Date(items[2], items[1], items[0]);
    }

    return null;
}

function changeDate(date) {
    var showFlightsOnly = window.location.href.includes('flightsOnly') ? '?flightsOnly' : '';
    const zeroPad = (num, places) => String(num).padStart(places, '0');
    var dateStr = date.getFullYear() + '-' + zeroPad(date.getMonth()+1, 2) + '-' + zeroPad(date.getDate(),2);
    var items = window.location.pathname.split('/');
    var url = '/' + items[1] + '/' + items[2] + '/' + dateStr + showFlightsOnly;
    window.open(url, '_self');
}

function onSearchBtnClick() {
    var text = document.getElementById('searchTerm').value

    if(text.length == 0) return false;

    parent.location='/search/' + text;
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

function switchTimezone() {
    const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const cookieTimezone = getCookie('browser_timezone');

    var newTimezone = browserTimezone;
    if (browserTimezone == cookieTimezone) newTimezone = 'UTC';

    document.cookie = `browser_timezone=${newTimezone};path=/`;
    fetch("/set_timezone", {method: 'POST', body: newTimezone})
        .then(function() { location.reload(); });
}