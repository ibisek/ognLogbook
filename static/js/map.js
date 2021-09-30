
function onPageLoad() {
    var map = L.map('map'); //.setView([51.505, -0.09], 13);

	L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
		maxZoom: 18,
		attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, ' +
			'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
		id: 'mapbox/streets-v11',
		tileSize: 512,
		zoomOffset: -1
	}).addTo(map);

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

    var takeoffMarker = L.marker(latlngs[0], {icon: greenIcon}).addTo(map);
    takeoffMarker.bindPopup("<b>Take-off<b>");

    var landingMarker = L.marker(latlngs[latlngs.length-1],{icon: redIcon}).addTo(map);
    landingMarker.bindPopup("<b>Landing</b>");

}
