/*
 This is a component that allows to draw line-chart visualizations.
 It depends on jQuery as it is a jQuery plugin.
 It also uses nv.d3 library that uses d3.js framework.
 The diagram uses div container to put svg frame in it
 and another container to hold  table with values.
 */

(function($) {
    $.vizLineChart = function(svg_selector, options) {
        var svg = $(svg_selector);
        var options = $.extend({ //Default or expected options go here
            xLabel : "",
            yLabel : "",
            table  : "", //table selector
            stat_id: ""  // api/stat/{stat_id}
        }, options);

        var tab = $(options.table);
        var chart = nv.models.lineChart()
                .useInteractiveGuideline(true)
            ;

        chart.xAxis
            .axisLabel("Date")
            .tickFormat(function(d) {
                return d3.time.format("%x")(new Date(d));
            });

        chart.yAxis
            .axisLabel("Runs")
            .tickFormat(d3.format(".0f"))
        ;


        function clear_diagram(){
            tab.find("tbody").empty();
            svg.empty();
        }

        function addRow(date, value) {
            tab.find("tbody").append(
                $('<tr>')
                    .append($('<td>').text(d3.time.format("%x")(new Date(date))))
                    .append($('<td>').text(value))
            )
        }
        function data(args) {
            var appData = [];
            snmapi.getStat(options.stat_id, args,
                function(r) {
                    var data = r.data[0].data;
                    var parseDate = d3.time.format("%Y-%m-%d").parse;
                    var x, y, entry;
                    for (var i = 0; i < data.length; i++) {
                        entry = data[i];
                        data[i].x = parseDate(entry.x);
                        addRow(entry.x, entry.y);
                    }

                    var d = data.sort(
                        function(a, b){
                            if (a.x > b.x) return 1;
                            else return -1;
                        }
                    );
                    appData = [{values: d , key: r.data[0].id,  color: "#ff7f0e"}];
                });
            return appData;
        }

        function drawDiagram(args) {
            //TODO: Smooth transition between datasets, fill table with d3
            clear_diagram();
            nv.addGraph(function() {

                d3.select(svg[0])
                    .datum(data(args))
                    .transition().duration(500)
                    .call(chart)
                ;
                nv.utils.windowResize(chart.update);
                return chart;
            });
        }

        return {
            drawDiagram: drawDiagram
        };
    };
})(jQuery);