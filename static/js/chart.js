// Register Chart.js Zoom plugin globally at the very top
if (window.Chart && window.Chart.register && window.ChartZoom) {
  Chart.register(window.ChartZoom);
}

let tutorChart;

function isDarkMode() {
  // Charts page uses fixed light purple theme - always return false
  return false;
}

const chartOptions = {
  appointments_per_tutor: ['bar', 'pie', 'doughnut'],
  hours_per_tutor: ['bar', 'pie', 'doughnut'],
  daily_appointments: ['bar', 'line', 'scatter'],
  daily_hours: ['bar', 'line', 'area', 'scatter'],
  cumulative_appointments: ['line', 'area'],
  cumulative_hours: ['line', 'area'],
  hourly_distribution: ['bar', 'line', 'scatter'],
  monthly_appointments: ['bar', 'line', 'scatter'],
  monthly_hours: ['bar', 'line', 'scatter'],
  avg_hours_per_day_of_week: ['bar', 'pie', 'doughnut'],
  appointments_per_day_of_week: ['bar', 'pie', 'doughnut'],
  appointments_by_status: ['bar', 'pie', 'doughnut'],
  appointments_by_course: ['bar', 'pie', 'doughnut'],
  appointment_duration_distribution: ['bar', 'pie', 'doughnut'],
  tutor_course_distribution: ['bar', 'pie', 'doughnut'],
  shifts_overview: ['bar', 'pie', 'doughnut'],
  tutor_availability: ['bar', 'pie', 'doughnut']
};

const chartTitles = {
  appointments_per_tutor: "Appointments per Tutor",
  hours_per_tutor: "Scheduled Hours per Tutor",
  daily_appointments: "Daily Appointments",
  daily_hours: "Daily Scheduled Hours",
  cumulative_appointments: "Cumulative Appointments",
  cumulative_hours: "Cumulative Hours",
  hourly_distribution: "Hourly Appointment Distribution",
  monthly_appointments: "Monthly Appointments",
  monthly_hours: "Monthly Hours",
  avg_hours_per_day_of_week: "Average Hours per Day of Week",
  appointments_per_day_of_week: "Appointments per Day of Week",
  appointments_by_status: "Appointments by Status",
  appointments_by_course: "Appointments by Course",
  appointment_duration_distribution: "Appointment Duration Distribution",
  tutor_course_distribution: "Courses Assigned per Tutor",
  shifts_overview: "Shift Assignments per Tutor",
  tutor_availability: "Availability Windows per Tutor"
};

// Dark mode color schemes
const darkModeColors = {
  background: '#1e293b',
  surface: '#334155',
  primary: '#3b82f6',
  secondary: '#64748b',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#06b6d4',
  text: '#f8fafc',
  textSecondary: '#cbd5e1',
  textMuted: '#94a3b8',
  border: '#334155',
  grid: '#475569'
};

const lightModeColors = {
  background: '#ffffff',
  surface: '#ffffff',
  primary: '#667eea', // Purple to match dashboard theme
  secondary: '#64748b',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#667eea', // Purple to match dashboard theme
  text: '#1e293b',
  textSecondary: '#475569',
  textMuted: '#64748b',
  border: '#e2e8f0',
  grid: '#f1f5f9'
};

function getChartColors() {
  // Always use light mode colors for dashboard theme
  return lightModeColors;
}

function getChartColorPalette() {
  // Dashboard theme color palette - purple gradient colors
  return [
    '#667eea', // Primary purple
    '#764ba2', // Secondary purple
    '#10b981', // Success green
    '#f59e0b', // Warning amber
    '#ef4444', // Danger red
    '#8b5cf6', // Purple
    '#a78bfa', // Light purple
    '#c084fc', // Lighter purple
    '#06b6d4', // Cyan
    '#84cc16', // Lime
    '#ec4899', // Pink
    '#6366f1', // Indigo
    '#14b8a6', // Teal
    '#f59e0b', // Amber
    '#ef4444', // Red
    '#22c55e'  // Green
  ];
}

// Expose chartTitles to global scope
window.chartTitles = chartTitles;

// Function to update all existing charts with new theme colors
function updateAllChartsForTheme() {
  const colors = getChartColors();
  
  // Update Chart.js defaults
  Chart.defaults.color = colors.text;
  Chart.defaults.borderColor = colors.border;
  
  // Update all existing chart instances
  Object.values(Chart.instances).forEach(chart => {
    if (chart && chart.config) {
      // Update scales
      if (chart.config.options && chart.config.options.scales) {
        const scales = chart.config.options.scales;
        if (scales.x) {
          if (scales.x.grid) scales.x.grid.color = colors.grid;
          if (scales.x.ticks) scales.x.ticks.color = colors.textSecondary;
          if (scales.x.border) scales.x.border.color = colors.border;
        }
        if (scales.y) {
          if (scales.y.grid) scales.y.grid.color = colors.grid;
          if (scales.y.ticks) scales.y.ticks.color = colors.textSecondary;
          if (scales.y.border) scales.y.border.color = colors.border;
        }
      }
      
      // Update plugins
      if (chart.config.options && chart.config.options.plugins) {
        const plugins = chart.config.options.plugins;
        if (plugins.legend && plugins.legend.labels) {
          plugins.legend.labels.color = colors.text;
        }
        if (plugins.tooltip) {
          plugins.tooltip.backgroundColor = colors.surface;
          plugins.tooltip.titleColor = colors.text;
          plugins.tooltip.bodyColor = colors.textSecondary;
          plugins.tooltip.borderColor = colors.border;
        }
      }
      
      // Update chart background
      if (chart.canvas) {
        chart.canvas.style.backgroundColor = colors.background;
      }
      
      chart.update('none');
    }
  });
}

// Listen for theme changes
document.addEventListener('themeChanged', function(event) {
  updateAllChartsForTheme();
});

// Get default chart configuration with theme support
function getDefaultChartConfig() {
  const colors = getChartColors();
  
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: colors.text,
          font: {
            family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            size: 12
          }
        }
      },
      tooltip: {
        backgroundColor: colors.surface,
        titleColor: colors.text,
        bodyColor: colors.textSecondary,
        borderColor: colors.border,
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          title: function(context) {
            return context[0].label;
          },
          label: function(context) {
            return context.dataset.label + ': ' + context.parsed.y;
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          color: colors.grid,
          drawBorder: false
        },
        ticks: {
          color: colors.textSecondary,
          font: {
            family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            size: 11
          }
        },
        border: {
          color: colors.border
        }
      },
      y: {
        grid: {
          color: colors.grid,
          drawBorder: false
        },
        ticks: {
          color: colors.textSecondary,
          font: {
            family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            size: 11
          }
        },
        border: {
          color: colors.border
        }
      }
    },
    elements: {
      point: {
        borderWidth: 2,
        hoverBorderWidth: 3
      },
      line: {
        borderWidth: 2,
        tension: 0.1
      },
      bar: {
        borderWidth: 0,
        borderRadius: 4
      }
    },
    interaction: {
      intersect: false,
      mode: 'index'
    },
    animation: {
      duration: 750,
      easing: 'easeInOutQuart'
    }
  };
}

function renderChart(chartType, rawData, title, isComparisonMode = false, forecastData = null) {
  // Get current layout from global variable (defined in charts.html)
  const layout = typeof currentChartLayout !== 'undefined' ? currentChartLayout : 'single';
  
  if (layout === 'single') {
    renderSingleChart(chartType, rawData, title, isComparisonMode, forecastData);
  } else if (layout === 'split') {
    renderSplitChart(chartType, rawData, title, isComparisonMode, forecastData);
  } else if (layout === 'grid') {
    renderGridChart(chartType, rawData, title, isComparisonMode, forecastData);
  }
}

