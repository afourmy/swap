/* global L network vis */

let layers = {
  'Open Street Map': 'http://{s}.tile.osm.org/{z}/{x}/{y}.png',
  'Google Maps': 'http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga',
  'NASA': 'http://tileserver.maptiler.com/nasa/{z}/{x}/{y}.jpg',
};

let map = L.map('map', {zoomControl: false}).setView([48, 2], 5);
let osmLayer = L.tileLayer(layers['Open Street Map']);
let currentLayer = osmLayer;
let iconSwitch = L.icon({
  iconUrl: 'static/images/optical_switch.gif',
  iconSize: [20, 20],
  iconAnchor: [9, 6],
  popupAnchor: [8, -5],
});
let colors = ['red', '#08f', '#0c0', '#f80', 'purple', 'pink', 'yellow'];
let polylines = [];
let selectedLines = [];
let linkNameToPolyline = {};
let nodes = new vis.DataSet();
let action = {
  'Transform graph': transformGraph,
  'Routing': routing,
  'Open Street Map': partial(switchLayer, 'Open Street Map'),
  'Google Maps': partial(switchLayer, 'Google Maps'),
  'NASA': partial(switchLayer, 'NASA'),
};
let lineWeight = 5;

$('#graph-transformation').on('shown.bs.modal', function() {
  graphTransformation();
});

(function() {
  map.on('click', function() {
    unselectLines();
  });
  map.addLayer(osmLayer);
  document.getElementById('file').onchange = function() {
    $('#fileform').submit();
  };

  $('.dropdown-submenu a.test').on('click', function(e) {
    $(this).next('ul').toggle();
    e.stopPropagation();
    e.preventDefault();
  });

  for (let s = 0; s < network.node.length; s++) {
    createOpticalSwitch(network.node[s]);
  }
  for (let l = 0; l < network.link.length; l++) {
    createLink(network.link[l]);
  }
})();

/**
 * Returns partial function
 * @param {function} func - any function
 * @return {function}
 */
function partial(func, ...args) {
  return function() {
    return func.apply(this, args);
  };
}

/**
 * Unselect all links (all leaflet polylines)
 */
function unselectLines() {
  for (let i = 0; i < selectedLines.length; i++) {
    selectedLines[i].setStyle({color: '#0000FF'});
  }
}

/**
 * @param {oxc} oxc - Optical switch object
 */
function createOpticalSwitch(oxc) {
  let marker = L.marker([oxc.latitude, oxc.longitude]);
  marker.bindPopup(`
    <b>Name</b>: ${oxc.name}<br>\
    <b>Longitude</b>: ${oxc.longitude}<br>\
    <b>Latitude</b>: ${oxc.latitude}<br>\
  `);
  marker.bindTooltip(oxc.name, {permanent: false});
  marker.setIcon(iconSwitch);
  marker.addTo(map);
}

/**
 * @param {link} link - A link object
 */
function createLink(link) {
  let pointA = new L.LatLng(
    link.source.latitude,
    link.source.longitude
  );
  let pointB = new L.LatLng(
    link.destination.latitude,
    link.destination.longitude
  );
  let pointList = [pointA, pointB];
  let polyline = new L.Polyline(pointList, {
    color: link.subtype === 'fiber' ? '#0000FF' : '#333333',
    weight: 3, opacity: 1, smoothFactor: 1,
  });
  polyline.addTo(map);
  polylines.push(polyline);
  if (link.subtype === 'fiber') {
    linkNameToPolyline[link.name] = polyline;
    polyline.bindPopup('');
  } else {
    polyline.on('click', function() {
      unselectLines();
      $.ajax({
        type: 'POST',
        url: `/path_${link.name}`,
        dataType: 'json',
        success: function(data) {
          for (let i = 0; i < data.length; i++) {
            polyline = linkNameToPolyline[data[i]];
            selectedLines.push(polyline);
            polyline.setStyle({color: 'red'});
          }
        },
      });
    });
  }
}

/**
 * @param {layer} layer - Changes the tile layer
 */
function switchLayer(layer) {
  map.removeLayer(currentLayer);
  currentLayer = L.tileLayer(layers[layer]);
  map.addLayer(currentLayer);
  $('.dropdown-submenu a.test').next('ul').toggle();
  alertify.notify(`Switch to a new tile layer: ${layer}.`, 'success', 5);
}

