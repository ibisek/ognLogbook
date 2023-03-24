
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