function renderSingleChart(chartType, rawData, title, isComparisonMode = false, forecastData = null) {
  const ctx = document.getElementById('tutorChart')?.getContext('2d');
  if (!ctx) return;
  
  const totalCountSpan = document.getElementById('totalCount');
  const summaryTableDiv = document.getElementById('chartSummaryTable');
  const chartTitleEl = document.getElementById('chartTitle');

  // Destroy existing chart instances
  if (tutorChart) tutorChart.destroy();
  if (window.chartInstance) window.chartInstance.destroy();
  if (window.comparisonChartInstance) window.comparisonChartInstance.destroy();
  
  // Clear currentChartInstances
  if (typeof currentChartInstances !== 'undefined') {
    Object.values(currentChartInstances).forEach(chart => {
      if (chart && chart.destroy) chart.destroy();
    });
    currentChartInstances = {};
  }
  
  if (summaryTableDiv) summaryTableDiv.innerHTML = '';

  let labels, datasetsArray;

  if (!rawData || (typeof rawData === 'object' && Object.keys(rawData).length === 0 && !isComparisonMode) || (Array.isArray(rawData) && rawData.length === 0) ) {
    chartTitleEl.innerText = "No data for this filter or chart type.";
    totalCountSpan.textContent = '';
    if (ctx) ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    return;
  }
  
  const chartKey = document.getElementById('dataset').value; // Get current chart key

  if (isComparisonMode && (chartKey === 'daily_appointments' || chartKey === 'daily_hours') && typeof rawData === 'object' && Object.keys(rawData).length > 0) {
    const allLabelsSet = new Set();
    Object.values(rawData).forEach(tutorData => Object.keys(tutorData).forEach(label => allLabelsSet.add(label)));
    labels = Array.from(allLabelsSet).sort();

    datasetsArray = Object.entries(rawData).map(([tutorName, tutorData], index) => {
        const dataPoints = labels.map(label => tutorData[label] || 0);
        const color = generateColors(Object.keys(rawData).length, false, index);
        const borderColor = generateColors(Object.keys(rawData).length, true, index);
        return {
            label: tutorName, data: dataPoints, fill: chartType === 'area',
            backgroundColor: color, borderColor: borderColor, borderWidth: 1.5, tension: 0.3,
            pointBackgroundColor: borderColor, pointBorderColor: '#1e293b'
        };
    });
    chartTitleEl.innerText = `${title} (Comparison)`;
    totalCountSpan.textContent = `Comparing ${Object.keys(rawData).length} tutors`;

  } else if (chartKey === 'hourly_activity_by_day' && (chartType === 'bar' || chartType === 'line')) {
    const daysOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    labels = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);
    datasetsArray = daysOrder.map((day, index) => {
        const dayData = rawData[day] || {};
        const dataPoints = labels.map(hourLabel => dayData[hourLabel] || 0);
        const color = generateColors(daysOrder.length, false, index);
        const borderColor = generateColors(daysOrder.length, true, index);
        return { label: day, data: dataPoints, backgroundColor: color, borderColor: borderColor, borderWidth: 1, tension: 0.3, fill: false };
    });
    chartTitleEl.innerText = title;
    let totalActivity = 0;
    Object.values(rawData).forEach(dayData => Object.values(dayData).forEach(count => totalActivity += count));
    totalCountSpan.textContent = `(Total Activity Events: ${totalActivity})`;

  } else if (!(chartKey === 'hourly_activity_by_day' && chartType === 'heatmap')) { // Standard mode or pie chart
    // Guard: prevent incompatible chart types on nested-object datasets
    const isNestedObject = typeof rawData === 'object' && rawData !== null && !Array.isArray(rawData) && Object.values(rawData).some(v => typeof v === 'object');
    if (isNestedObject && (chartType === 'pie' || chartType === 'line' || chartType === 'area')) {
        chartTitleEl.innerText = `This dataset requires a bar chart.`;
        totalCountSpan.textContent = '';
        if (ctx) ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        return;
    }
    let displayData = rawData;
    // For comparison mode on charts like 'appointments_per_tutor', rawData itself is the {TutorA: count, TutorB: count}
    // So labels are tutor names and data is their counts.
    labels = Object.keys(displayData);
    const data = Object.values(displayData);

    if (!labels.length || !data.length) {
        chartTitleEl.innerText = "No data for this filter.";
        totalCountSpan.textContent = '';
        if (ctx) ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        return;
    }
    
    let total;
    if (title.toLowerCase().includes("average")) {
        total = data.length; 
        totalCountSpan.textContent = `(Items: ${total})`;
    } else {
        total = data.reduce((a, b) => (typeof b === 'number' ? a + b : a), 0); // Sum only numbers
        totalCountSpan.textContent = `(Total: ${total.toFixed(2)})`;
    }
    chartTitleEl.innerText = title;

    // Dashboard theme colors - purple gradient
    const singleBackgroundColor = 'rgba(102, 126, 234, 0.7)'; // Purple with transparency
    const singleBorderColor = 'rgba(102, 126, 234, 1)'; // Solid purple

    datasetsArray = [{
        label: title, data: data, fill: chartType === 'area',
        backgroundColor: chartType === 'pie' ? generateColors(data.length) : singleBackgroundColor,
        borderColor: chartType === 'pie' ? generateColors(data.length, true) : singleBorderColor,
        borderWidth: 1, tension: 0.4,
        pointBackgroundColor: singleBorderColor, pointBorderColor: '#1e293b'
    }];

    if (forecastData && Object.keys(forecastData).length > 0 && chartType === 'line') {
        const forecastLabels = Object.keys(forecastData).sort();
        const forecastValues = forecastLabels.map(fl => forecastData[fl]);
        const allForecastLabels = [...new Set([...labels, ...forecastLabels])].sort();
        const alignedOriginalData = allForecastLabels.map(l => data[labels.indexOf(l)] ?? null);
        datasetsArray[0].data = alignedOriginalData;
        const alignedForecastData = allForecastLabels.map(l => forecastValues[forecastLabels.indexOf(l)] ?? null);
        datasetsArray.push({
            label: 'Forecast', data: alignedForecastData, borderColor: 'rgba(255, 0, 0, 0.7)',
            borderDash: [5, 5], fill: false, tension: 0.1, pointRadius: 3,
            pointBackgroundColor: 'rgba(255, 0, 0, 0.7)'
        });
        labels = allForecastLabels;
    }
    
    // Generate summary table for the chart's aggregated data
    if (Object.keys(displayData).length > 0 && (typeof displayData[Object.keys(displayData)[0]] === 'number' || typeof displayData[Object.keys(displayData)[0]] === 'string')) {
        summaryTableDiv.innerHTML = `
            <h6 class="mt-3">Chart Data Summary:</h6>
            <table class="table table-sm table-bordered table-striped">
            <thead><tr><th>Label</th><th>Value</th></tr></thead>
            <tbody>
                ${Object.keys(displayData).map((l) => `<tr><td>${l}</td><td>${parseFloat(displayData[l]).toFixed(2)}</td></tr>`).join('')}
            </tbody>
            </table>`;
    }
  } else if (chartKey === 'hourly_activity_by_day' && chartType === 'heatmap') {
    const daysOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const hours = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);
    const flatData = [];
    daysOrder.forEach((day, y) => {
      const byHour = rawData[day] || {};
      hours.forEach((h, x) => {
        flatData.push({ x, y, v: byHour[h] || 0 });
      });
    });
    // Render heatmap with axes and legend
    const canvas = ctx.canvas;
    // Ensure canvas fills its container and accounts for device pixel ratio
    const parent = canvas.parentElement || canvas;
    const cssW = Math.max(300, parent.clientWidth || canvas.width);
    const cssH = Math.max(300, parent.clientHeight || canvas.height);
    const dpr = window.devicePixelRatio || 1;
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);
    const W = cssW, H = cssH;
    ctx.clearRect(0, 0, W, H);
    const isDark = false; // Fixed light purple theme
    const margin = { top: 16, right: 24, bottom: 36, left: 80 };
    const width = W - margin.left - margin.right;
    const height = H - margin.top - margin.bottom;
    const cellW = Math.max(10, Math.floor(width / hours.length));
    const cellH = Math.max(16, Math.floor(height / daysOrder.length));
    const x0 = margin.left;
    const y0 = margin.top;
    // Compute value range
    const values = flatData.map(d => d.v);
    const maxV = Math.max(1, Math.max(...values));
    const minV = Math.min(0, Math.min(...values));
    const colorFor = (val) => {
      const t = (val - minV) / (maxV - minV || 1);
      const r = Math.floor(255 * t);
      const g = Math.floor(80 * (1 - t) + 20);
      const b = Math.floor(220 * (1 - t) + 20 * t);
      return `rgba(${r},${g},${b},0.9)`;
    };
    // Draw cells
    flatData.forEach(d => {
      const px = x0 + d.x * cellW;
      const py = y0 + d.y * cellH;
      ctx.fillStyle = colorFor(d.v);
      ctx.fillRect(px, py, cellW - 1, cellH - 1);
    });
    // Axes labels
    ctx.fillStyle = '#1e293b';
    ctx.font = '12px Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    daysOrder.forEach((day, i) => {
      const ty = y0 + i * cellH + cellH * 0.65;
      ctx.fillText(day.substring(0, 3), 10, ty);
    });
    hours.forEach((h, i) => {
      if (i % 2 === 0) {
        const tx = x0 + i * cellW + 2;
        const ty = y0 + height + 18;
        ctx.fillText(h.slice(0, 2), tx, ty);
      }
    });
    // Color legend
    const lgW = 140, lgH = 12;
    const lgX = x0 + width - lgW;
    const lgY = y0 + height + 4;
    const grad = ctx.createLinearGradient(lgX, lgY, lgX + lgW, lgY);
    for (let i = 0; i <= 10; i++) {
      const t = i / 10;
      const r = Math.floor(255 * t);
      const g = Math.floor(80 * (1 - t) + 20);
      const b = Math.floor(220 * (1 - t) + 20 * t);
      grad.addColorStop(t, `rgba(${r},${g},${b},0.9)`);
    }
    ctx.fillStyle = grad;
    ctx.fillRect(lgX, lgY, lgW, lgH);
    ctx.fillStyle = '#1e293b';
    ctx.font = '11px Inter, sans-serif';
    ctx.fillText(String(Math.round(minV)), lgX - 4 - ctx.measureText(String(Math.round(minV))).width, lgY + lgH);
    ctx.fillText(String(Math.round(maxV)), lgX + lgW + 4, lgY + lgH);
    chartTitleEl.innerText = title + ' (Heatmap)';
    totalCountSpan.textContent = '';
    return;
  }

  // Special handling for scatter plot
  if (chartType === 'scatter') {
    // Accept either array of {x,y} or object map -> convert to points
    let points = [];
    if (Array.isArray(rawData)) {
      points = rawData;
    } else if (rawData && typeof rawData === 'object') {
      const xs = Object.keys(rawData);
      const ys = Object.values(rawData);
      points = xs.map((x, i) => ({ x: isNaN(Number(x)) ? i : Number(x), y: Number(ys[i]) }));
    }
    const datasetsArray = [{
      label: title,
      data: points,
      backgroundColor: 'rgba(102, 126, 234, 0.7)', // Purple theme
      borderColor: 'rgba(102, 126, 234, 1)', // Purple theme
      pointRadius: 4
    }];
    const defaultConfig = getDefaultChartConfig();
    tutorChart = new Chart(ctx, {
      type: 'scatter',
      data: { datasets: datasetsArray },
      options: {
        ...defaultConfig,
        plugins: {
          zoom: {
            zoom: {
              wheel: { enabled: true },
              pinch: { enabled: true },
              mode: 'xy'
            },
            pan: {
              enabled: true,
              mode: 'xy'
            }
          }
        },
        scales: {
          x: { title: { display: true, text: 'Check-in Hour' }, min: 0, max: 23 },
          y: { title: { display: true, text: 'Session Duration (hours)' }, min: 0 }
        }
      }
    });
    window.chartInstance = tutorChart;
    return;
  }

  // Create chart with zoom plugin enabled for all chart types
  const defaultConfig = getDefaultChartConfig();
  tutorChart = new Chart(ctx, {
    type: chartType === 'area' ? 'line' : chartType,
    data: { labels: labels, datasets: datasetsArray },
    options: {
      ...defaultConfig,
      plugins: {
        zoom: {
          zoom: {
            wheel: { enabled: true },
            pinch: { enabled: true },
            mode: 'xy'
          },
          pan: {
            enabled: true,
            mode: 'xy'
          }
        }
      },
      scales: chartType === 'pie' || chartType === 'doughnut' ? {} : {
        y: {
          beginAtZero: true,
          grid: { color: '#f1f5f9' },
          ticks: { color: '#475569' }
        },
        x: {
          grid: { color: '#f1f5f9' },
          ticks: { color: '#475569' }
        }
      }
    }
  });
  
  // Store the chart instance for zoom functionality
  window.chartInstance = tutorChart;
  if (typeof currentChartInstances !== 'undefined') {
    currentChartInstances.singleChart = tutorChart;
  }
}

