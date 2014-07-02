/*
This is a component that allows to draw line-chart visualizations.
It depends on jQuery as it is a jQuery plugin.
It also uses nv.d3 library that uses d3.js framework.
The diagram uses div container to put svg frame in it
and another container to hold  table with values.
 */

(function($) {
    $.vizLineChart = function(svg_container, options) {
        var svg = $("<svg>").appendTo(svg_container);
        var options = $.extend({ //Default or expected options go here
            xLabel : "Date",
            yLabel : "#Runs",
            table  : svg_container.find("table"),
            stat_id: "",
            height : "400px"
            }, options);

        var tab = $(table);
        var chart = nv.models.lineChart()
        .useInteractiveGuideline(true);

        chart.xAxis
        .axisLabel(options.xLabel)
        .tickFormat(function(d) {
          return d3.time.format("%x")(new Date(d));
        });

        chart.yAxis
        .axisLabel(options.yLabel)
        .tickFormat(d3.format(".0f"))
        ;


        function clear_diagram(){
            tab.find("tbody").empty();
            svg.empty();
        }

        function addRow(date, value) {
            tab.find("tbody").append(
              $('<tr>')
                .append($('<td>').text(date))
                .append($('<td>').text(value))
            )
        }
        function draw_diagram(period) {
            function data(period) {
                var appData = [];
                snmapi.getStat(options.stat_id, {"group_by": period},
                    function(data) {
                  var dates = data["data"]["dates"];
                  var runs = data["data"]["runs"];
                  var parseDate = d3.time.format("%Y-%m-%d").parse;
                  var x, y;
                    for (var i = 0; i < dates.length; i++) {
                        x = parseDate(dates[i]);
                        y = runs[i];
                        appData.push({'x': x, 'y': y});
                        addRow(dates[i],y);
                    }
                  });

                  return [
                    {
                      values: appData,
                      key: "Application",
                      color: "#ff7f0e"
                    }
                  ];
            }
            nv.addGraph(function() {
              d3.select(svg)
              .datum(data(period))
              .transition().duration(500)
              .call(chart);
              nv.utils.windowResize(chart.update);
              return chart;
            });
        }

        return {

        };
    };
})(jQuery);