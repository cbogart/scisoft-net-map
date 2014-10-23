// Note: maybe try this: http://jsfiddle.net/VTNax/2/
//   i.e. put the rows below the header in one giant colspan=n cell,
//       and do the same with columns inside that after the header,so
//       there's two nested <div>s inside the table (the first containing
//       the left-column headers and the second <div>, and the second <div> containing
//       just the table cell blocks)
function vizDSM(container, options) {
    var options = $.extend({ //Default or expected options go here
        height  : container.height(),
        width   : container.width(),
        stat_id: "force_directed",  // api/stat/{stat_id},
        clickable: true
    }, options);
    
    function colorScale(static, logical) { 
       if (static > 0) {
           v = Math.floor(192-(static*12))
           return "rgb(" + v + "," + v + "," + v + ")"
       } else {
           v = Math.floor(200-(logical*20))
           return "rgb(0," + v + "," + v + ")"
       }
    } 
    function loadData(id) {snmapi.getStat(options.stat_id, {"id": id, "clustered": true},
        function(result) {
            var nodeIdToIndex = {};
            nodes2value = {}
            var data = result.data;

            for (i in data.nodes) {
                nodeIdToIndex[data.nodes[i].id] = i
            }
            for (linksIx in data.links) {
                link = data.links[linksIx];
                nodes2value[[nodeIdToIndex[link["source"]],nodeIdToIndex[link["target"]]]] = link.value
            }

            var table = d3.select("#dsm table")
            table.html("")//    // Clean it out in case there was junk there before
            var headrow = table.append("tr")
            headrow.append("th")      // Upper left corner empty square
            for (i in data.nodes) {
                headrow.append("th")
                       .attr("class","rotated")
                       .append("div")
                       .append("span")
                       .text(data.nodes[i].name);
                var row = table.append("tr");
                row.append("th")
                   .append("div")
                   .append("span")
                   .text(data.nodes[i].name);
                for (j in data.nodes) {
                    var v = nodes2value[[i,j]]
                    var color = "rgb(255,255,255)"
                    var caption = "No dependency between " + data.nodes[i].name + " and " + data.nodes[j].name;
                    if (!(v == undefined)) {
                        color = colorScale(v.static, v.logical)
                        if (v.static > 0) {
                            caption = data.nodes[i].name + " statically depends " + (v.static*10) +  "% of the time on " + data.nodes[j].name;
                        } else {
                            caption = data.nodes[i].name + " is used " + (v.logical*10) +  "% of the time after " + data.nodes[j].name;
                        }
                    }
                    row.append("td")
                       .style("background-color", color)
                       .attr("title", caption);
                }
            }

              //degree= (255 - min(255, 40*math.log(dsm[row,col]+1)))
              //color = "bgcolor=\"#ff%02x%02x\"" % (degree, degree)
              //title = "title=\"%s -> %s\"" % (nLabels[row], nLabels[col])
              //f.write("<td %s %s></td>" % (color, title))
        });
    }


    return {
        start: function(id){loadData(id);}
    }
}