function renderSplitChart(chartType, rawData, title, isComparisonMode = false, forecastData = null) {
  // For split layout, render the main chart on the left and a comparison chart on the right
  const primaryCtx = document.getElementById('primaryChart')?.getContext('2d');
  const comparisonCtx = document.getElementById('comparisonChart')?.getContext('2d');
  
  if (!primaryCtx || !comparisonCtx) return;
  
  // Destroy all existing chart instances
  if (tutorChart) tutorChart.destroy();
  if (window.chartInstance) window.chartInstance.destroy();
  if (window.comparisonChartInstance) window.comparisonChartInstance.destroy();
  
  // Clear currentChartInstances
  if (typeof currentChartInstances !== 'undefined') {
    Object.values(currentChartInstances).forEach(chart => {
      if (chart && chart.destroy) chart.destroy();
    });
    currentChartInstances = {};
  }
  
  // Clear existing charts
  if (currentChartInstances.primaryChart) currentChartInstances.primaryChart.destroy();
  if (currentChartInstances.comparisonChart) currentChartInstances.comparisonChart.destroy();
  
  // Render primary chart (same as single chart)
  const chartKey = document.getElementById('dataset').value;
  
  // Primary chart - current data
  currentChartInstances.primaryChart = createChartInstance(primaryCtx, chartType, rawData, title, false);
  
  // Comparison chart - show different perspective or time period
  let comparisonData = {};
  let comparisonTitle = "Comparison View";
  
  if (chartKey === 'checkins_per_tutor') {
    // Show hours per tutor as comparison
    comparisonData = rawData; // For now, use same data
    comparisonTitle = "Hours per Tutor";
  } else if (chartKey === 'daily_checkins') {
    // Show daily hours as comparison
    comparisonData = rawData;
    comparisonTitle = "Daily Hours";
  } else {
    // Default: show pie chart version of the data
    comparisonData = rawData;
    comparisonTitle = title + " (Pie View)";
  }
  
  currentChartInstances.comparisonChart = createChartInstance(comparisonCtx, 'pie', comparisonData, comparisonTitle, true);
}

