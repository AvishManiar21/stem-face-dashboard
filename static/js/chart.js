let tutorChart;

function isDarkMode() {
  return document.documentElement.classList.contains('dark-mode');
}

const chartOptions = {
  checkins_per_tutor: ['bar', 'pie'],
  hours_per_tutor: ['bar', 'pie'],
  daily_checkins: ['bar', 'line'],
  daily_hours: ['bar', 'line', 'area'],
  cumulative_checkins: ['line', 'area'],
  cumulative_hours: ['line', 'area'],
  hourly_checkins_dist: ['bar', 'line'],
  monthly_hours: ['bar', 'line'],
  avg_hours_per_day_of_week: ['bar', 'pie'],
  checkins_per_day_of_week: ['bar', 'pie'],
  hourly_activity_by_day: ['bar', 'line'], // Grouped bar or multi-line
  forecast_daily_checkins: ['line'] 
};

const chartTitles = {
  checkins_per_tutor: "Check-ins per Tutor",
  hours_per_tutor: "Hours per Tutor",
  daily_checkins: "Daily Check-ins",
  daily_hours: "Daily Hours",
  cumulative_checkins: "Cumulative Check-ins",
  cumulative_hours: "Cumulative Hours",
  hourly_checkins_dist: "Hourly Check-Ins Distribution (Overall)",
  monthly_hours: "Monthly Hours",
  avg_hours_per_day_of_week: "Average Session Hours per Day of Week",
  checkins_per_day_of_week: "Check-ins per Day of Week",
  hourly_activity_by_day: "Hourly Activity by Day of Week",
  forecast_daily_checkins: "Daily Check-ins Forecast (Experimental)"
};

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

  if (tutorChart) tutorChart.destroy();
  if (summaryTableDiv) summaryTableDiv.innerHTML = '';

  let labels, datasetsArray;

  if (!rawData || (typeof rawData === 'object' && Object.keys(rawData).length === 0 && !isComparisonMode) || (Array.isArray(rawData) && rawData.length === 0) ) {
    chartTitleEl.innerText = "No data for this filter or chart type.";
    totalCountSpan.textContent = '';
    if (ctx) ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    return;
  }
  
  const chartKey = document.getElementById('dataset').value; // Get current chart key

  if (isComparisonMode && (chartKey === 'daily_checkins' || chartKey === 'daily_hours') && typeof rawData === 'object' && Object.keys(rawData).length > 0) {
    const allLabelsSet = new Set();
    Object.values(rawData).forEach(tutorData => Object.keys(tutorData).forEach(label => allLabelsSet.add(label)));
    labels = Array.from(allLabelsSet).sort();

    datasetsArray = Object.entries(rawData).map(([tutorName, tutorData], index) => {
        const dataPoints = labels.map(label => tutorData[label] || 0);
        const color = متنوعColors(Object.keys(rawData).length, false, index);
        const borderColor = متنوعColors(Object.keys(rawData).length, true, index);
        return {
            label: tutorName, data: dataPoints, fill: chartType === 'area',
            backgroundColor: color, borderColor: borderColor, borderWidth: 1.5, tension: 0.3,
            pointBackgroundColor: borderColor, pointBorderColor: isDarkMode() ? '#fff' : '#333'
        };
    });
    chartTitleEl.innerText = `${title} (Comparison)`;
    totalCountSpan.textContent = `Comparing ${Object.keys(rawData).length} tutors`;

  } else if (chartKey === 'hourly_activity_by_day' && chartType === 'bar') {
    const daysOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    labels = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);
    datasetsArray = daysOrder.map((day, index) => {
        const dayData = rawData[day] || {};
        const dataPoints = labels.map(hourLabel => dayData[hourLabel] || 0);
        const color = متنوعColors(daysOrder.length, false, index);
        const borderColor = متنوعColors(daysOrder.length, true, index);
        return { label: day, data: dataPoints, backgroundColor: color, borderColor: borderColor, borderWidth: 1 };
    });
    chartTitleEl.innerText = title;
    let totalActivity = 0;
    Object.values(rawData).forEach(dayData => Object.values(dayData).forEach(count => totalActivity += count));
    totalCountSpan.textContent = `(Total Activity Events: ${totalActivity})`;

  } else { // Standard mode or pie chart, or comparison for non-daily charts
    let displayData = rawData;
    // For comparison mode on charts like 'checkins_per_tutor', rawData itself is the {TutorA: count, TutorB: count}
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

    const singleBackgroundColor = isDarkMode() ? 'rgba(255, 159, 64, 0.7)' : 'rgba(0, 188, 212, 0.7)';
    const singleBorderColor = isDarkMode() ? 'rgba(255, 159, 64, 1)' : 'rgba(0, 188, 212, 1)';

    datasetsArray = [{
        label: title, data: data, fill: chartType === 'area',
        backgroundColor: chartType === 'pie' ? متنوعColors(data.length) : singleBackgroundColor,
        borderColor: chartType === 'pie' ? متنوعColors(data.length, true) : singleBorderColor,
        borderWidth: 1, tension: 0.4,
        pointBackgroundColor: singleBorderColor, pointBorderColor: isDarkMode() ? '#fff' : '#333'
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
            <table class="table table-sm table-bordered table-striped ${isDarkMode() ? 'table-dark' : ''}">
            <thead><tr><th>Label</th><th>Value</th></tr></thead>
            <tbody>
                ${Object.keys(displayData).map((l) => `<tr><td>${l}</td><td>${parseFloat(displayData[l]).toFixed(2)}</td></tr>`).join('')}
            </tbody>
            </table>`;
    }
  }

  tutorChart = new Chart(ctx, {
    type: chartType === 'area' ? 'line' : chartType,
    data: { labels: labels, datasets: datasetsArray },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: chartType === 'pie' ? {} : {
        x: { ticks: { color: isDarkMode() ? '#f2f2f2' : '#111' }, grid: { color: isDarkMode() ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' } },
        y: { beginAtZero: true, ticks: { color: isDarkMode() ? '#f2f2f2' : '#111' }, grid: { color: isDarkMode() ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' } }
      },
      plugins: {
        legend: { position: chartType === 'pie' ? 'right' : 'top', labels: { color: isDarkMode() ? '#f2f2f2' : '#111', boxWidth: 12, padding: 10 } },
        tooltip: { callbacks: { label: function(context) {
            let label = context.dataset.label || '';
            if (label) label += ': ';
            if (context.parsed.y !== null && context.parsed.y !== undefined) label += context.parsed.y.toFixed(2);
            else if (context.raw !== null && context.raw !== undefined) label += parseFloat(context.raw).toFixed(2);
            return label;
        }}}
      }
    }
  });
}

function renderSplitChart(chartType, rawData, title, isComparisonMode = false, forecastData = null) {
  // For split layout, render the main chart on the left and a comparison chart on the right
  const primaryCtx = document.getElementById('primaryChart')?.getContext('2d');
  const comparisonCtx = document.getElementById('comparisonChart')?.getContext('2d');
  
  if (!primaryCtx || !comparisonCtx) return;
  
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
  
  currentChartInstances.comparisonChart = createChartInstance(comparisonCtx, 'pie', comparisonData, comparisonTitle, false);
}

function renderGridChart(chartType, rawData, title, isComparisonMode = false, forecastData = null) {
  // For grid layout, render 4 different charts showing different metrics
  const gridCtx1 = document.getElementById('gridChart1')?.getContext('2d');
  const gridCtx2 = document.getElementById('gridChart2')?.getContext('2d');
  const gridCtx3 = document.getElementById('gridChart3')?.getContext('2d');
  const gridCtx4 = document.getElementById('gridChart4')?.getContext('2d');
    
  if (!gridCtx1 || !gridCtx2 || !gridCtx3 || !gridCtx4) return;
  
  // Clear existing charts
  ['gridChart1', 'gridChart2', 'gridChart3', 'gridChart4'].forEach(chartId => {
    if (currentChartInstances[chartId]) currentChartInstances[chartId].destroy();
  });
  
  // Fetch data for different chart types
  fetchGridChartData().then(gridData => {
    // Chart 1: Check-ins per Tutor (Bar)
    if (gridData.checkins_per_tutor) {
      currentChartInstances.gridChart1 = createChartInstance(
        gridCtx1, 'bar', gridData.checkins_per_tutor, 'Check-ins per Tutor', false
      );
    }
    
    // Chart 2: Hours per Tutor (Pie)
    if (gridData.hours_per_tutor) {
      currentChartInstances.gridChart2 = createChartInstance(
        gridCtx2, 'pie', gridData.hours_per_tutor, 'Hours per Tutor', false
      );
    }
    
    // Chart 3: Daily Check-ins (Line)
    if (gridData.daily_checkins) {
      currentChartInstances.gridChart3 = createChartInstance(
        gridCtx3, 'line', gridData.daily_checkins, 'Daily Check-ins', false
      );
    }
    
    // Chart 4: Hourly Distribution (Bar)
    if (gridData.hourly_checkins_dist) {
      currentChartInstances.gridChart4 = createChartInstance(
        gridCtx4, 'bar', gridData.hourly_checkins_dist, 'Hourly Distribution', false
      );
    }
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
    backgroundColor: chartType === 'pie' ? متنوعColors(values.length) : singleBackgroundColor,
    borderColor: chartType === 'pie' ? متنوعColors(values.length, true) : singleBorderColor,
    borderWidth: 1,
    tension: 0.4
  }];
  
  return new Chart(ctx, {
    type: chartType === 'area' ? 'line' : chartType,
    data: { labels: labels, datasets: datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: chartType === 'pie' ? {} : {
        x: { 
          ticks: { color: isDarkMode() ? '#f2f2f2' : '#111', font: { size: 10 } },
          grid: { color: isDarkMode() ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }
        },
        y: { 
          beginAtZero: true,
          ticks: { color: isDarkMode() ? '#f2f2f2' : '#111', font: { size: 10 } },
          grid: { color: isDarkMode() ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }
        }
      },
      plugins: {
        legend: { 
          position: chartType === 'pie' ? 'bottom' : 'top',
          labels: { color: isDarkMode() ? '#f2f2f2' : '#111', boxWidth: 8, padding: 5, font: { size: 10 } }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || '';
              if (label) label += ': ';
              if (context.parsed.y !== null && context.parsed.y !== undefined) label += context.parsed.y.toFixed(2);
              else if (context.raw !== null && context.raw !== undefined) label += parseFloat(context.raw).toFixed(2);
              return label;
            }
          }
        }
      }
    }
  });
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
  
  try {
    const response = await fetch('/chart-data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(Object.fromEntries(params))
    });
    
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Error fetching grid chart data:', error);
    return {};
  }
}

function متنوعColors(num, border = false, index = -1) { /* ... same as before ... */
    const baseColors = [
        'rgba(255, 99, 132, DYNAMIC_ALPHA)', 'rgba(54, 162, 235, DYNAMIC_ALPHA)',
        'rgba(255, 206, 86, DYNAMIC_ALPHA)', 'rgba(75, 192, 192, DYNAMIC_ALPHA)',
        'rgba(153, 102, 255, DYNAMIC_ALPHA)', 'rgba(255, 159, 64, DYNAMIC_ALPHA)',
        'rgba(201, 203, 207, DYNAMIC_ALPHA)', 'rgba(50, 205, 50, DYNAMIC_ALPHA)',
        'rgba(255, 0, 255, DYNAMIC_ALPHA)', 'rgba(0, 255, 255, DYNAMIC_ALPHA)',
        'rgba(128, 0, 0, DYNAMIC_ALPHA)', 'rgba(0, 128, 0, DYNAMIC_ALPHA)', 
        'rgba(0, 0, 128, DYNAMIC_ALPHA)', 'rgba(128, 128, 0, DYNAMIC_ALPHA)',
        'rgba(128, 0, 128, DYNAMIC_ALPHA)'
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
  payload.chartKey = chartKey; 
  
  // Include advanced filters from sessionStorage
  const advancedFilters = JSON.parse(sessionStorage.getItem('advancedFilters') || '{}');
  Object.assign(payload, advancedFilters);
  
  console.log('Sending payload to backend:', payload); // Debug log
  
  document.getElementById('tutorChart').parentElement.innerHTML = '<div class="text-center p-5"><div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Loading chart data...</p></div>'; // Replace canvas with spinner

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
      const dataset = data[chartKey];
      const isComparison = data.is_comparison_mode || false;
      const forecast = data.forecast_daily_checkins || null;

      if (dataset === undefined || dataset === null) {
          console.error("Dataset key not found or is null:", chartKey, data);
          throw new Error(`No data for chart key "${chartKey}".`);
      }
      renderChart(chartType, dataset, chartTitles[chartKey] || "Chart", isComparison, forecast);
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


function toggleTheme() { /* ... same as before ... */
  const html = document.documentElement;
  html.classList.toggle('dark-mode');
  document.body.classList.toggle('dark-mode'); 
  const isDark = html.classList.contains('dark-mode');
  document.getElementById('themeToggleBtn').innerHTML = isDark ? '<i class="fas fa-sun"></i> Light Mode' : '<i class="fas fa-moon"></i> Dark Mode';
  localStorage.setItem('darkMode', isDark ? 'enabled' : 'disabled');
  const form = document.getElementById('filterForm');
  if (form) form.dispatchEvent(new Event('submit', {bubbles: true}));
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

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('filterForm');
  const datasetSelect = document.getElementById('dataset');
  const chartTypeSelect = document.getElementById('chartTypeSelect');

  if (localStorage.getItem('darkMode') === 'enabled') {
    document.documentElement.classList.add('dark-mode');
    document.body.classList.add('dark-mode');
    document.getElementById('themeToggleBtn').innerHTML = '<i class="fas fa-sun"></i> Light Mode';
  } else {
    document.getElementById('themeToggleBtn').innerHTML = '<i class="fas fa-moon"></i> Dark Mode';
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
      form.dispatchEvent(new Event('submit', { bubbles: true }));
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
    updateFilterChips();
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
  updateFilterChips();

  if (shouldSubmit) form.dispatchEvent(new Event('submit', { bubbles: true }));
  else form.dispatchEvent(new Event('submit', { bubbles: true })); // Initial load
});