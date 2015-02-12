function vizForceChart(container, options) {
    var options = $.extend({ //Default or expected options go here
        height  : container.height(),
        width   : container.width(),
        linkDistance  : 70, //table selector
        scimapID: "",
        charge  : -3000,
        stat_id: "force_directed",  // api/stat/{stat_id},
        clickable: true
    }, options);
    var height = options.height;
    var width = options.width;
    var focusid = "";
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
        sqrt_max_uses = 0,
        user_vector = {"fftw3": 0.8},
        links = [];
    force
        .nodes(nodes)
        .links(links);
    force.on("tick", function() {
        svg.selectAll('g.gnode').each(function (d) {
            if (d.x < 8) { d.x = 8; }
            if (d.x > width-8) { d.x = width-8; }
            if (d.y < 8) { d.y = 8; }
            if (d.y > height-8) { d.y = height-8; }
        });
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
                return 'translate(' + [d.x,d.y] + ')';  
        });
    });
    function loadUserInfo(user) { 
      //setTimeout(function() {
        snmapi.getStat("user_vector", {"id": options.scimapID},
            function(result) {
               user_vector = result.data;
               //updateChart();
            });
      //}, 2000);
    }
    function loadData(id) {snmapi.getStat(options.stat_id, {"id": id},
        function(result) {
            focusid = id;
            var data = result.data,
                node, link;
            var max_uses = 0;
            var allnodes = []; var alllinks = [];
            for (i in data.nodes) {
                node = data.nodes[i];
                if (!(node.id in app_dict)) {
                    if (node.id == id) {
                        node.loaded = true;
                        node.topTen = true;
                        node.focus_co_uses = node.uses;
                    } else {
                        node.topTen = false;
                        node.focus_co_uses = 0;
                    }
                    app_dict[node.id] = counter;
                    counter++;
                    allnodes.push(node);
                    max_uses = Math.max(max_uses, node.uses);
                }
            }
            sqrt_max_uses = Math.sqrt(max_uses);

            for (i in data.links) {
                link = data.links[i];
                var s = app_dict[link.source],
                    t = app_dict[link.target],
                    st = s + ":" + t,
                    ts = t + ":" + s;
                if (!(st in link_dict)) {
                    link_dict[st] = link_dict[ts] = true;
                    alllinks.push({
                        "source" : s,
                        "target" : t,
                        "value"  : link.value,
                        "unscaled"  : link.unscaled
                    });
                    if (link.source == id) {
                        allnodes[t].focus_co_uses += link.unscaled.static + link.unscaled.logical;
                    } else if (link.target == id) {
                        allnodes[s].focus_co_uses += link.unscaled.static + link.unscaled.logical;
                    } 
                }
            }
            
            // Find the 10 nodes with the biggest mass (not percentage) pie slices, and mark them as "topTen"
            // We'll just display those in the graph, to keep it simpler.

            var sortedNodes = [];
            for (n in allnodes) {
                // Could divide by allnodes[n].uses if we wanted biggest *percentage* users.  It gives a very
                // different graph, which is possibly more useful for some purposes; but it's harder to understand
                // in relationship to the bar graph, so I'm not including it for now.  Future work.
                sortedNodes.push({"id": n, "pct": allnodes[n].focus_co_uses}); //*1.0/allnodes[n].uses*1.0});
            }
            sortedNodes.sort(function(a,b) { return b["pct"]-a["pct"]; });
            for (n = 0; n< Math.min(10,sortedNodes.length); n++) {
                allnodes[sortedNodes[n].id].topTen = true;
            }
            for (n in allnodes) {
                if (allnodes[n].topTen) {
                    nodes.push(allnodes[n]);
                    allnodes[n].newid = nodes.length - 1;
                }
            }
            for (i in alllinks) {
                var link = alllinks[i];
                if (allnodes[link.source].topTen && allnodes[link.target].topTen) {
                    link.source = allnodes[link.source].newid;
                    link.target = allnodes[link.target].newid;
                    links.push(link);
                }
            }
                
            
            updateChart();
        });
    }

    function updateChart() {
        force.start();
        var big = 25, small=4;
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
            .call(force.drag)
            .append("a").attr("xlink:href", function(d) { return d.link; });

        var labels = allGNodes //.append("a")
            //.attr("xlink:href", function(d) {return d.link;})
            .append("text")
            .attr("transform", function(d) { return "translate(" + (10 + small +big*(Math.sqrt(d.uses)/sqrt_max_uses)) + ",0)"; })
            .text(function(d) { return d.name; });

        var allNodes = allGNodes.append("circle")
            .attr("class", "node")
            .classed("loaded", function(d){return d.loaded})
            .attr("r", function(d){ 
                  d.radius = big*(Math.sqrt(d.uses)/sqrt_max_uses)+small;
                  return d.radius;
             });
             //.append("a").attr("xlink:href", function(d) { return d.link; });

        allGNodes
             .filter(function(d) { return d.id == focusid; })
             .append("circle").attr("x",0).attr("y",0).attr("r",function(d) { return d.radius})
             .classed("focusnode-color", true);

        var allPies = allGNodes
             .filter(function(d) { return d.id != focusid; })
             .append("path")
             .attr("d", function (d) { 
                         var angle = 6.28 * d.focus_co_uses / d.uses;
                         return d3.svg.arc()
                          .outerRadius(d.radius).innerRadius(0)
                          .startAngle(0.0)
                          .endAngle(angle)(); })
             .attr("class", function(d) { if (d.id == focusid) { return "focusnode-color"; } else { return "co-use-color"}})

        var highlightMe = allGNodes.append("circle")
            .attr("stroke-width", function(d) { return 10*(user_vector[d.name] || 0); })
            .attr("stroke", "yellow")
            .attr("opacity", ".3")
            .attr("fill", "none")
            .attr("r", function(d){ 
                  d.radius = big*(Math.sqrt(d.uses)/sqrt_max_uses)+small+1; 
                  return d.radius + (user_vector[d.name] || 0);
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
        start: function(id){loadUserInfo(); loadData(id);}
    }
}