function renderGridChart(chartType, rawData, title, isComparisonMode = false, forecastData = null) {
  // For grid layout, render 6 different charts showing different metrics
  console.log('Rendering grid charts...');
  
  // Verify containers exist
  const containers = ['gridChart1Container', 'gridChart2Container', 'gridChart3Container', 
                     'gridChart4Container', 'gridChart5Container', 'gridChart6Container'];
  const missingContainers = containers.filter(id => !document.getElementById(id));
  if (missingContainers.length > 0) {
    console.error('Missing grid chart containers:', missingContainers);
    return;
  }
  
  // Clear existing charts
  ['gridChart1', 'gridChart2', 'gridChart3', 'gridChart4', 'gridChart5', 'gridChart6'].forEach(chartId => {
    if (currentChartInstances[chartId]) {
      try {
        currentChartInstances[chartId].destroy();
      } catch (e) {
        console.warn(`Error destroying ${chartId}:`, e);
      }
      currentChartInstances[chartId] = null;
    }
  });
  
  // Show loading indicators
  const loadingIndicators = ['gridChart1Container', 'gridChart2Container', 'gridChart3Container', 
                             'gridChart4Container', 'gridChart5Container', 'gridChart6Container'];
  loadingIndicators.forEach(containerId => {
    const container = document.getElementById(containerId);
    if (container) {
      container.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
    }
  });
  
  // Fetch data for different chart types
  fetchGridChartData().then(gridData => {
    console.log('Grid data received:', gridData);
    
    // Helper function to render a chart
    const renderGridChartItem = (chartId, chartType, data, title) => {
      const container = document.getElementById(chartId + 'Container');
      if (!container) {
        console.error(`Container not found: ${chartId}Container`);
        return null;
      }
      
      if (!data || Object.keys(data).length === 0) {
        container.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 text-muted"><small>No data available</small></div>';
        return null;
      }
      
      // Ensure canvas exists
      let canvas = document.getElementById(chartId);
      if (!canvas) {
        container.innerHTML = `<canvas id="${chartId}"></canvas>`;
        canvas = document.getElementById(chartId);
      }
      
      if (!canvas) {
        console.error(`Canvas not found: ${chartId}`);
        return null;
      }
      
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        console.error(`Context not available for: ${chartId}`);
        return null;
      }
      
      return createChartInstance(ctx, chartType, data, title, false);
    };
    
    // Chart 1: Appointments per Tutor (Bar)
    currentChartInstances.gridChart1 = renderGridChartItem(
      'gridChart1', 'bar', 
      gridData.appointments_per_tutor || {}, 
      'Appointments per Tutor'
    );
    
    // Chart 2: Hours per Tutor (Pie)
    currentChartInstances.gridChart2 = renderGridChartItem(
      'gridChart2', 'pie', 
      gridData.hours_per_tutor || {}, 
      'Scheduled Hours per Tutor'
    );
    
    // Chart 3: Daily Appointments (Line)
    currentChartInstances.gridChart3 = renderGridChartItem(
      'gridChart3', 'line', 
      gridData.daily_appointments || {}, 
      'Daily Appointments'
    );
    
    // Chart 4: Appointments by Status (Pie)
    currentChartInstances.gridChart4 = renderGridChartItem(
      'gridChart4', 'pie', 
      gridData.appointments_by_status || {}, 
      'Appointments by Status'
    );
    
    // Chart 5: Course Popularity (Bar)
    currentChartInstances.gridChart5 = renderGridChartItem(
      'gridChart5', 'bar', 
      gridData.course_popularity || {}, 
      'Course Popularity'
    );
    
    // Chart 6: Hourly Distribution (Bar)
    currentChartInstances.gridChart6 = renderGridChartItem(
      'gridChart6', 'bar', 
      gridData.hourly_appointments_dist || {}, 
      'Hourly Distribution'
    );
    
    console.log('Grid charts rendered:', {
      chart1: !!currentChartInstances.gridChart1,
      chart2: !!currentChartInstances.gridChart2,
      chart3: !!currentChartInstances.gridChart3,
      chart4: !!currentChartInstances.gridChart4,
      chart5: !!currentChartInstances.gridChart5,
      chart6: !!currentChartInstances.gridChart6
    });
    
  }).catch(error => {
    console.error('Error fetching grid chart data:', error);
    // Show error in all containers
    ['gridChart1Container', 'gridChart2Container', 'gridChart3Container', 
     'gridChart4Container', 'gridChart5Container', 'gridChart6Container'].forEach(containerId => {
      const container = document.getElementById(containerId);
      if (container) {
        container.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 text-danger"><small>Error loading data</small></div>';
      }
    });
  });
}

function createChartInstance(ctx, chartType, data, title, isComparison = false) {
  if (!data || Object.keys(data).length === 0) {
    return null;
  }
  
  const labels = Object.keys(data);
  const values = Object.values(data);
  
  const singleBackgroundColor = isDarkMode() ? 'rgba(255, 159, 64, 0.7)' : 'rgba(0, 188, 212, 0.7)';
  const singleBorderColor = isDarkMode() ? 'rgba(255, 159, 64, 1)' : 'rgba(0, 188, 212, 1)';
  
  const datasets = [{
    label: title,
    data: values,
    backgroundColor: chartType === 'pie' ? generateColors(values.length) : singleBackgroundColor,
    borderColor: chartType === 'pie' ? generateColors(values.length, true) : singleBorderColor,
    borderWidth: 1,
    tension: 0.4
  }];
  
  const defaultConfig = getDefaultChartConfig();
  
  // Check if this is a grid chart (smaller, more compact)
  const isGridChart = ctx.canvas.id && ctx.canvas.id.startsWith('gridChart');
  
  const chartOptions = {
    ...defaultConfig,
    maintainAspectRatio: true,
    responsive: true,
    scales: chartType === 'pie' || chartType === 'doughnut' ? {} : {
      x: { 
        ticks: { 
          color: '#1e293b', 
          font: { 
            family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            size: isGridChart ? 9 : 11 
          },
          maxRotation: isGridChart ? 45 : 0,
          autoSkip: isGridChart
        },
        grid: { color: 'rgba(0,0,0,0.1)' }
      },
      y: { 
        beginAtZero: true,
        ticks: { 
          color: '#1e293b', 
          font: { size: isGridChart ? 9 : 11 }
        },
        grid: { color: 'rgba(0,0,0,0.1)' }
      }
    },
    plugins: {
      ...defaultConfig.plugins,
      legend: { 
        position: chartType === 'pie' || chartType === 'doughnut' ? 'bottom' : 'top',
        labels: { 
          color: '#1e293b', 
          boxWidth: isGridChart ? 10 : 12, 
          padding: isGridChart ? 8 : 10, 
          font: { 
            family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            size: isGridChart ? 9 : 11 
          },
          usePointStyle: isGridChart
        },
        display: !isGridChart || chartType === 'pie' || chartType === 'doughnut'
      },
      tooltip: {
        ...defaultConfig.plugins.tooltip,
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) label += ': ';
            if (context.parsed.y !== null && context.parsed.y !== undefined) {
              label += context.parsed.y.toFixed(2);
            } else if (context.raw !== null && context.raw !== undefined) {
              label += parseFloat(context.raw).toFixed(2);
            }
            return label;
          }
        }
      },
      zoom: isGridChart ? {} : { 
        pan: { enabled: true, mode: 'xy' }, 
        zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'xy' } 
      }
    }
  };
  
  const chartInstance = new Chart(ctx, {
    type: chartType === 'area' ? 'line' : chartType,
    data: { labels: labels, datasets: datasets },
    options: chartOptions
  });
  
  // Store chart instance in global variables for proper cleanup
  if (isComparison) {
    window.comparisonChartInstance = chartInstance;
  } else {
    window.chartInstance = chartInstance;
  }
  
  return chartInstance;
}

