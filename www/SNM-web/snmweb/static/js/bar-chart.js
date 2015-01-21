function vizBarChart(container, options) {
    var options = $.extend({ //Default or expected options go here
        height  : container.height(),
        width   : container.width(),
        scimapID: "",
        focusid : "0",
        stat_id: "force_directed",  // api/stat/{stat_id},
        clickable: true
    }, options);
    var height = options.height;
    var width = options.width;
    var focusid = options.focusid;
    var focusnode = {};
    var focus = "focus";
    var svg = d3.select("#barchart svg")
        .attr("width", width)
        .attr("height", height);
    var mainbartitle = svg.append("text")
        .attr("class", "bartitle")
        .text("Out of _ runs of _");
    var inbartitle = svg.append("text")
        .attr("class", "barsubtitle")
        .text("Packages that depend on _");
    var outbartitle = svg.append("text")
        .attr("class", "barsubtitle")
        .text("Packages that _ depends on ");
    var logicbartitle = svg.append("text")
        .attr("class", "barsubtitle")
        .text("Packages were used with _");
    function setLabels(focusname) {
        mainbartitle.text("Out of " + focusnode.uses + " runs of "+ focusname);
        inbartitle.text("Packages that depend on " + focusname);
        outbartitle.text("Packages that " + focusname + " depends on");
        logicbartitle.text("Packages used along with " + focusname);
    }    
    var svginbars = svg.append("g")
    var svgoutbars = svg.append("g")
    var svglogicbars = svg.append("g")
    var inbars = [], outbars = [], logicbars = [];
    var app_dict = {},
        link_dict = {},
        counter = 0,
        nodes = [],
        user_vector = {"fftw3": 0.8},
        links = [];
    function loadUserInfo(user) { 
        snmapi.getStat("user_vector", {"id": options.scimapID},
            function(result) {
               user_vector = result.data;
            });
    }
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
                        "value"  : link.value,
                        "unscaled"  : link.unscaled
                    });
                }
            }
            setBarInfo(focusid);
            updateChart();
        });
    }
    function setBarInfo(focusid) {
        // These are maps from appname to: countWith
        focusnode = {};
        if (focusid in app_dict) {
           focusnode = nodes[app_dict[focusid]];
           focus = focusnode.name;
        }
        if (focus == "") { return; }
        outbars = []; inbars=[]; logicbars = [];
        for (linknum in links) { 
            link = links[linknum]
            if  (nodes[link.source].id == focusid && link.unscaled.static > 0) {
                outbars.push( { "count": link.unscaled.static, "node": nodes[link.target] });
            } 
            if (nodes[link.source].id == focusid && link.unscaled.logical > 0) {
                logicbars.push({ "count": link.unscaled.logical, "node": nodes[link.source] });
            } 
            if (nodes[link.target].id == focusid && link.unscaled.static > 0) {
                inbars.push({ "count": link.unscaled.static, "node": nodes[link.target] });
            }
        }         
        setLabels(focus);
    }
    function updateChart() {
        svg.append("text").text("updateChart");
        var barHeight = 25;
        var titleHeight = 25;
        var xscale = d3.scale.linear()
            .domain([0, focusnode["uses"]])
            .range([0,width]);

        var vposn = titleHeight;
        mainbartitle.attr("y", vposn);

        vposn = vposn + titleHeight;
        inbartitle.attr("y", vposn);

        vposn = vposn + titleHeight;
        svginbars.attr("y", vposn);
        svginbars.attr("height", barHeight*inbars.length);
 
        svg.append("text").text(inbars);
        var inbar = svginbars.selectAll("g")
            .data(inbars)
            .enter().append("g")
            .attr("class", "dependencybars")
            .attr("transform", function(d,i) { return "translate(0," + i*barHeight + ")"; });
        drawRect(inbar);
        vposn = vposn + barHeight*inbars.length; //svginbars.node().getBBox().height;
        svginbars.attr("y", vposn);

        outbartitle.attr("y", vposn);
        vposn = vposn + titleHeight; //outbartitle.node().getBBox().height;

        svgoutbars.attr("y", vposn)
                  .attr("height", barHeight*outbars.length);
        var outbar = svgoutbars.selectAll("g")
            .data(outbars)
            .enter().append("g")
            .attr("class", "dependencybars")
            .attr("transform", function(d,i) { return "translate(0," +i*barHeight + ")"; });
        drawRect(outbar);
        vposn = vposn + barHeight*outbars.length; //svgoutbars.node().getBBox().height;

        logicbartitle.attr("y", vposn);
        vposn = vposn + titleHeight; //outbartitle.node().getBBox().height;

        svglogicbars.attr("y", vposn)
                    .attr("height", barHeight*logicbars.length);
        var logicbar = svglogicbars.selectAll("g")
            .data(logicbars)
            .enter().append("g")
            .attr("class", "dependencybars")
            .attr("transform", function(d,i) { return "translate(0," +i*barHeight + ")"; });
        drawRect(logicbar);

        function drawRect(bar) {
            bar.append("rect")
                .attr("stroke", "blue")
  
                .attr("width", function(b) { return xscale(b["count"]); })
                .attr("height", barHeight - 2);
            bar.append("text")
                .attr("x", function(b) { return xscale(b["count"])+3; })
                .attr("y", barHeight/2)
                .text(function(b) { return b["node"]["name"] + ": " + b["count"] + " runs"; });
        }

    }


    return {
        start: function(id){loadUserInfo(); loadData(id);}
    }
}
