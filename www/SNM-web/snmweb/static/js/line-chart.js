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
        var chart = nv.models.lineChart().useInteractiveGuideline(true);

        chart.xAxis
            .axisLabel("Date")
            .tickFormat(function(d) {
                return d3.time.format("%x")(new Date(d));
            });

        chart.yAxis
            .axisLabel("Runs")
            .tickFormat(d3.format(".0f"));


        function clear_diagram() {
            tab.find("tbody").empty();
            svg.empty();
        }

        function addRowApp(appName) {
            tab.find("tbody").append(
                $('<tr>')
                    .append($('<td colspan="2" class="app-name">').text(appName))
            );
        }

        function addRow(date, value) {
            tab.find("tbody").append(
                $('<tr>')
                    .append($('<td>').text(d3.time.format("%x")(new Date(date))))
                    .append($('<td>').text(value))
            );
        }

        function data(args) {
            var appData = [];
            if (args.id != "") {
                snmapi.getStat(options.stat_id, args,
                    function(r) {
                        for (var i = 0; i < r.data.length; i++) {
                            addRowApp(r.data[i].title);
                            var data = r.data[i].data;
                            var parseDate = d3.time.format("%Y-%m-%d").parse;
                            var x, y, entry;
                            for (var j = 0; j < data.length; j++) {
                                entry = data[j];
                                data[j].x = parseDate(entry.x);
                                addRow(entry.x, entry.y);
                            }

                            var d = data.sort(
                                function(a, b) {
                                    if (a.x > b.x) return 1;
                                    else return -1;
                                }
                            );

                            appData.push({values: d, key: r.data[i].title});
                        }
                    });
            }
            return appData;
        }

        function drawDiagram(args) {
            //TODO: Smooth transition between datasets, fill table with d3
            clear_diagram();
            nv.addGraph(function() {
                d3.select(svg[0])
                    .datum(data(args))
                    .transition().duration(500)
                    .call(chart);
                nv.utils.windowResize(chart.update);
                return chart;
            });
        }

        return {
            drawDiagram: drawDiagram
        };
    };
})(jQuery);