async function fetchGridChartData() {
  // Get current form data
  const form = document.getElementById('filterForm');
  const formData = new FormData(form);
  const params = new URLSearchParams();
  
  // Add form data to params
  for (let [key, value] of formData.entries()) {
    if (value.trim()) params.append(key, value.trim());
  }
  
  // Add advanced filters
  const advancedFilters = JSON.parse(sessionStorage.getItem('advancedFilters') || '{}');
  Object.entries(advancedFilters).forEach(([key, value]) => {
    if (value && value !== '') params.append(key, value);
  });

  // --- FIX: Always send grid mode for grid chart ---
  const bodyObj = Object.fromEntries(params);
  bodyObj.mode = 'grid';

  try {
    const response = await fetch('/chart-data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyObj)
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Error fetching grid chart data:', error);
    return {};
  }
}

function generateColors(num, border = false, index = -1) { /* ... same as before ... */
    // Improved palette: 20-color Set3-like with better contrast for doughnut/pie
    const baseColors = [
        'rgba(141, 211, 199, DYNAMIC_ALPHA)', 'rgba(255, 255, 179, DYNAMIC_ALPHA)',
        'rgba(190, 186, 218, DYNAMIC_ALPHA)', 'rgba(251, 128, 114, DYNAMIC_ALPHA)',
        'rgba(128, 177, 211, DYNAMIC_ALPHA)', 'rgba(253, 180, 98, DYNAMIC_ALPHA)',
        'rgba(179, 222, 105, DYNAMIC_ALPHA)', 'rgba(252, 205, 229, DYNAMIC_ALPHA)',
        'rgba(217, 217, 217, DYNAMIC_ALPHA)', 'rgba(188, 128, 189, DYNAMIC_ALPHA)',
        'rgba(204, 235, 197, DYNAMIC_ALPHA)', 'rgba(255, 237, 111, DYNAMIC_ALPHA)',
        'rgba(166, 206, 227, DYNAMIC_ALPHA)', 'rgba(31, 120, 180, DYNAMIC_ALPHA)',
        'rgba(178, 223, 138, DYNAMIC_ALPHA)', 'rgba(251, 154, 153, DYNAMIC_ALPHA)',
        'rgba(227, 26, 28, DYNAMIC_ALPHA)', 'rgba(253, 191, 111, DYNAMIC_ALPHA)',
        'rgba(255, 127, 0, DYNAMIC_ALPHA)', 'rgba(202, 178, 214, DYNAMIC_ALPHA)'
    ];
    const alpha = border ? '1' : '0.7';
    if (index !== -1) return baseColors[index % baseColors.length].replace('DYNAMIC_ALPHA', alpha);
    return Array.from({ length: num }, (_, i) => baseColors[i % baseColors.length].replace('DYNAMIC_ALPHA', alpha));
}

function updateChartTypeOptions(selectedDataset) { /* ... same as before ... */
  const chartTypeSelect = document.getElementById('chartTypeSelect');
  const currentValue = chartTypeSelect.value;
  chartTypeSelect.innerHTML = ''; 
  const availableTypes = chartOptions[selectedDataset] || ['bar']; 
  availableTypes.forEach(type => {
    const opt = document.createElement('option');
    opt.value = type; opt.text = type.charAt(0).toUpperCase() + type.slice(1);
    chartTypeSelect.appendChild(opt);
  });
  if (availableTypes.includes(currentValue)) chartTypeSelect.value = currentValue;
  else if (availableTypes.length > 0) chartTypeSelect.value = availableTypes[0]; 
}

function fetchChartData(query = '', chartType = 'bar', chartKey = 'checkins_per_tutor') {
  const payload = Object.fromEntries(new URLSearchParams(query));
  payload.dataset = chartKey; // Use 'dataset' to match backend expectation 
  // Include the currently selected chart type so backend can echo it back
  const chartTypeSelectEl = document.getElementById('chartTypeSelect');
  if (chartTypeSelectEl && chartTypeSelectEl.value) {
    payload.chart_type = chartTypeSelectEl.value;
  } else if (chartType) {
    payload.chart_type = chartType;
  }
  
  // Include advanced filters from sessionStorage
  const advancedFilters = JSON.parse(sessionStorage.getItem('advancedFilters') || '{}');
  Object.assign(payload, advancedFilters);
  
  console.log('Sending payload to backend:', payload); // Debug log
  
  const tutorChartElement = document.getElementById('tutorChart');
  if (tutorChartElement && tutorChartElement.parentElement) {
    tutorChartElement.parentElement.innerHTML = '<div class="text-center p-5"><div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Loading chart data...</p></div>'; // Replace canvas with spinner
  }

  fetch(`/chart-data`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then(res => {
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      return res.json();
    })
    .then(data => {
      // Re-create canvas before rendering
      document.getElementById('tutorChartContainer').innerHTML = '<canvas id="tutorChart"></canvas>';
      
      // Handle new structured response format
      let dataset, chartType, title, isComparison, forecast;
      
      if (data.chart_data && data.chart_type && data.title) {
        // New structured format
        dataset = data.chart_data;
        chartType = data.chart_type;
        title = data.title;
        isComparison = data.comparison_mode || false;
        forecast = data.forecast_data || null;
      } else if (data[chartKey]) {
        // Legacy format (fallback)
        dataset = data[chartKey];
        chartType = chartType;
        title = chartTitles[chartKey] || "Chart";
        isComparison = data.is_comparison_mode || false;
        forecast = data.forecast_daily_checkins || null;
      } else {
        console.error("No valid data found in response:", data);
        throw new Error(`No data for chart key "${chartKey}".`);
      }

      // If the caller requested a specific chart type, prefer it
      if (payload.chart_type) {
        chartType = payload.chart_type;
      }

      if (dataset === undefined || dataset === null) {
          console.error("Dataset is null or undefined:", dataset);
          throw new Error(`No data for chart key "${chartKey}".`);
      }
      
      renderChart(chartType, dataset, title, isComparison, forecast);
      // raw_records_for_chart_context can be used here if a chart needs to display some of its underlying points,
      // but not for rendering a full table anymore.
      // Example: you might update a small div with top 5 records relevant to the chart.
    })
    .catch(err => {
      console.error('Chart load failed:', err);
      document.getElementById('tutorChartContainer').innerHTML = '<canvas id="tutorChart"></canvas>'; // Restore canvas
      const chartTitleEl = document.getElementById('chartTitle');
      if (chartTitleEl) chartTitleEl.innerText = "Could not load chart data. " + err.message;
      document.getElementById('totalCount').textContent = '';
      document.getElementById('chartSummaryTable').innerHTML = `<p class="text-danger">Error: ${err.message}</p>`;
    });
}

// Snapshot modal (if needed for some chart interaction, though less likely now)
function showSnapshotModal(src) {
    const modal = new bootstrap.Modal(document.getElementById('chartsSnapshotModal'));
    document.getElementById('chartsModalImage').src = src.startsWith('http') || src.startsWith('/') ? src : `/static/${src}`;
    modal.show();
}

// Expose functions to global scope
window.renderChart = renderChart;
window.renderSingleChart = renderSingleChart;
window.renderSplitChart = renderSplitChart;
window.renderGridChart = renderGridChart;
window.createChartInstance = createChartInstance;
window.updateChartTypeOptions = updateChartTypeOptions;
window.fetchChartData = fetchChartData;

function downloadChartImage() { /* ... same as before ... */
  if (!tutorChart || !tutorChart.canvas) { alert("No chart to download."); return; }
  const url = tutorChart.toBase64Image();
  const link = document.createElement('a');
  const selectedDataset = document.getElementById('dataset').value;
  const filename = (chartTitles[selectedDataset] || "chart").replace(/[^a-z0-9]/gi, '_').toLowerCase();
  link.download = `${filename}.png`; link.href = url; link.click();
}

function exportChartDataCSV() { /* ... same as before ... */
    if (!tutorChart || !tutorChart.data || !tutorChart.data.labels || !tutorChart.data.datasets) {
        alert("No chart data to export."); return;
    }
    const { labels, datasets } = tutorChart.data;
    let csvContent = "data:text/csv;charset=utf-8,";
    const headerRow = ["Label", ...datasets.map(ds => ds.label || "Value")].join(",");
    csvContent += headerRow + "\r\n";
    labels.forEach((label, index) => {
        const rowData = [label];
        datasets.forEach(dataset => {
            rowData.push(dataset.data[index] !== null && dataset.data[index] !== undefined ? dataset.data[index] : "");
        });
        csvContent += rowData.join(",") + "\r\n";
    });
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    const selectedDataset = document.getElementById('dataset').value;
    const filename = (chartTitles[selectedDataset] || "chart_data").replace(/[^a-z0-9]/gi, '_').toLowerCase();
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${filename}.csv`);
    document.body.appendChild(link); link.click(); document.body.removeChild(link);
}

// Export Filtered Raw Data used for Charts
async function exportChartUnderlyingDataCSV() {
    const form = document.getElementById('filterForm');
    const params = new URLSearchParams(new FormData(form)); // Use chart filters
    // This button now calls the specific export endpoint
    try {
        const response = await fetch('/export-filtered-data-csv', {
            method: 'POST',
            body: params // Send current chart filters
        });
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Export failed: ${response.status} - ${errorText}`);
        }
        const blob = await response.blob();
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'chart_underlying_data.csv';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    } catch (error) {
        console.error('Error exporting chart underlying data CSV:', error);
        alert(`Could not export data: ${error.message}`);
    }
}


