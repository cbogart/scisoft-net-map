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
        .text("Out of _ jobs of _");
    var mainbartitle2 = svg.append("text")
        .attr("class", "bartitle")
        .text("Out of _ jobs of _");
    var axis = svg.append("g").attr("class","baraxis");
    var inbartitle = svg.append("text")
        .attr("class", "barsubtitle")
        .attr("id", "inbartitle")
        .text("Packages that depend on _");
    var outbartitle = svg.append("text")
        .attr("class", "barsubtitle")
        .attr("id", "outbartitle")
        .text("Packages that _ depends on ");
    var hoverhelp = svg.append("text").text("?");
    var outbarExplanation = "";
    var logicbartitle = svg.append("text")
        .attr("class", "barsubtitle")
        .attr("id", "logicbartitle")
        .text("Packages were used with _");
    function titleAndText(elt, content, hover) {
        var hovertext = true;
        if (typeof(hover)==='undefined') { 
            hover = content; hovertext = false; 
        }
        elt.text(content).append("title").text(hover);
        if (hovertext) { 
            var q = elt.append("circle").attr("fill","blue").attr("r", 16).attr("x","0").attr("y","0").attr("stroke","green").attr("transform","translate(50,0)").append("text");
            q.text("?").append("title").text(hover);
        }
    }
    function setLabels(focusname) {
        titleAndText(mainbartitle, "What users used with " + focusname);
        titleAndText(mainbartitle2, "Out of " + focusnode.uses + " jobs...");
        titleAndText(inbartitle, "" + inbars.length + " downstream dependencies",
                                  "These packages appeared in jobs alongside " + focusname + ", and listed " + focusname + " as a dependency.");
        outbarExplanation = "These packages appeared in jobs alongside " + focusname + ", and were listed as dependencies. " +
                                  "They may not show up in all " + focusnode.uses + " jobs, if there were different versions of " + focusname +
                                  ", or if some dependency data was unavailable.";
        titleAndText(outbartitle, "" + outbars.length + " upstream dependencies", outbarExplanation);
        titleAndText(logicbartitle, "" + logicbars.length + " other packages",
                                  "These packages appeared in jobs alongside " + focusname + ", with no known dependency relationship.");
           
        
    }    
    var svginbars = svg.append("g")
    var svgoutbars = svg.append("g")
    var svglogicbars = svg.append("g")
    var inbars = [], outbars = [], logicbars = [];
    var app_dict = {},
        link_dict = {},
        counter = 0,
        nodes = [],
        user_vector = {},
        links = [];
    function loadUserInfo(user) { 
        snmapi.getStat("user_vector", {"id": options.scimapID},
            function(result) {
               user_vector = result.data;
            });
    }
    function loadData(id) {snmapi.getStat(options.stat_id, {"id": id, "limit":99},
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
                        "type"  : link.type,
                        "scaled"  : link.scaled,
                        "raw"  : link.raw
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
            if  (nodes[link.source].id == focusid && link.type == "upstream") {
                outbars.push( { "count": link.raw, "node": nodes[link.target] });
            } 
            else if (nodes[link.target].id == focusid && link.type=="usedwith" ) {
                logicbars.push({ "count": link.raw, "node": nodes[link.source] });
            } 
            else if (nodes[link.source].id == focusid && link.type=="usedwith") {
                logicbars.push({ "count": link.raw, "node": nodes[link.target] });
            } 
            else if (nodes[link.source].id == focusid &&  link.type=="downstream") {
                inbars.push({ "count": link.raw, "node": nodes[link.target] });
            }
            else if (nodes[link.target].id == focusid &&  link.type=="upstream") {
                inbars.push({ "count": link.raw, "node": nodes[link.source] });
            }
            else if (nodes[link.target].id == focusid &&  link.type=="downstream") {
                inbars.push({ "count": link.raw, "node": nodes[link.source] });
            }
        }         
        outbars.sort(function(a,b) { return b.count - a.count; });
        inbars.sort(function(a,b) { return b.count - a.count; });
        logicbars.sort(function(a,b) { return b.count - a.count; });
        setLabels(focus);
    }
    function updateChart() {
        var barHeight = 20;
        var heightFudge = 14;
        var titleHeight = 25;
        var horizpadding = 5;
        var xscale = d3.scale.linear()
            .domain([0, focusnode["uses"]])
            .range([horizpadding,width-horizpadding]);

        var vposn = titleHeight;
        mainbartitle.attr("y", vposn).attr("x", horizpadding);

        vposn = vposn + titleHeight;
        mainbartitle2.attr("y", vposn).attr("x", horizpadding);

        vposn = vposn + titleHeight;
        var xAxis = d3.svg.axis().scale(xscale).orient("top").ticks(4);
        axis.call(xAxis);
        axis.attr("transform", "translate(0, " + vposn + ")");
        
        function addBorder(title, bars) {
            svg.insert("rect", "#" + title.attr("id"))
             .attr("x", 0)
             .attr("y", title.attr("y")-heightFudge)
             .attr("stroke", "#888888")
             .attr("fill-opacity", "0.1")
             .attr("width", width)
             .attr("height", barHeight*bars.length+titleHeight);
        }

        vposn = vposn + titleHeight;
        inbartitle.attr("y", vposn).attr("x", horizpadding);

        vposn = vposn + titleHeight;
        svginbars.attr("transform", "translate(" + xscale(0) + "," + (vposn-heightFudge) + ")");
        svginbars.attr("height", barHeight*inbars.length);
 
        var inbar = svginbars.selectAll("g")
            .data(inbars)
            .enter().append("g")
            .attr("class", "dependencybars")
            .attr("transform", function(d,i) { return "translate(" + xscale(0) + "," + i*barHeight + ")"; });
        drawRect(inbar);
        vposn = vposn + barHeight*inbars.length; 
        addBorder(inbartitle, inbars);


        outbartitle.attr("y", vposn).attr("x", horizpadding);
        vposn = vposn + titleHeight; //outbartitle.node().getBBox().height;

        svgoutbars.attr("transform", "translate(" + xscale(0) + "," + (vposn-heightFudge) + ")")
                  .attr("height", barHeight*outbars.length);
        var outbar = svgoutbars.selectAll("g")
            .data(outbars)
            .enter().append("g")
            .attr("class", "dependencybars")
            .attr("transform", function(d,i) { return "translate(" + xscale(0) + "," +i*barHeight + ")"; });
        drawRect(outbar);
        vposn = vposn + barHeight*outbars.length; //svgoutbars.node().getBBox().height;
        addBorder(outbartitle, outbars);


        logicbartitle.attr("y", vposn).attr("x", horizpadding);
        vposn = vposn + titleHeight; 

        svglogicbars.attr("transform", "translate(" + xscale(0) + "," + (vposn-heightFudge) + ")")
                    .attr("height", barHeight*logicbars.length);
        var logicbar = svglogicbars.selectAll("g")
            .data(logicbars)
            .enter().append("g")
            .attr("class", "dependencybars")
            .attr("transform", function(d,i) { return "translate(" + xscale(0) + "," +i*barHeight + ")"; });
        drawRect(logicbar);
        addBorder(logicbartitle, logicbars);

        function text_CoUsePercentOfFocus(d) {
            var only = "";
            if (d["count"] < focusnode["uses"]/2) { only = " only"; }
            return(
                  d["node"]["name"] + ": " + d["count"] + " jobs\n" +
                  "In " + (Math.floor(d["count"]*100/focusnode["uses"])) + "% of the jobs where "
                   + focusnode["name"] + " was run, "
                   + d["node"]["name"] + " was also run "
                   + "(" + d["count"] + "/" + focusnode["uses"] + " jobs)");
        }
        function text_FocusPercentOfCoUse(d) {
            var only = "";
            if (d["count"] < focusnode["uses"]/2) { only = " only"; }
            return(
                  "In " + only + (Math.floor(d["count"]*100/focusnode["uses"])) + "% of the jobs where "
                   + focusnode["name"] + " was run, "
                   + d["node"]["name"] + " was also run "
                   + "(" + d["count"] + "/" + focusnode["uses"] + " jobs)");
        }

        function drawRect(bar) {
            bar.append("rect")
               // .attr("stroke", "red")   //#1f77b4
                //.attr("fill", "red")
                .attr("class", "co-use-color")
                .attr("width", function(b) { return xscale(b["count"]); })
                .attr("height", barHeight - 2);

            bar.append("title").text(text_CoUsePercentOfFocus);

            bar.append("a")
                .attr("xlink:href", function(d) { return d.node.link; })
                .append("text")
                .text(function(b) { return b["node"]["name"] + ": " + b["count"] + " jobs"; })
                .each(function(b) { if (xscale(b["count"]) > this.getComputedTextLength()) {
                                        b["posn"] = "inside"; } else { b["posn"] = "outside"; } })
                .attr("class", "co-use-color")
                .attr("style", function(b) { if (b.posn=="outside") { 
                      return "text-anchor: start; "; } 
                    else { 
                      return "text-anchor: end; fill:#ffffff; stroke:#fff; stroke-width:1px;"; }})
                .attr("x", function(b) { 
                   var pad = horizpadding;
                   if (b.posn == "inside") { pad = -horizpadding; }
                   return xscale(b["count"]) + pad; })
                .attr("y", heightFudge)
                .append("title").text(text_CoUsePercentOfFocus);
        }

    }


    return {
        start: function(id){loadUserInfo(); loadData(id);}
    }
}
