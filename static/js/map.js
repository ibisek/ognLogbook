var map;
var searchInProgress = false;
var searchResults = document.getElementById("searchResults");
var colors = ['Green', 'MidnightBlue', 'Sienna', 'Gray', 'Plum', 'Turquoise', 'Black', 'Aqua', 'Chartreuse', 'BlueViolet', 'CornflowerBlue', 'DarkMagenta' , 'DeepPink'];
var colorIndex = 0;

function addFlightToMap(flightSegments, skipSegments, lineColor='red') {
    var allPoints = new Array();
    for (var i = 0; i < flightSegments.length; i++) {
        L.polyline(flightSegments[i], {color: 'white', weight: 4}).addTo(map);
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

function onPageLoad(flightId) {
    map = L.map('map'); //.setView([51.505, -0.09], 13);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

	L.control.scale().addTo(map);

    addFlightToMap(flightSegments, skipSegments);
    listEncounters(flightId);
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
    if (resp.readyState === 4) {
        if (resp.status === 200) {
            var content = "";
            var flights = JSON.parse(resp.responseText);
            for (const flight of flights) {
                var reg = flight.reg ? flight.reg : '?';
                var cn = flight.cn ? flight.cn : '?';
                console.log("XXX:" + flight.to_loc);
                var takeoffLoc = flight.to_loc ? flight.to_loc : '?';
                var to_ts = new Date(flight.to_ts*1000).toLocaleTimeString('en-US', { hour: 'numeric', hour12: false, minute: 'numeric' });
                var landingLoc = flight.la_loc ? flight.la_loc : '?';
                var la_ts = new Date(flight.la_ts*1000).toLocaleTimeString('en-US', { hour: 'numeric', hour12: false, minute: 'numeric' });;

                content += `<div id='SR${flight.id}' class="searchResult" onClick="addFoundFlightToMap(${flight.id});"><span id="FL${flight.id}"></span><div class='flex_item'>${reg} (${cn}) ${takeoffLoc} ${to_ts} &#8605; ${landingLoc} ${la_ts}</div></div>`
            }

            searchResults.innerHTML = content;
        } else if (resp.status === 429) {
            alert('Reached request rate limit. Try again in a minute.');
        }

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
        if (resp.readyState === 4) {
            if (resp.status === 200) {
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

            } else if (resp.status === 429) {
                alert('Reached request rate limit. Try again in a minute.');
            }

        } else {
            alert('No data..?');
        }
    };

    req.onerror = (e) => {
      console.error(req.statusText);
      alert('Nejaky problem v pridavani letu na mapu.');
    };
    req.send(null);

}

var encountersMarkers = [];

function listEncounters(flightId) {
    if (encountersMarkers.length > 0) return; // already loaded

    var query = `/api/enc/${flightId}`;

    const req = new XMLHttpRequest();
    req.open("GET", query, true);

    req.onload = (e) => {
        var resp = e.currentTarget;
        if (resp.readyState === 4) {
            if (resp.status === 200) {
                var encounters = JSON.parse(resp.responseText);
                var encLen = encounters.length;
                if(encLen == 0) return;

                for (var i = 0; i < encLen; i++) {
                    var enc = encounters[i];

                    var encMarker = L.marker([enc.other_lat, enc.other_lon]).addTo(map);
                    var registration = (enc.registration != null ? `<b>${enc.registration}</b>`: '?');
                    var cn = (enc.registration != null ? ` (${enc.cn})` : '');
                    var aircraftType = (enc.aircraft_type != null ? `<br>${enc.aircraft_type}` : '');

                    var altDiff = enc.alt - enc.other_alt;
                    var text = (altDiff > 0 ? "below" : "above");

                    var butId = `encBut${i}`;
                    var button = (enc.other_flight_id != null ? `<br><br><button onclick='addFoundFlightToMap(${enc.other_flight_id}); document.getElementById("${butId}").style.display="none";'>add flight to map</button>` : '');

                    encMarker.bindPopup(`${registration}${cn}${aircraftType}<br>${enc.other_alt.toFixed(0)}m AMSL<br>${enc.dist}m apart & ${Math.abs(altDiff.toFixed(0))}m ${text}${button}`);

                    encountersMarkers.push(encMarker);
                }

            } else if (resp.status === 429) {
                alert('Reached request rate limit. Try again in a minute.');
            }

        } else {
            alert('No data..?');
        }
    };

    req.onerror = (e) => {
      console.error(req.statusText);
      alert('Nejaky problem v listu encounters.');
    };
    req.send(null);

}