function toggleTheme() {
  // Use the new theme switcher if available
  if (window.themeSwitcher && typeof window.themeSwitcher.toggleTheme === 'function') {
    window.themeSwitcher.toggleTheme();
  } else {
    // Fallback to data-theme attribute
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Update theme toggle button if exists
    const themeBtn = document.getElementById('themeToggleBtn');
    if (themeBtn) {
      themeBtn.innerHTML = newTheme === 'dark' 
        ? '<i class="fas fa-sun"></i> Light Mode' 
        : '<i class="fas fa-moon"></i> Dark Mode';
    }
    
    // Trigger theme change event
    document.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: newTheme } }));
  }
}

async function initTutorAutocomplete() { /* ... same as before ... */
    const tutorInput = document.getElementById('tutor_id');
    const tutorDatalist = document.getElementById('tutorList');
    if (!tutorInput || !tutorDatalist) return;
    try {
        const response = await fetch('/get-tutors');
        const tutors = await response.json();
        tutorDatalist.innerHTML = '';
        tutors.forEach(tutor => {
            const option = document.createElement('option');
            option.value = tutor.tutor_id;
            option.textContent = `${tutor.tutor_name} (${tutor.tutor_id})`;
            tutorDatalist.appendChild(option);
        });
    } catch (error) { console.error("Failed to load tutors for autocomplete:", error); }
}

function exportFiltersLink() { /* ... same as before ... */
    const form = document.getElementById('filterForm');
    const params = new URLSearchParams();
    // Collect all relevant filter values from form
    const formData = new FormData(form);
    for (const [key, value] of formData.entries()) {
        if (value && String(value).trim() !== '') {
             // Special handling for dataset and chart_type if names are different
            if (key === "tutor_id") params.append('tutor_ids', value);
            else if (key === "chart_type" && form.elements["chartTypeSelect"]) params.append('chart_type', form.elements["chartTypeSelect"].value);
            else params.append(key, value);
        }
    }
    const queryString = params.toString();
    const shareableLink = `${window.location.origin}${window.location.pathname}?${queryString}`;
    navigator.clipboard.writeText(shareableLink).then(() => {
        alert("Shareable link with current filters copied to clipboard!");
    }).catch(err => { prompt("Copy this link:", shareableLink); });
}

// --- Punctuality Analysis Fetch and Update ---
async function loadPunctualityAnalysis(params = '') {
  try {
    let body = { dataset: 'punctuality_analysis' };
    if (params && typeof params === 'string' && params.length > 0) {
      params.split('&').forEach(pair => {
        const [key, value] = pair.split('=');
        if (key && value) body[key] = decodeURIComponent(value);
      });
    }
    const res = await fetch('/chart-data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    const pa = data.punctuality_analysis || {};
    // Update the cards (only if elements exist)
    const earlyPercentage = document.getElementById('earlyPercentage');
    const ontimePercentage = document.getElementById('ontimePercentage');
    const latePercentage = document.getElementById('latePercentage');
    const earlyCount = document.getElementById('earlyCount');
    const ontimeCount = document.getElementById('ontimeCount');
    const lateCount = document.getElementById('lateCount');
    if (earlyPercentage) earlyPercentage.textContent = pa.Early !== undefined ? pa.Early : '-';
    if (ontimePercentage) ontimePercentage.textContent = pa['On Time'] !== undefined ? pa['On Time'] : '-';
    if (latePercentage) latePercentage.textContent = pa.Late !== undefined ? pa.Late : '-';
    if (earlyCount) earlyCount.textContent = (pa.Early !== undefined ? pa.Early : '-') + ' sessions';
    if (ontimeCount) ontimeCount.textContent = (pa['On Time'] !== undefined ? pa['On Time'] : '-') + ' sessions';
    if (lateCount) lateCount.textContent = (pa.Late !== undefined ? pa.Late : '-') + ' sessions';
  } catch (error) {
    const earlyPercentage = document.getElementById('earlyPercentage');
    const ontimePercentage = document.getElementById('ontimePercentage');
    const latePercentage = document.getElementById('latePercentage');
    const earlyCount = document.getElementById('earlyCount');
    const ontimeCount = document.getElementById('ontimeCount');
    const lateCount = document.getElementById('lateCount');
    if (earlyPercentage) earlyPercentage.textContent = '-';
    if (ontimePercentage) ontimePercentage.textContent = '-';
    if (latePercentage) latePercentage.textContent = '-';
    if (earlyCount) earlyCount.textContent = '- sessions';
    if (ontimeCount) ontimeCount.textContent = '- sessions';
    if (lateCount) lateCount.textContent = '- sessions';
  }
}

function updatePunctualityAnalysis(punctualityAnalysis) {
  if (!punctualityAnalysis || !punctualityAnalysis.breakdown) {
    ['earlyPercentage', 'ontimePercentage', 'latePercentage'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '-';
    });
    ['earlyCount', 'ontimeCount', 'lateCount'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '- sessions';
    });
    return;
  }
  const breakdown = punctualityAnalysis.breakdown;
  // Early
  const early = breakdown['Early'] || {};
  const earlyCount = document.getElementById('earlyCount');
  const earlyPercentage = document.getElementById('earlyPercentage');
  if (earlyCount) earlyCount.textContent = (early.count !== undefined ? early.count : '-') + ' sessions';
  if (earlyPercentage) earlyPercentage.textContent = (early.percent !== undefined ? early.percent + '%' : '-');
  // On Time
  const ontime = breakdown['On Time'] || {};
  const ontimeCount = document.getElementById('ontimeCount');
  const ontimePercentage = document.getElementById('ontimePercentage');
  if (ontimeCount) ontimeCount.textContent = (ontime.count !== undefined ? ontime.count : '-') + ' sessions';
  if (ontimePercentage) ontimePercentage.textContent = (ontime.percent !== undefined ? ontime.percent + '%' : '-');
  // Late
  const late = breakdown['Late'] || {};
  const lateCount = document.getElementById('lateCount');
  const latePercentage = document.getElementById('latePercentage');
  if (lateCount) lateCount.textContent = (late.count !== undefined ? late.count : '-') + ' sessions';
  if (latePercentage) latePercentage.textContent = (late.percent !== undefined ? late.percent + '%' : '-');
}

