function initializeMap(vessels) {
    var map = L.map('map').setView([51.9225, 4.4792], 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    vessels.forEach(function(vessel) {
        if (vessel.track.length > 0) {
            L.polyline(vessel.track, {color: getRandomColor()}).addTo(map);
            L.marker(vessel.track[0]).addTo(map).bindPopup(`MMSI: ${vessel.mmsi} (Start)`);
            L.marker(vessel.track[vessel.track.length - 1]).addTo(map).bindPopup(`MMSI: ${vessel.mmsi} (End)`);
        }
    });

    function getRandomColor() {
        var letters = '0123456789ABCDEF';
        var color = '#';
        for (var i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }
}