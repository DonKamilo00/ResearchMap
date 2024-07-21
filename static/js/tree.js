// tree.js

console.log("tree.js loaded");

function renderTree(data) {
    console.log("Rendering tree with data:", data);
    // Clear any existing SVG
    d3.select("#network").selectAll("*").remove();

    // Set up dimensions
    const width = 2000;
    const height = 1200;
    const margin = {top: 20, right: 120, bottom: 30, left: 120};

    // Create SVG
    const svg = d3.select("#network")
        .append("svg")
        .attr("width", "100%")
        .attr("height", "100%")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Add zoom functionality
    const zoom = d3.zoom().on("zoom", (event) => {
        svg.attr("transform", event.transform);
    });
    d3.select("#network svg").call(zoom);

    // Create tree layout
    const treeLayout = d3.tree().size([height - margin.top - margin.bottom, width - margin.left - margin.right]);

    // Create root node
    const root = d3.hierarchy(data);

    // Assign positions to nodes
    treeLayout(root);

    // Create color scale for institutions
    const institutions = new Set(root.descendants().map(d => d.data.institution));
    const colorScale = d3.scaleOrdinal(d3.schemeCategory10).domain(Array.from(institutions));

    // Create links
    svg.selectAll(".link")
        .data(root.links())
        .enter().append("path")
        .attr("class", "link")
        .attr("d", d3.linkHorizontal()
            .x(d => d.y)
            .y(d => d.x))
        .attr("stroke", "#ccc")
        .attr("fill", "none");

    // Create nodes
    const node = svg.selectAll(".node")
        .data(root.descendants())
        .enter().append("g")
        .attr("class", d => "node" + (d.children ? " node--internal" : " node--leaf"))
        .attr("transform", d => `translate(${d.y},${d.x})`);

    // Add circles to nodes
    node.append("circle")
        .attr("r", d => Math.sqrt(d.data.value) * 3 || 5)
        .attr("fill", d => colorScale(d.data.institution));

    // Function to wrap text
    function wrap(text, width) {
        text.each(function() {
            let text = d3.select(this),
                words = text.text().split(/\s+/).reverse(),
                word,
                line = [],
                lineNumber = 0,
                lineHeight = 1.1,
                y = text.attr("y"),
                dy = parseFloat(text.attr("dy")),
                tspan = text.text(null).append("tspan").attr("x", 0).attr("y", y).attr("dy", dy + "em");
            while (word = words.pop()) {
                line.push(word);
                tspan.text(line.join(" "));
                if (tspan.node().getComputedTextLength() > width) {
                    line.pop();
                    tspan.text(line.join(" "));
                    line = [word];
                    tspan = text.append("tspan").attr("x", 0).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
                }
            }
        });
    }

    // Add clickable labels to nodes
    node.append("a")
        .attr("xlink:href", d => d.data.profile_url)
        .attr("target", "_blank")
        .append("text")
        .attr("dy", ".31em")
        .attr("x", d => d.children ? -8 : 8)
        .style("text-anchor", d => d.children ? "end" : "start")
        .text(d => `${d.data.name} [${d.data.institution}]`)
        .call(wrap, 200);

    // Add toggle functionality for collapsing/expanding nodes
    node.on("click", (event, d) => {
        if (d.children) {
            d._children = d.children;
            d.children = null;
        } else {
            d.children = d._children;
            d._children = null;
        }
        renderTree(root.data);
    });
}

function searchResearcher() {
    console.log("Search button clicked");
    const query = document.getElementById('searchInput').value;
    console.log("Search query:", query);
    fetch(`/search?query=${encodeURIComponent(query)}`)
        .then(response => {
            console.log("Search response received:", response);
            return response.json();
        })
        .then(data => {
            console.log("Search results:", data);
            const resultsList = document.getElementById('searchResults');
            resultsList.innerHTML = '';
            data.forEach(researcher => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = researcher.profile_url;
                a.target = "_blank";
                a.textContent = researcher.name;
                li.appendChild(a);
                li.appendChild(document.createTextNode(` [${researcher.institution}]`));
                li.onclick = (e) => {
                    if (e.target.tagName !== 'A') {
                        fetchNetwork(researcher.id);
                    }
                };
                resultsList.appendChild(li);
            });
        })
        .catch(error => console.error("Error in searchResearcher:", error));
}

function fetchNetwork(researcherId) {
    console.log("Fetching network for researcher ID:", researcherId);
    fetch(`/network?researcher=${researcherId}`)
        .then(response => response.json())
        .then(data => {
            console.log("Network data received:", data);
            renderTree(data);
        })
        .catch(error => console.error("Error in fetchNetwork:", error));
}

document.addEventListener('DOMContentLoaded', (event) => {
    console.log("DOM fully loaded and parsed");
    const searchButton = document.getElementById('searchButton');
    if (searchButton) {
        searchButton.addEventListener('click', searchResearcher);
        console.log("Search button event listener added");
    } else {
        console.error("Search button not found in the DOM");
    }
});