function showPunctualityDetails(section) {
  fetch('/chart-data', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dataset: 'punctuality_analysis' })
  })
  .then(response => response.json())
  .then(data => {
    const punctualityData = data.punctuality_analysis || {};
    const breakdown = punctualityData.breakdown || {};
    const cats = ['Early', 'On Time', 'Late'];
    cats.forEach(cat => {
      const idPrefix = cat.toLowerCase().replace(' ', '');
      document.getElementById(idPrefix + 'DetailCount').textContent = (breakdown[cat]?.count ?? '-');
      document.getElementById(idPrefix + 'DetailPercent').textContent = (breakdown[cat]?.percent ?? '-') + '%';
      document.getElementById(idPrefix + 'DetailAvg').textContent = (breakdown[cat]?.avg_deviation ?? '-');
    });
    // Donut chart
    const ctx = document.getElementById('punctualityChart');
    if (ctx) {
      if (window.punctualityChartInstance) window.punctualityChartInstance.destroy();
      const defaultConfig = getDefaultChartConfig();
      window.punctualityChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: cats,
          datasets: [{
            data: cats.map(cat => breakdown[cat]?.count ?? 0),
            backgroundColor: ['#28a745', '#17a2b8', '#dc3545'],
            borderWidth: 2,
            borderColor: '#fff'
          }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
      });
    }
    // Trends chart
    const trendCtx = document.getElementById('punctualityTrendCanvas');
    if (trendCtx) {
      if (window.punctualityTrendChartInstance) window.punctualityTrendChartInstance.destroy();
      const days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
      const defaultConfig = getDefaultChartConfig();
      window.punctualityTrendChartInstance = new Chart(trendCtx, {
        type: 'line',
        data: {
          labels: days.map(d => d.slice(0,3)),
          datasets: cats.map((cat, idx) => ({
            label: cat + ' %',
            data: (punctualityData.trends && punctualityData.trends[cat]) ? punctualityData.trends[cat] : Array(7).fill(0),
            borderColor: ['#28a745', '#17a2b8', '#dc3545'][idx],
            backgroundColor: ['rgba(40,167,69,0.1)','rgba(23,162,184,0.1)','rgba(220,53,69,0.1)'][idx],
            tension: 0.4
          }))
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: { y: { beginAtZero: true, max: 100, ticks: { callback: v => v + '%' } } },
          plugins: { legend: { display: true, position: 'bottom' } }
        }
      });
    }
    // Day/Time grouped bar chart
    const dayTimeCtx = document.getElementById('punctualityDayTimeChart');
    if (dayTimeCtx) {
      if (window.punctualityDayTimeChartInstance) window.punctualityDayTimeChartInstance.destroy();
      const dayLabels = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
      const slots = ['Morning','Afternoon','Evening'];
      const defaultConfig = getDefaultChartConfig();
      window.punctualityDayTimeChartInstance = new Chart(dayTimeCtx, {
        type: 'bar',
        data: {
          labels: dayLabels,
          datasets: slots.map((slot, idx) => ({
            label: slot,
            data: (punctualityData.day_time && punctualityData.day_time[slot]) ? punctualityData.day_time[slot] : Array(7).fill(0),
            backgroundColor: ['rgba(40,167,69,0.7)','rgba(23,162,184,0.7)','rgba(220,53,69,0.7)'][idx],
            borderRadius: 4,
            barPercentage: 0.7,
            categoryPercentage: 0.5
          }))
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: true, position: 'bottom' } },
          scales: { y: { beginAtZero: true, max: 100, ticks: { callback: v => v + '%' } } }
        }
      });
    }
    // Outliers/top performers
    const mostPunctual = (punctualityData.outliers && punctualityData.outliers.most_punctual) || [];
    const leastPunctual = (punctualityData.outliers && punctualityData.outliers.least_punctual) || [];
    document.getElementById('mostPunctualList').textContent = mostPunctual.length ? mostPunctual.join(', ') : '-';
    document.getElementById('leastPunctualList').textContent = leastPunctual.length ? leastPunctual.join(', ') : '-';
    // Deviation distribution bar chart
    const devDistCtx = document.getElementById('punctualityDeviationChart');
    if (devDistCtx) {
      if (window.punctualityDeviationChartInstance) window.punctualityDeviationChartInstance.destroy();
      const devLabels = ['Early >15min', 'Early 5-15min', 'On Time ±5min', 'Late 5-15min', 'Late >15min'];
      const devData = devLabels.map(l => (punctualityData.deviation_distribution && punctualityData.deviation_distribution[l]) || 0);
      const defaultConfig = getDefaultChartConfig();
      window.punctualityDeviationChartInstance = new Chart(devDistCtx, {
        type: 'bar',
        data: {
          labels: devLabels,
          datasets: [{
            label: 'Sessions',
            data: devData,
            backgroundColor: [
              'rgba(40,167,69,0.7)', 'rgba(40,167,69,0.4)',
              'rgba(23,162,184,0.7)',
              'rgba(220,53,69,0.4)', 'rgba(220,53,69,0.7)'
            ],
            borderRadius: 4
          }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
      });
    }
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('punctualityModal'));
    modal.show();
    // Activate the correct tab
    setTimeout(() => {
      let tabId = 'tab-breakdown';
      if (section === 'trends') tabId = 'tab-trends';
      else if (section === 'daytime') tabId = 'tab-daytime';
      else if (section === 'outliers') tabId = 'tab-outliers';
      else if (section === 'deviation') tabId = 'tab-deviation';
      const tabEl = document.getElementById(tabId);
      if (tabEl) {
        const tab = new bootstrap.Tab(tabEl);
        tab.show();
      }
    }, 400);
  });
}

