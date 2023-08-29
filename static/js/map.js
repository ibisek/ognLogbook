var searchInProgress = false;
var searchResults = document.getElementById("searchResults");

function onPageLoad() {
    var map = L.map('map'); //.setView([51.505, -0.09], 13);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

	L.control.scale().addTo(map);

    var allPoints = new Array();
    for (var i = 0; i < flightSegments.length; i++) {
        L.polyline(flightSegments[i], {color: 'red', weight: 2}).addTo(map);
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

    var query = `/ff?date=${date}&loc=${loc}&reg=${reg}&cn=${cn}`;

    const req = new XMLHttpRequest();
    req.open("GET", query, true);
    req.onload = onFlightSearchResp;
    req.onerror = (e) => {
      console.error(req.statusText);
      alert('nejaky problem ve vyhledavani letu #2');
    };
    req.send(null);
}

function searchStarted() {
    searchInProgress = true;
    document.getElementById("sideBarSearchBtn").disabled=true;
    document.getElementById("labelForSearchResults").style.visibility='hidden';
    searchResults.textContent = "Working..";
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
        var content = "<table>";
        var flights = JSON.parse(resp.responseText);
        for (const flight of flights) {
            var reg = flight.reg ? flight.reg : '?';
            var cn = flight.cn ? flight.cn : '?';
            var takeoffLoc = flight.to_loc ? flight.to_loc : 'UNK';
            //var to_ts = new Date(flight.to_ts*1000);
            var landingLoc = flight.to_loc ? flight.la_loc : 'UNK';
            //var la_ts = new Date(flight.la_ts*1000);

            content += `<tr><td>${reg} (${cn})</td><td>${takeoffLoc} &#8605; ${landingLoc}<td><td><a href="${flight.id}">(+)</a></td></tr>`
        }
        content += "</table>"

        searchResults.innerHTML = content;

    } else {
        alert('nejaky problem ve vyhledavani letu #1');
    }
}
