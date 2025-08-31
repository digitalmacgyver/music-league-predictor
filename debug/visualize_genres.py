#!/usr/bin/env python3
"""
Generate a D3.js visualization of genre relationships.
Creates an interactive HTML file showing genre distances.
"""

import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'lib'))

from genre_mapper import GenreMapper

def generate_genre_visualization():
    """Generate HTML visualization of genre relationships."""
    mapper = GenreMapper(verbose=False)
    
    # Collect top genres to visualize
    genre_frequency = {}
    for artist_genres in mapper.artist_genres_cache.values():
        for genre in artist_genres:
            genre_frequency[genre] = genre_frequency.get(genre, 0) + 1
    
    # Get top genres plus our manually defined root genres
    top_genres = set()
    
    # Add root genres from manual hierarchy
    for genre, rel in mapper.genre_relationships.items():
        if rel.get('parent') is None:
            top_genres.add(genre)
            # Add their immediate children
            for subgenre in rel.get('subgenres', [])[:5]:  # Limit to 5 subgenres each
                top_genres.add(subgenre)
    
    # Add most common Spotify genres
    sorted_genres = sorted(genre_frequency.items(), key=lambda x: x[1], reverse=True)
    for genre, _ in sorted_genres[:20]:
        top_genres.add(genre)
    
    # Limit total for visualization
    genre_list = list(top_genres)[:40]
    
    # Build nodes and links for D3
    nodes = []
    links = []
    
    # Create nodes
    for i, genre in enumerate(genre_list):
        # Determine node type
        if genre in mapper.genre_relationships and mapper.genre_relationships[genre].get('parent') is None:
            group = 'root'
            size = 15
        elif genre in mapper.genre_relationships:
            group = 'defined'
            size = 10
        else:
            group = 'spotify'
            size = 8
        
        nodes.append({
            'id': genre,
            'group': group,
            'size': size,
            'frequency': genre_frequency.get(genre, 0)
        })
    
    # Create links (edges) based on distances
    for i, g1 in enumerate(genre_list):
        for j, g2 in enumerate(genre_list):
            if i < j:  # Avoid duplicates
                distance = mapper.calculate_genre_distance(g1, g2)
                if distance <= 0.5:  # Only show related genres
                    links.append({
                        'source': g1,
                        'target': g2,
                        'distance': distance,
                        'strength': 1.0 - distance  # For force simulation
                    })
    
    # Generate HTML with embedded D3.js
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Music Genre Relationship Map</title>
    <meta charset="utf-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        
        h1 {
            text-align: center;
            color: #333;
        }
        
        #info {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 250px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        #legend {
            position: absolute;
            top: 20px;
            left: 20px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .legend-item {
            margin: 5px 0;
        }
        
        .legend-color {
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 10px;
            vertical-align: middle;
            border-radius: 50%;
        }
        
        svg {
            display: block;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .node {
            cursor: pointer;
            stroke: #fff;
            stroke-width: 2px;
        }
        
        .node:hover {
            stroke: #000;
            stroke-width: 3px;
        }
        
        .link {
            fill: none;
            stroke-opacity: 0.4;
        }
        
        .link.highlighted {
            stroke-opacity: 1;
            stroke-width: 3px;
        }
        
        .node-label {
            font-size: 10px;
            pointer-events: none;
            text-anchor: middle;
            fill: #333;
        }
        
        .distance-label {
            font-size: 14px;
            font-weight: bold;
            color: #666;
        }
        
        #controls {
            text-align: center;
            margin: 20px 0;
        }
        
        button {
            margin: 0 5px;
            padding: 8px 15px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        
        button:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <h1>Music Genre Relationship Map</h1>
    
    <div id="legend">
        <h3>Legend</h3>
        <div class="legend-item">
            <span class="legend-color" style="background: #ff6b6b"></span>
            Root Genre
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #4ecdc4"></span>
            Defined Genre
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #95e77e"></span>
            Spotify Genre
        </div>
        <h4>Edge Distance:</h4>
        <div class="legend-item">
            <span style="color: #2ecc71">━━━</span> 0.0-0.15 (very close)
        </div>
        <div class="legend-item">
            <span style="color: #f39c12">━━━</span> 0.15-0.3 (related)
        </div>
        <div class="legend-item">
            <span style="color: #e74c3c">━━━</span> 0.3-0.5 (distant)
        </div>
    </div>
    
    <div id="info">
        <h3>Genre Info</h3>
        <p>Click on a genre to see its relationships</p>
        <div id="genre-details"></div>
    </div>
    
    <div id="controls">
        <button onclick="resetZoom()">Reset View</button>
        <button onclick="toggleLabels()">Toggle Labels</button>
    </div>
    
    <svg id="graph"></svg>
    
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
        // Data
        const nodes = ''' + json.dumps(nodes) + ''';
        const links = ''' + json.dumps(links) + ''';
        
        // Dimensions
        const width = 1200;
        const height = 800;
        
        // Color scales
        const nodeColors = {
            'root': '#ff6b6b',
            'defined': '#4ecdc4',
            'spotify': '#95e77e'
        };
        
        function linkColor(distance) {
            if (distance <= 0.15) return '#2ecc71';
            if (distance <= 0.3) return '#f39c12';
            return '#e74c3c';
        }
        
        function linkWidth(distance) {
            return Math.max(1, 5 * (1 - distance));
        }
        
        // Create SVG
        const svg = d3.select('#graph')
            .attr('width', width)
            .attr('height', height);
        
        const g = svg.append('g');
        
        // Add zoom
        const zoom = d3.zoom()
            .scaleExtent([0.5, 5])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });
        
        svg.call(zoom);
        
        // Create force simulation
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links)
                .id(d => d.id)
                .distance(d => 50 + d.distance * 150)
                .strength(d => d.strength))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(d => d.size + 5));
        
        // Create links
        const link = g.append('g')
            .selectAll('line')
            .data(links)
            .join('line')
            .attr('class', 'link')
            .attr('stroke', d => linkColor(d.distance))
            .attr('stroke-width', d => linkWidth(d.distance));
        
        // Create nodes
        const node = g.append('g')
            .selectAll('circle')
            .data(nodes)
            .join('circle')
            .attr('class', 'node')
            .attr('r', d => d.size)
            .attr('fill', d => nodeColors[d.group])
            .call(drag(simulation));
        
        // Add labels
        const labels = g.append('g')
            .selectAll('text')
            .data(nodes)
            .join('text')
            .attr('class', 'node-label')
            .text(d => d.id)
            .style('display', 'block');
        
        // Node interactions
        node.on('click', function(event, d) {
            // Highlight connected nodes and links
            const connectedNodes = new Set();
            const distances = {};
            
            links.forEach(l => {
                if (l.source.id === d.id) {
                    connectedNodes.add(l.target.id);
                    distances[l.target.id] = l.distance;
                } else if (l.target.id === d.id) {
                    connectedNodes.add(l.source.id);
                    distances[l.source.id] = l.distance;
                }
            });
            
            // Update link highlighting
            link.classed('highlighted', l => 
                l.source.id === d.id || l.target.id === d.id);
            
            // Update node opacity
            node.style('opacity', n => 
                n.id === d.id || connectedNodes.has(n.id) ? 1 : 0.3);
            
            // Update info panel
            let details = `<h4>${d.id}</h4>`;
            details += `<p>Type: ${d.group}</p>`;
            if (d.frequency > 0) {
                details += `<p>Found in ${d.frequency} artist(s)</p>`;
            }
            details += `<h5>Related Genres:</h5><ul>`;
            
            const sortedConnected = Array.from(connectedNodes)
                .sort((a, b) => distances[a] - distances[b]);
            
            sortedConnected.forEach(nodeId => {
                const dist = distances[nodeId].toFixed(2);
                details += `<li>${nodeId} <span class="distance-label">(${dist})</span></li>`;
            });
            details += '</ul>';
            
            document.getElementById('genre-details').innerHTML = details;
        });
        
        // Update positions on tick
        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            
            labels
                .attr('x', d => d.x)
                .attr('y', d => d.y - d.size - 5);
        });
        
        // Drag functionality
        function drag(simulation) {
            function dragstarted(event) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }
            
            function dragged(event) {
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }
            
            function dragended(event) {
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }
            
            return d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended);
        }
        
        // Control functions
        function resetZoom() {
            svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity);
        }
        
        let labelsVisible = true;
        function toggleLabels() {
            labelsVisible = !labelsVisible;
            labels.style('display', labelsVisible ? 'block' : 'none');
        }
    </script>
</body>
</html>'''
    
    # Write HTML file
    output_path = Path('reports/genre_relationships.html')
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"Visualization generated: {output_path}")
    print(f"Included {len(nodes)} genres with {len(links)} relationships")
    print("\nOpen reports/genre_relationships.html in a browser to view the interactive visualization")
    
    # Also generate a simple text table for quick reference
    print("\n" + "="*60)
    print("GENRE DISTANCE TABLE (Sample)")
    print("="*60)
    
    # Show distances for a few key genres
    sample_genres = ['rock', 'pop', 'jazz', 'hip hop', 'electronic']
    print(f"{'Genre':<15}", end='')
    for g in sample_genres:
        print(f"{g:<12}", end='')
    print()
    print("-" * 75)
    
    for g1 in sample_genres:
        print(f"{g1:<15}", end='')
        for g2 in sample_genres:
            if g1 == g2:
                print(f"{'0.00':<12}", end='')
            else:
                dist = mapper.calculate_genre_distance(g1, g2)
                print(f"{dist:<12.2f}", end='')
        print()

if __name__ == "__main__":
    generate_genre_visualization()