function exportPunctualityData(tab) {
  // If no tab argument, detect the active tab
  if (!tab) {
    const activeTab = document.querySelector('#punctualityTabNav .nav-link.active');
    if (activeTab) {
      if (activeTab.id === 'tab-breakdown') tab = 'breakdown';
      else if (activeTab.id === 'tab-trends') tab = 'trends';
      else if (activeTab.id === 'tab-daytime') tab = 'daytime';
      else if (activeTab.id === 'tab-outliers') tab = 'outliers';
      else if (activeTab.id === 'tab-deviation') tab = 'deviation';
    }
  }
  // Collect current filter form values
  const form = document.getElementById('filterForm');
  const formData = new FormData(form);
  formData.append('tab', tab);
  fetch('/export-punctuality-csv', {
    method: 'POST',
    body: formData
  })
  .then(response => {
    if (!response.ok) throw new Error('Export failed');
    return response.blob();
  })
  .then(blob => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `punctuality_${tab}.csv`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 100);
  })
  .catch(error => {
    alert('Could not export punctuality data: ' + error.message);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('filterForm');
  const datasetSelect = document.getElementById('dataset');
  const chartTypeSelect = document.getElementById('chartTypeSelect');

  // Use data-theme attribute instead of dark-mode class
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  
  // Update theme toggle button if exists
  const themeBtn = document.getElementById('themeToggleBtn');
  if (themeBtn) {
    themeBtn.innerHTML = savedTheme === 'dark'
      ? '<i class="fas fa-sun"></i> Light Mode'
      : '<i class="fas fa-moon"></i> Dark Mode';
  }

  initTutorAutocomplete(); 

  document.getElementById('todayBtn')?.addEventListener('click', () => { /* ... */ 
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('start_date').value = today; document.getElementById('end_date').value = today;
    form.dispatchEvent(new Event('submit', { bubbles: true }));
  });
  document.getElementById('thisWeekBtn')?.addEventListener('click', () => { /* ... */ 
    const today = new Date(), dayOfWeek = today.getDay();
    const startDate = new Date(today); startDate.setDate(today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1));
    const endDate = new Date(startDate); endDate.setDate(startDate.getDate() + 6);
    document.getElementById('start_date').value = startDate.toISOString().split('T')[0];
    document.getElementById('end_date').value = endDate.toISOString().split('T')[0];
    form.dispatchEvent(new Event('submit', { bubbles: true }));
  });
  document.getElementById('thisMonthBtn')?.addEventListener('click', () => { /* ... */
    const today = new Date(), year = today.getFullYear(), month = today.getMonth();
    const startDate = new Date(year, month, 1), endDate = new Date(year, month + 1, 0);
    document.getElementById('start_date').value = startDate.toISOString().split('T')[0];
    document.getElementById('end_date').value = endDate.toISOString().split('T')[0];
    form.dispatchEvent(new Event('submit', { bubbles: true }));
  });
  document.getElementById('last7DaysBtn')?.addEventListener('click', () => { /* ... */
    const endDate = new Date(), startDate = new Date(); startDate.setDate(endDate.getDate() - 6);
    document.getElementById('start_date').value = startDate.toISOString().split('T')[0];
    document.getElementById('end_date').value = endDate.toISOString().split('T')[0];
    form.dispatchEvent(new Event('submit', { bubbles: true }));
  });

  document.getElementById('exportFiltersLinkBtn')?.addEventListener('click', exportFiltersLink);
  document.getElementById('exportChartCSVBtn')?.addEventListener('click', exportChartDataCSV);
  document.getElementById('exportChartUnderlyingTableCSVBtn')?.addEventListener('click', exportChartUnderlyingDataCSV); // Changed ID

  datasetSelect.addEventListener('change', () => {
      updateChartTypeOptions(datasetSelect.value);
      // Build params from current form values
      const params = new URLSearchParams();
      // Handle tutor_ids from the multi-select functionality
      const tutorIdsInput = form.querySelector('input[name="tutor_ids"]');
      if (tutorIdsInput && tutorIdsInput.value.trim()) {
        params.append('tutor_ids', tutorIdsInput.value.trim());
      }
      if (form.start_date.value.trim()) params.append('start_date', form.start_date.value.trim());
      if (form.end_date.value.trim()) params.append('end_date', form.end_date.value.trim());
      if (form.duration.value.trim()) params.append('duration', form.duration.value.trim());
      if (form.day_type.value.trim()) params.append('day_type', form.day_type.value.trim());
      if (form.shift_start_hour.value !== '0') params.append('shift_start_hour', form.shift_start_hour.value);
      if (form.shift_end_hour.value !== '23') params.append('shift_end_hour', form.shift_end_hour.value);
      form.dispatchEvent(new Event('submit', { bubbles: true }));
      loadPunctualityAnalysis(params.toString());
  });
  chartTypeSelect.addEventListener('change', () => form.dispatchEvent(new Event('submit', { bubbles: true })));

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    const params = new URLSearchParams();
    
    // Handle tutor_ids from the multi-select functionality
    const tutorIdsInput = this.querySelector('input[name="tutor_ids"]');
    if (tutorIdsInput && tutorIdsInput.value.trim()) {
      params.append('tutor_ids', tutorIdsInput.value.trim());
    }
    
    // Handle other form fields
    if (this.start_date.value.trim()) params.append('start_date', this.start_date.value.trim());
    if (this.end_date.value.trim()) params.append('end_date', this.end_date.value.trim());
    if (this.duration.value.trim()) params.append('duration', this.duration.value.trim());
    if (this.day_type.value.trim()) params.append('day_type', this.day_type.value.trim());
    if (this.shift_start_hour.value !== '0') params.append('shift_start_hour', this.shift_start_hour.value);
    if (this.shift_end_hour.value !== '23') params.append('shift_end_hour', this.shift_end_hour.value);
    
    fetchChartData(params.toString(), this.chartTypeSelect.value, this.dataset.value);
    if (typeof updateFilterChips === 'function') {
      updateFilterChips();
    }
    loadPunctualityAnalysis(params.toString());
  });

  document.getElementById('resetBtn')?.addEventListener('click', () => {
    // Clear selected tutors
    if (typeof selectedTutors !== 'undefined') {
      selectedTutors = [];
      updateSelectedTutorsDisplay();
      updateTutorIdInput();
    }
    
    // Clear other form fields
    ['tutor_id', 'start_date', 'end_date', 'duration', 'day_type', 'shift_start_hour', 'shift_end_hour'].forEach(id => {
      const element = document.getElementById(id);
      if (element) {
        if (element.type === 'range') {
            if (id === 'shift_start_hour') element.value = '0'; 
            if (id === 'shift_end_hour') element.value = '23';
            document.getElementById(id === 'shift_start_hour' ? 'shiftStartTimeDisplay' : 'shiftEndTimeDisplay').textContent = (id === 'shift_start_hour' ? '00' : '23') + ':00';
        } else { element.value = ''; }
      }
    });
    
    form.dispatchEvent(new Event('submit', { bubbles: true }));
  });
  
  const shiftStartHourInput = document.getElementById('shift_start_hour');
  const shiftEndHourInput = document.getElementById('shift_end_hour');
  const shiftStartTimeDisplay = document.getElementById('shiftStartTimeDisplay');
  const shiftEndTimeDisplay = document.getElementById('shiftEndTimeDisplay');
  if(shiftStartHourInput && shiftStartTimeDisplay) shiftStartHourInput.addEventListener('input', () => shiftStartTimeDisplay.textContent = `${String(shiftStartHourInput.value).padStart(2, '0')}:00`);
  if(shiftEndHourInput && shiftEndTimeDisplay) shiftEndHourInput.addEventListener('input', () => shiftEndTimeDisplay.textContent = `${String(shiftEndHourInput.value).padStart(2, '0')}:00`);

  const urlParams = new URLSearchParams(window.location.search);
  let shouldSubmit = false;
  urlParams.forEach((value, key) => {
      let formKey = key;
      if (key === 'tutor_ids') formKey = 'tutor_id'; // Map URL param to form field name
      const element = form.elements[formKey];
      if (element) {
          if (formKey === 'dataset') {
              element.value = value;
              updateChartTypeOptions(value);
              if (urlParams.has('chart_type')) form.elements['chartTypeSelect'].value = urlParams.get('chart_type');
          } else if (formKey === 'chart_type') {
             // Already handled if dataset is present, otherwise set it directly
             if (!urlParams.has('dataset')) form.elements['chartTypeSelect'].value = value;
          } else {
              element.value = value;
          }
          // Update range slider display if values are from URL
          if (formKey === 'shift_start_hour' && shiftStartTimeDisplay) shiftStartTimeDisplay.textContent = `${String(value).padStart(2, '0')}:00`;
          if (formKey === 'shift_end_hour' && shiftEndTimeDisplay) shiftEndTimeDisplay.textContent = `${String(value).padStart(2, '0')}:00`;
          shouldSubmit = true;
      }
  });
  
  updateChartTypeOptions(datasetSelect.value); 
  if (typeof updateFilterChips === 'function') {
    updateFilterChips();
  }

  if (shouldSubmit) form.dispatchEvent(new Event('submit', { bubbles: true }));
  else form.dispatchEvent(new Event('submit', { bubbles: true })); // Initial load

  // Initial load
  loadPunctualityAnalysis();
});