var map;
var searchInProgress = false;
var searchResults = document.getElementById("searchResults");
var colors = ['Green', 'MidnightBlue', 'Sienna', 'Gray', 'Plum', 'Turquoise', 'Black', 'Aqua', 'Chartreuse', 'BlueViolet', 'CornflowerBlue', 'DarkMagenta' , 'DeepPink'];
var colorIndex = 0;

function addFlightToMap(flightSegments, skipSegments, lineColor='red') {
    var allPoints = new Array();
    for (var i = 0; i < flightSegments.length; i++) {
        L.polyline(flightSegments[i], {color: lineColor, weight: 2}).addTo(map);
        allPoints = allPoints.concat(flightSegments[i]);
    }
    for (var i = 0; i < skipSegments.length; i++) {
        L.polyline(skipSegments[i], {color: 'blue', weight: '2', dashArray: '4, 4', dashOffset: '0'}).addTo(map)
        allPoints = allPoints.concat(skipSegments[i]);
    }
    var polyline = L.polyline(allPoints, {color: 'green', weight: 2});
    map.fitBounds(polyline.getBounds());

    var greenIcon = new L.Icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    });

    var redIcon = new L.Icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    });

    var takeoffMarker = L.marker(flightSegments[0][0], {icon: greenIcon}).addTo(map);
    takeoffMarker.bindPopup("<b>Take-off<b>");

    var lastFlightSegment = flightSegments[flightSegments.length-1];
    var landingMarker = L.marker(lastFlightSegment[lastFlightSegment.length-1],{icon: redIcon}).addTo(map);
    landingMarker.bindPopup("<b>Landing</b>");
}

function onPageLoad() {
    map = L.map('map'); //.setView([51.505, -0.09], 13);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

	L.control.scale().addTo(map);

    addFlightToMap(flightSegments, skipSegments);
}

function addButtonClicked() {
    document.getElementById("addButton").style.visibility = 'hidden';
    document.getElementById("sideBar").style.visibility = 'visible';
}

function closeSideBar() {
    document.getElementById("sideBar").style.visibility = 'hidden';
    document.getElementById("addButton").style.visibility = 'visible';
}

function searchFlight() {
    var date = document.getElementById("date").value.trim();
    var loc = document.getElementById("location").value.trim();
    var reg = document.getElementById("reg").value.trim();
    var cn = document.getElementById("cn").value.trim();

    if(!loc && !reg && !cn) {
        alert("WTF?!");
        return;
    }

    if(searchInProgress) {
        alert("Search already in progress!");
        return;
    }

    searchStarted();

    var query = `/api/ff?date=${date}&loc=${loc}&reg=${reg}&cn=${cn}`;

    const req = new XMLHttpRequest();
    req.open("GET", query, true);
    req.onload = onFlightSearchResp;
    req.onerror = (e) => {
      console.error(req.statusText);
      alert('Nejaky problem ve vyhledavani letu #2');
    };
    req.send(null);
}

function searchStarted() {
    searchInProgress = true;
    document.getElementById("sideBarSearchBtn").disabled=true;
    document.getElementById("labelForSearchResults").style.visibility='hidden';
    searchResults.textContent = "Working..";
    colorIndex = 0;
}

function searchFinished() {
    searchInProgress = false;
    document.getElementById("sideBarSearchBtn").disabled=false;
    document.getElementById("labelForSearchResults").style.visibility='visible';
    searchResults.innerHtml = "";
}

function onFlightSearchResp(e) {
    searchFinished();

    //var req = e.originalTarget;
    var resp = e.currentTarget;
    if (resp.readyState === 4 && resp.status === 200) {
        var content = "";
        var flights = JSON.parse(resp.responseText);
        for (const flight of flights) {
            var reg = flight.reg ? flight.reg : '?';
            var cn = flight.cn ? flight.cn : '?';
            console.log("XXX:" + flight.to_loc);
            var takeoffLoc = flight.to_loc ? flight.to_loc : '?';
            //var to_ts = new Date(flight.to_ts*1000);
            var landingLoc = flight.la_loc ? flight.la_loc : '?';
            //var la_ts = new Date(flight.la_ts*1000);

            content += `<div id='SR${flight.id}' class="searchResult" onClick="addFoundFlightToMap(${flight.id});"><span id="FL${flight.id}"></span><div class='flex_item'>${reg} (${cn}) ${takeoffLoc} &#8605; ${landingLoc}</div></div>`
        }

        searchResults.innerHTML = content;

    } else {
        alert('Nejaky problem ve vyhledavani letu #1');
    }
}

function addFoundFlightToMap(flightId) {
    var query = `/api/fd/${flightId}`;

    const req = new XMLHttpRequest();
    req.open("GET", query, true);

    req.onload = (e) => {
        var resp = e.currentTarget;
        if (resp.readyState === 4 && resp.status === 200) {
            var flightData = JSON.parse(resp.responseText);
            if(!flightData.hasOwnProperty('flightSegments') || !flightData.hasOwnProperty('skipSegments')) return;

            var flightSegments = flightData.flightSegments;
            var skipSegments = flightData.skipSegments;
            var color = colors[(colorIndex < colors.length ? colorIndex++ : colors.length-1)];
            addFlightToMap(flightSegments, skipSegments, color);

            // change appearance in the search results:
            var span = document.getElementById(`FL${flightId}`);
            span.style.backgroundColor=color;
            var searchResultDiv = document.getElementById(`SR${flightId}`);
            searchResultDiv.className = "searchResultDisabled";
            searchResultDiv.onclick = null;

        } else {
            alert('No data');
        }
    };

    req.onerror = (e) => {
      console.error(req.statusText);
      alert('Nejaky problem v pridavani letu na mapu.');
    };
    req.send(null);

}