/**
 * Use linear programming to fid the shortest path for all traffic links.
 */
function routing() {
  $.ajax({
    type: 'POST',
    url: '/routing',
    dataType: 'json',
    success: function() {
      $('#action-button').text('Transform graph');
    },
  });
  alertify.notify(
    'Routing successful: click on a black link to see its path.',
    'success',
    5
  );
}

/**
 * Open the bootstrap modal containing the traffic adjacency graph.
 */
function transformGraph() {
  $('#graph-transformation').modal('show');
}

(function($, window) {
  $.fn.contextMenu = function(settings) {
    return this.each(function() {
      $(this).on('contextmenu', function(e) {
        if (e.ctrlKey) {
          return;
        }
        let $menu = $(settings.menuSelector)
          .data('invokedOn', $(e.target))
          .show()
          .css({
            position: 'absolute',
            left: getMenuPosition(e.clientX, 'width', 'scrollLeft'),
            top: getMenuPosition(e.clientY, 'height', 'scrollTop'),
          })
          .off('click')
          .on('click', 'a', function(e) {
            $menu.hide();
            let $invokedOn = $menu.data('invokedOn');
            let $selectedMenu = $(e.target);
            settings.menuSelected.call(this, $invokedOn, $selectedMenu);
          });
        return false;
      });
      $('body').click(function() {
        $(settings.menuSelector).hide();
      });
    });

    /**
    * Get menu position.
    * @param {mouse} mouse
    * @param {direction} direction
    * @param {scrollDir} scrollDir
    * @return {position}
    */
    function getMenuPosition(mouse, direction, scrollDir) {
      let win = $(window)[direction]();
      let scroll = $(window)[scrollDir]();
      let menu = $(settings.menuSelector)[direction]();
      let position = mouse + scroll;
      if (mouse + menu > win && menu < mouse) {
        position -= menu;
      }
      return position;
    }
  };
})(jQuery, window);

/**
 * Add a polyline to the map.
 * @param {lineSegment} lineSegment
 */
function addPolyline(lineSegment) {
  let linesOnSegment = lineSegment.properties.lines;
  let segmentWidth = linesOnSegment.length * (lineWeight + 1);
  for (let j = 0; j < linesOnSegment.length; j++) {
    L.polyline(L.GeoJSON.coordsToLatLngs(
      lineSegment.geometry.coordinates, 0),
      {
        color: colors[linesOnSegment[j]],
        weight: lineWeight,
        opacity: 1,
        offset: j * (lineWeight + 1) - (segmentWidth/2) + ((lineWeight + 1)/2),
      }
    ).addTo(map);
  }
}

/**
 * Call the wavelength assignment algorithm and display result.
 * @param {algorithm} algorithm - Linear programming or Largest Degree First.
 */
function wavelengthAssignment(algorithm) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/wavelength_assignment/${algorithm}`,
    dataType: 'json',
    success: function(results) {
      $('#score').text(results.lambda + ' wavelengths');
      for (let i = 0; i < polylines.length; i++) {
        map.removeLayer(polylines[i]);
      }
      for (const [key, value] of Object.entries(results.colors)) {
        nodes.update({id: key, color: colors[value]});
        }
      for (const [key, value] of Object.entries(results.fiber_colors)) {
        let geoJson = {
          'type': 'FeatureCollection',
          'features': [
            {'type': 'Feature', 'properties': {'lines': value},
            'geometry': {'type': 'LineString', 'coordinates': [
              [...results.coords[key][0]], [...results.coords[key][1]],
            ]}}],
        };
        geoJson.features.map(addPolyline);
      }
      alertify.notify('Transformation successful', 'success', 5);
    },
  });
}

/**
 * Transforms graph with vis.js.
 */
function graphTransformation() {
  $.ajax({
    type: 'POST',
    url: '/graph_transformation',
    dataType: 'json',
    success: function(graph) {
      $('#graph-transformation').modal('show');
      nodes.add(graph.nodes);
      let edges = new vis.DataSet(graph.links);
      const container = $('#network');
      let data = {nodes: nodes, edges: edges};
      let options = {};
      new vis.Network(container[0], data, options);
    },
  });
}

$('body').contextMenu({
  menuSelector: '#contextMenu',
  menuSelected: function(invokedOn, selectedMenu) {
    let row = selectedMenu.text();
    action[row]();
  },
});
