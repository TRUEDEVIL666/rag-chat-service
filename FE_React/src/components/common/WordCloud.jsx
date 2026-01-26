
import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import cloud from 'd3-cloud';

// Simple default color scale using Tailwind-ish hex codes
const defaultColors = ['#4f46e5', '#ec4899', '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b'];

const WordCloud = ({ words = [], width = 400, height = 300, colors = defaultColors }) => {
  // Use a dedicated ref for D3. React will NEVER put children inside this.
  const d3ContainerRef = useRef(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (!d3ContainerRef.current) return;

    // 1. Clean up previous D3 render
    // This is safe now because d3ContainerRef is an empty <div> from React's perspective.
    d3.select(d3ContainerRef.current).selectAll("*").remove();

    // Reset ready state if data changes
    if (words.length === 0) {
      setIsReady(true); // Nothing to render, so we are "ready"
      return;
    }
    setIsReady(false);

    // 2. Setup Dimensions
    const layoutW = width;
    const layoutH = height;

    // 3. Normalization Scale
    const values = words.map(w => w.value);
    const minVal = d3.min(values) || 0;
    const maxVal = d3.max(values) || 100;

    const fontScale = d3.scaleSqrt()
      .domain([minVal, maxVal])
      .range([12, 40]);

    const fill = d3.scaleOrdinal(colors);

    // 4. Configure Layout
    const layout = cloud()
      .size([layoutW, layoutH])
      .words(words.map(d => ({ text: d.text, size: fontScale(d.value), value: d.value })))
      .padding(2)
      .rotate(0) // Horizontal only
      .font("Inter, sans-serif")
      .fontSize(d => d.size)
      .on("end", draw);

    layout.start();

    function draw(computedWords) {
      if (!d3ContainerRef.current) return;

      const svg = d3.select(d3ContainerRef.current)
        .append("svg")
        .attr("width", "100%")
        .attr("height", "100%")
        .attr("viewBox", `0 0 ${layout.size()[0]} ${layout.size()[1]}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("overflow", "visible")
        .append("g")
        .attr("transform", "translate(" + layout.size()[0] / 2 + "," + layout.size()[1] / 2 + ")");

      const text = svg.selectAll("text")
        .data(computedWords)
        .enter().append("text")
        .style("font-size", d => d.size + "px")
        .style("font-family", "Inter, sans-serif")
        .style("fill", (d, i) => fill(i))
        .attr("text-anchor", "middle")
        .attr("transform", d => "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")")
        .text(d => d.text)
        .style("cursor", "default")
        .style("opacity", 0);

      // Animation
      text.transition()
        .duration(600)
        .style("opacity", 1)
        .on("end", () => setIsReady(true)); // Mark ready after animation starts/ends

      // Fallback in case transition is interrupted or fast
      setTimeout(() => setIsReady(true), 100);
    }

  }, [words, width, height, colors]);

  return (
    <div className="w-full h-full relative overflow-hidden flex items-center justify-center bg-transparent">
      {/* D3 Render Layer - Strict Isolation */}
      <div
        ref={d3ContainerRef}
        className="w-full h-full absolute inset-0 z-0 flex items-center justify-center pointer-events-none"
      />

      {/* React Status Layer - Sibling overlay */}
      {!isReady && words.length > 0 && (
        <div className="z-10 bg-white/50 dark:bg-gray-800/50 p-2 rounded-lg backdrop-blur-sm transition-opacity">
          <span className="text-xs text-gray-500 font-medium animate-pulse">
            Rendering...
          </span>
        </div>
      )}
    </div>
  );
};

export default WordCloud;
