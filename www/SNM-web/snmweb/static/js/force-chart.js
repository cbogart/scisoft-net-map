function vizForceChart(container, options) {
    var options = $.extend({ //Default or expected options go here
        height  : container.height(),
        width   : container.width(),
        linkDistance  : 30, //table selector
        charge  : -1000,
        stat_id: "force_directed",  // api/stat/{stat_id},
        clickable: true
    }, options);
    var height = options.height;
    var width = options.width;
    var svg = d3.select("#chart svg")
        .attr("width", width)
        .attr("height", height);
   // Arrowhead definition from http://www.w3.org/TR/SVG/painting.html#Markers
    svg.append("defs").append("marker")
        .attr("id", "Triangle")
        .attr("viewBox", "0 0 10 10")
        .attr("refX", "10").attr("refY", "5")
        .attr("markerUnits", "userSpaceOnUse")
        .attr("markerWidth", "10") 
        .attr("markerHeight", "10") 
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M 0 0 L 10 5 L 0 10 z");
    var svglinks = svg.append("g");
    var svgnodes = svg.append("g");
    var force = d3.layout.force()
        .charge(options.charge)
        .gravity(.2)    // Makes the nodes cluster a little tighter than default of .1
        .linkDistance(options.linkDistance)
        .linkStrength(function(d) { return( Math.max(d.value.logical, d.value.static)/10.0); })
        .size([width, height]);
    var app_dict = {},
        link_dict = {},
        counter = 0,
        nodes = [],
        links = [];
    force
        .nodes(nodes)
        .links(links);
    force.on("tick", function() {
        svg.selectAll(".link")
            .attr("x1", function(d) { 
                d.len = Math.pow(Math.pow(d.source.x-d.target.x,2) + Math.pow(d.source.y-d.target.y,2), .5)
                return d.source.x; 
             })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x - (d.target.x-d.source.x)*(d.target.radius/d.len); })
            .attr("y2", function(d) { return d.target.y - (d.target.y-d.source.y)*(d.target.radius/d.len); })
            ;
        svg.selectAll('g.gnode')
            .attr("transform", function(d) {
                // Bounds here keep node centers 8 pix within edges
                return 'translate(' + [Math.max(8,Math.min(width-8,d.x)), Math.max(8,Math.min(height-8,d.y))] + ')';
        });
    });
    function loadData(id) {snmapi.getStat(options.stat_id, {"id": id},
        function(result) {
            var data = result.data,
                node, link;
            for (i in data.nodes) {
                node = data.nodes[i];
                if (!(node.id in app_dict)) {
                    if (node.id == id) node.loaded = true;
                    app_dict[node.id] = counter;
                    counter++;
                    nodes.push(node);
                }
            }

            for (i in data.links) {
                link = data.links[i];
                var s = app_dict[link.source],
                    t = app_dict[link.target],
                    st = s + ":" + t,
                    ts = t + ":" + s;
                if (!(st in link_dict)) {
                    link_dict[st] = link_dict[ts] = true;
                    links.push({
                        "source" : s,
                        "target" : t,
                        "value"  : link.value
                    });
                }
            }
            updateChart();
        });
    }

    function updateChart() {
        force.start();
        var allLinks = svglinks.selectAll(".link")
            .data(force.links())
            .enter().append("line")
            .attr("class", function(d) { if (d.value.static > 0) { return("link static-link") } else { return("link logical-link") }})
            .attr("marker-end", function(d) { if (d.value.static > 0) { return("url(#Triangle)") } else { return("") }})
            .style("stroke-width", function(d) { if (d.value.static > 0) { return(d.value.static)/4+1; } else if (d.value.logical > 0) { return(d.value.logical)/4+1; } else { return(0); }});

        var allGNodes = svgnodes.selectAll('g.gnode')
            .data(force.nodes())
            .enter()
            .append('g')
            .classed('gnode', true)
            .call(force.drag);

        var labels = allGNodes.append("a")
            .attr("xlink:href", function(d) {return d.link;})
            .append("text")
            .attr("transform", function(d) { return "translate(" + (10+Math.log(d.publications+1)*2) + ",0)"; })
            .text(function(d) { return d.name; });

        var allNodes = allGNodes.append("circle")
            .attr("class", "node")
            .classed("loaded", function(d){return d.loaded})
            .attr("r", function(d){ 
                  d.radius = (Math.log(d.publications+1)*2+5);
                  return d.radius;
             });  // 9

        if (options.clickable) {
            allNodes.on("click", function(d) {
                d.loaded = true;
                d3.select(this).classed("loaded", true);
                loadData(d.id);
            });
        }


    }


    return {
        start: function(id){loadData(id);}
    }
}
