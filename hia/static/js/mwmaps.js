/**
 * @author: theo
 */

var overlays = new Set();
var baseMaps;
var overlayMaps;

var storage = sessionStorage; // or localStorage?

function addOverlay(e) {
	overlays.add(e.name);
	storage.setItem('overlays', JSON.stringify(Array.from(overlays)));
}

function removeOverlay(e) {
	overlays.delete(e.name);
	storage.setItem('overlays', JSON.stringify(Array.from(overlays)));
}

function changeBaseLayer(e) {
	storage.setItem("baselayer", e.name);
}

function restoreMap(map) {
	succes = false;
	var items = storage.getItem('overlays');
	if (items) {
		overlays = new Set(JSON.parse(items));
		overlays.forEach(function(item) {
			overlayMaps[item].addTo(map);
			succes = true;
		});
	}
	else {
		overlays = new Set();
	}
	var name = storage.getItem('baselayer');
	if (name) {
		baseMaps[name].addTo(map);
		succes = true;
	}
	return succes;
}

function saveBounds(map) {
	const b = map.getBounds()
	storage.setItem('bounds',b.toBBoxString());

	// calculate screen resolution in pixels per meter
	const dpm = 96 * window.devicePixelRatio / 0.0254;

	// Size of window
	const size = map.getSize();
	const width = size.x / dpm;
	const height = size.y / dpm;
	
	// get dimension of map in meters
	const dx1 = map.distance(b.getNorthWest(), b.getNorthEast());
	const dx2 = map.distance(b.getSouthWest(), b.getSouthEast());
	const dy1 = map.distance(b.getNorthWest(), b.getSouthWest());
	const dy2 = map.distance(b.getNorthEast(), b.getSouthEast());

	// average scale
	const scale = ((dx1+dx2)/2/width + (dy1+dy2)/2/height)/2;
	//	console.log(`Scale = 1:${scale}`);
	
	// save rounded scale to storage
	const rounded = Number(scale.toPrecision(1));
	storage.setItem('scale',`1:${rounded}`);
}

function restoreBounds(map) {
	var b = storage.getItem('bounds');
	if (b) {
		corners = b.split(',').map(Number);
		map.fitBounds([[corners[1],corners[0]],[corners[3],corners[2]]]);
		return true;
	}
	return false;
}

var redBullet = L.icon({
    iconUrl: '/static/red_marker16.png',
    iconSize: [12, 12],
    iconAnchor: [6,6],
    popupAnchor: [0, 0],
});

var theMap = null;
var markers = []; // Should be associative array: {} ??

function addMarkers(map,zoom) {
	$.getJSON('/locs', function(data) {
		bounds = new L.LatLngBounds();
		$.each(data, function(key,val) {
			marker = L.marker([val.lat, val.lon],{title:val.name, icon: redBullet});
			markers[val.id] = marker;
			marker.bindPopup("Loading...",{maxWidth: "auto"});
			marker.bindTooltip(val.name,{permanent:true,className:"label",opacity:0.7,direction:"top",offset:[0,-10]});
			marker.on("click", function(e) {
				var popup = e.target.getPopup();
			    $.get("/pop/"+val.id)
				    .done(function(data) {
				        popup.setContent(data);
				        popup.update();
				    })
				    .fail(function() {
				    	popup.closePopup();
				    });
			});
			marker.addTo(map);
			bounds.extend(marker.getLatLng());
		});
		if (zoom) { 
			map.fitBounds(bounds);
		}
	});
}

function addMarkerGroup(map) {
	$.getJSON('/locs', function(data) {
		var markers = L.markerClusterGroup(); 
		$.each(data, function(key,val) {
			markers.addLayer(L.marker([val.lat, val.lon]));
		});
		map.addLayer(markers);
	});
}

var hilite = null;
var hiliteVisible = false;

function showHilite(marker) {
	
	if (marker == null || theMap == null)
		return;
	
	if (!hilite) {
		hilite= new L.circleMarker(marker.getLatLng(),{radius:20,color:"green"})
			.addTo(theMap);
	}
	else {
		hilite.setLatLng(marker.getLatLng());
		if (!hiliteVisible) {
			theMap.addLayer(hilite);
		}
	}
	hiliteVisible = true;
}

function hideHilite() {
	if (hiliteVisible) {
		hilite.remove();
		hiliteVisible = false;
	}
}

var panTimeoutId = undefined;

function panToMarker(marker) {
	theMap.panTo(marker.getLatLng());
}

function clearPanTimer() {
	window.clearTimeout(panTimeoutId);
	panTimeoutId = undefined;
}

