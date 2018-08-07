function createOpticalSwitch(oxc) {
  var marker = L.marker([oxc.latitude, oxc.longitude]);
  marker.bindPopup(`
    <b>Name</b>: ${oxc.name}<br>\
    <b>Longitude</b>: ${oxc.longitude}<br>\
    <b>Latitude</b>: ${oxc.latitude}<br>\
  `);
  marker.bindTooltip(oxc.name, {permanent: false, });
  marker.setIcon(icon_switch), 
  marker.addTo(map);
}

function createLink(link) {
  var pointA = new L.LatLng(link.source.latitude, link.source.longitude);
  var pointB = new L.LatLng(link.destination.latitude, link.destination.longitude);
  var pointList = [pointA, pointB];
  var polyline = new L.Polyline(pointList, {
    color: link.subtype === 'fiber' ? '#0000FF' : '#333333',
    weight: 3, opacity: 1, smoothFactor: 1 
  });
  polyline.addTo(map);
  polylines.push(polyline);
  if (link.subtype == 'fiber') {
    link_name_to_polyline[link.name] = polyline;
    polyline.bindPopup("");
  } else {
    polyline.on('click', function() {
      unselectLines();
      $.ajax({
        type: "POST",
        url: `/path_${link.name}`,
        dataType: "json",
        success: function(data){
          for (i = 0; i < data.length; i++) {
            polyline = link_name_to_polyline[data[i]];
            selectedLines.push(polyline);
            polyline.setStyle({color: 'red'});
          }
        }
      });
    });
  }
}

(function() {
  for (var s = 0; s < network.node.length; s++) {
    createOpticalSwitch(network.node[s]);
  }
  for (var l = 0; l < network.link.length; l++) {
    createLink(network.link[l]);
  }
})();


var layers = {
  'Open Street Map': 'http://{s}.tile.osm.org/{z}/{x}/{y}.png',
  'Google Maps': 'http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga',
  'NASA': 'http://tileserver.maptiler.com/nasa/{z}/{x}/{y}.jpg'
};

(function ($, window) {
  $.fn.contextMenu = function (settings) {
    return this.each(function () {
      $(this).on('contextmenu', function (e) {
        if (e.ctrlKey) return;
        var $menu = $(settings.menuSelector)
          .data('invokedOn', $(e.target))
          .show()
          .css({
            position: 'absolute',
            left: getMenuPosition(e.clientX, 'width', 'scrollLeft'),
            top: getMenuPosition(e.clientY, 'height', 'scrollTop')
          })
          .off('click')
          .on('click', 'a', function (e) {
            $menu.hide();
            var $invokedOn = $menu.data('invokedOn');
            var $selectedMenu = $(e.target);
            settings.menuSelected.call(this, $invokedOn, $selectedMenu);
          });
        return false;
      });
      $('body').click(function () {
        $(settings.menuSelector).hide();
      });
    });

    function getMenuPosition(mouse, direction, scrollDir) {
      var win = $(window)[direction](),
          scroll = $(window)[scrollDir](),
          menu = $(settings.menuSelector)[direction](),
          position = mouse + scroll;
      if (mouse + menu > win && menu < mouse) 
        position -= menu;
        return position;
    }
  };
})(jQuery, window);

function switchLayer(layer) {
  map.removeLayer(current_layer);
  current_layer = L.tileLayer(layers[layer]);
  map.addLayer(current_layer);
}

function routing() {
  $.ajax({
    type: "POST",
    url: "/routing",
    dataType: "json",
    success: function(graph) {
      $("#action-button").text('Transform graph');
    }
  });
}

function transformGraph() {
  $('#graph-transformation').modal('show');
}

document.getElementById("file").onchange = function() {
  $("#fileform").submit();
};

var colors = ['red', '#08f', '#0c0', '#f80', 'purple', 'pink', 'yellow'];
function wavelengthAssignment(algorithm) {
  $.ajax({
    type: "POST",
    url: `/wavelength_assignment/${algorithm}`,
    dataType: "json",
    success: function(results) {
      $("#score").text(results['lambda'] + ' wavelengths');
      for (var i = 0; i < polylines.length; i++) {
        map.removeLayer(polylines[i]);
      }
      for (const [key, value] of Object.entries(results['colors'])) {
        nodes.update({id: key, color: colors[value]});
        }
      for (const [key, value] of Object.entries(results['fiber_colors'])) {
        var geoJson = {
          "type": "FeatureCollection",
          "features": [
            {"type": "Feature", "properties": {"lines": value},
            "geometry": {"type": "LineString", "coordinates": [
              [...results['coords'][key][0]], [...results['coords'][key][1]],
            ]}}]
        };
        var lineWeight = 5;
        var lineSegment, linesOnSegment, segmentCoords, segmentWidth;
        geoJson.features.forEach(function(lineSegment) {
          segmentCoords = 
          linesOnSegment = lineSegment.properties.lines;
          segmentWidth = linesOnSegment.length * (lineWeight + 1);
          for(var j = 0; j < linesOnSegment.length; j++) {
            L.polyline(L.GeoJSON.coordsToLatLngs(
              lineSegment.geometry.coordinates, 0), 
              {
                color: colors[linesOnSegment[j]],
                weight: lineWeight,
                opacity: 1,
                offset: j * (lineWeight + 1) - (segmentWidth / 2) + ((lineWeight + 1) / 2)
              }
            ).addTo(map);
          }
        });
      }
    }
  });
}

var nodes = new vis.DataSet();
function graphTransformation(algorithm){
  $.ajax({
    type: "POST",
    url: "/graph_transformation",
    dataType: "json",
    success: function(graph){
      $('#graph-transformation').modal('show');
      nodes.add(graph['nodes']);
      var edges = new vis.DataSet(graph['links']);
      const container = $("#network");
      var data = {nodes: nodes, edges: edges};
      var options = {};
      const network = new vis.Network(container[0], data, options);
    }
  });
}

$('#graph-transformation').on('shown.bs.modal', function() {
  graphTransformation();
});

function partial(func) {
  var args = Array.prototype.slice.call(arguments, 1);
  return function() {
    var allArguments = args.concat(Array.prototype.slice.call(arguments));
    return func.apply(this, allArguments);
  };
}

var action = {
  'Transform graph': transformGraph,
  'Routing': routing,
  'Open Street Map': partial(switchLayer, 'Open Street Map'),
  'Google Maps': partial(switchLayer, 'Google Maps'),
  'NASA': partial(switchLayer, 'NASA')
}

$('.dropdown-submenu a.test').on("click", function(e){
  $(this).next('ul').toggle();
  e.stopPropagation();
  e.preventDefault();
});

$('body').contextMenu({
  menuSelector: '#contextMenu',
  menuSelected: function (invokedOn, selectedMenu) {
    var row = selectedMenu.text();
    action[row]();
  }
});