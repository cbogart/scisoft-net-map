function vizForceChart(container) {
    var height = container.height();
    var width = container.width();
    var svg = d3.select("#chart svg")
        .attr("width", container.width())
        .attr("height", container.height());
    var force = d3.layout.force()
        .charge(-220)
        .linkDistance(90)
        .linkStrength(1)
        .size([width, height]);
    var app_dict = {},
        counter = 0,
        nodes = [],
        links = [];
    force
        .nodes(nodes)
        .links(links);
    force.on("tick", function() {
        svg.selectAll(".link").attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });
        svg.selectAll('g.gnode').attr("transform", function(d) {
            return 'translate(' + [d.x, d.y] + ')';
        });
    });
    function loadData(id) {snmapi.getStat('force_directed', {"id": id},
        function(result) {
            var data = result.data,
                node, link;
            for (i in data.nodes) {
                node = data.nodes[i];
                if (!(node.id in app_dict)) {
                    app_dict[node.id] = counter;
                    counter++;
                    nodes.push(node);
                }
            }
            console.log(nodes.length, nodes);
            // The link could be added twice. Should check here if a link already exists
            for (i in data.links) {
                link = data.links[i];
                links.push({
                    "source" : app_dict[link.source],
                    "target" : app_dict[link.target],
                    "value"  : link.value
                });
            }
            console.log(links.length, links);
            console.log(app_dict.length, app_dict);

            updateChart();
        });
    }

    function updateChart() {
        force.start();

        var allLinks = svg.selectAll(".link")
            .data(force.links())
            .enter().append("line")
            .attr("class", "link")
            .style("stroke-width",1);

        var allGNodes = svg.selectAll('g.gnode')
            .data(force.nodes())
            .enter()
            .append('g')
            .classed('gnode', true);

        var allNodes = allGNodes.append("circle")
            .attr("class", "node")
            .attr("r", 9)
            .on("click", function(d) {
                loadData(d.id);
            });

        var labels = allGNodes.append("text")
            .attr("transform", "translate(10,0)")
            .text(function(d) { return d.name; });

    }


    return {
        start: function(id){loadData(id);}
    }
}