function showMarker(m) {
	marker = markers[m];
	showHilite(marker);
	panTimeoutId = window.setTimeout(panToMarker,1000,marker);
}

function hideMarker(m) {
	hideHilite();
	clearPanTimer();
}

L.Control.LabelControl = L.Control.extend({
    onAdd: function(map) {
    	var container = L.DomUtil.create('div','leaflet-bar leaflet-control leaflet-control-custom');
        var img = L.DomUtil.create('a','fa fa-lg fa-tags',container);
    	img.title = 'Toggle labels';
        img.setAttribute('role','button');
        img.setAttribute('aria-label','Toggle Labels');

    	L.DomEvent.on(container, 'click', function(e) {
        	toggleLabels();
            L.DomEvent.preventDefault();
            L.DomEvent.stopPropagation();
        });
        
        return container;
    },

    onRemove: function(map) {
        // Nothing to do here
    },
    
});

L.control.labelcontrol = function(opts) {
    return new L.Control.LabelControl(opts);
}

var labelsShown = true;

function showLabels() {
	if (!labelsShown) {
		if (markers) {
			markers.forEach(function(marker){
				marker.openTooltip();
			});
		} 
		labelsShown = true;
	}
}

function hideLabels() {
	if (labelsShown) {
		if (markers) {
			markers.forEach(function(marker){
				marker.closeTooltip();
			}); 
		} 
		labelsShown = false;
	}
}

function toggleLabels() {
	if (labelsShown) {
		hideLabels();
	}
	else {
		showLabels();
	}
}

/**
 * Initializes leaflet map
 * @param div where map will be placed
 * @options initial centerpoint and zoomlevel
 * @returns the map
 */
function initMap(div,options) {
	var osm = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
		maxZoom: 19,
 		attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
	});
	
	var roads = L.gridLayer.googleMutant({
	    type: 'roadmap' // valid values are 'roadmap', 'satellite', 'terrain' and 'hybrid'
	});

	var satellite = L.gridLayer.googleMutant({
	    type: 'satellite' // valid values are 'roadmap', 'satellite', 'terrain' and 'hybrid'
	});
	
	var topo = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
		attribution: 'Tiles &copy; Esri'
	});
	
	var imagery = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
		attribution: 'Tiles &copy; Esri'
	});
	
	var bodemkaart = L.tileLayer.wms('http://geodata.nationaalgeoregister.nl/bodemkaart50000/wms', {
		layers: 'bodemkaart50000',
		format: 'image/png',
		opacity: 0.4
	});

	var ahn35 = L.esri.imageMapLayer({
		url: 'https://ahn.arcgisonline.nl/arcgis/rest/services/Hoogtebestand/AHN3_5m/ImageServer',
		opacity: 0.5})
		.bindPopup(function(err, results, response){
			var value = results.pixel.properties.value;
			return (value) ? 'Maaiveldhoogte: ' + value : false;
		});
	
	var ahn3Legend = L.wmsLegend({
		position:'bottomright', 
		title:'Maaiveld<br>(m tov NAP)', 
		uri:'http://maps.acaciadata.com/geoserver/Molenwaard/wms?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&WIDTH=20&HEIGHT=20&LAYER=Molenwaard:ahn3filledMerc'
	});
	
	var map = L.map(div,options);

 	baseMaps = {'Openstreetmap': osm, 'Google wegenkaart': roads, 'Google satelliet': satellite, 'ESRI wegenkaart': topo, 'ESRI satelliet': imagery};
	overlayMaps = {'AHN3 maaiveld': ahn35, 'Bodemkaart': bodemkaart };
	L.control.layers(baseMaps, overlayMaps).addTo(map);
	
	if (!restoreMap(map)) {
		// use default map
		osm.addTo(map);
	}
	
	if(restoreBounds(map)) {
		// add markers, but don't change extent
		addMarkers(map,false);
	}
	else {
		// add markers and zoom to extent
		addMarkers(map,true);
	}

	var control = L.control.labelcontrol({ position: 'topleft' }).addTo(map);
	var scale = L.control.scale({position: 'bottomleft', imperial: false}).addTo(map);
	
	map.on('baselayerchange',function(e){changeBaseLayer(e);});
 	map.on('overlayadd',function(e){addOverlay(e);});
 	map.on('overlayremove',function(e){removeOverlay(e);});
 	map.on('zoomend',function(){saveBounds(map);});
 	map.on('moveend',function(){saveBounds(map);});
 	
 	return theMap = map;

}
