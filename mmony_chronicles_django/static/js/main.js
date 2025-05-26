// Main JavaScript file for Mobile Money Chronicles

// Custom theme colors
const themeColors = {
    grass: '#2E7D32', // Primary brand/dark accent - vibrant green
    lime: '#81C784',  // Buttons, highlights - medium green
    yellow: '#FFC107', // Attention areas, call-outs - amber yellow
    white: '#F5F5F5',  // Light text, UI contrast - off-white
    darkBg: '#263238', // Dark background - blue-gray, lighter than before
    darkCard: '#37474F', // Dark card background - lighter blue-gray
    darkAccent: '#455A64' // Dark accent for tables, etc. - medium blue-gray
};

// Custom Plotly theme
const plotlyTheme = {
    colorway: [
        themeColors.lime,       // Medium green
        themeColors.yellow,     // Amber yellow
        '#4CAF50',              // Green
        '#66BB6A',              // Light green
        '#26A69A',              // Teal
        '#42A5F5',              // Blue
        '#7E57C2',              // Purple
        themeColors.grass       // Vibrant green
    ],
    paper_bgcolor: themeColors.darkCard,   // Dark card background for consistency
    plot_bgcolor: themeColors.darkCard,    // Dark card background for consistency
    font: {
        color: themeColors.white,          // Light text for dark background
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
    },
    title: {
        font: {
            color: themeColors.lime,       // Lime for titles to match headings
            weight: 700                    // Bold for titles
        }
    },
    xaxis: {
        title: {
            font: {
                color: themeColors.lime,   // Lime for axis titles
                weight: 500                // Medium for axis titles
            }
        },
        tickfont: {
            color: themeColors.white,      // Light text for dark background
            weight: 400                    // Regular for tick labels
        },
        gridcolor: 'rgba(245, 245, 245, 0.1)' // Light grid with low opacity
    },
    yaxis: {
        title: {
            font: {
                color: themeColors.lime,   // Lime for axis titles
                weight: 500                // Medium for axis titles
            }
        },
        tickfont: {
            color: themeColors.white,      // Light text for dark background
            weight: 400                    // Regular for tick labels
        },
        gridcolor: 'rgba(245, 245, 245, 0.1)' // Light grid with low opacity
    }
};

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Enable Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Add active class to current nav item
    var currentLocation = window.location.pathname;
    var navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    navLinks.forEach(function(link) {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
        }
    });

    // File input change handler for upload form
    var fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            var fileName = this.files[0].name;
            var fileLabel = document.querySelector('.custom-file-label');
            if (fileLabel) {
                fileLabel.textContent = fileName;
            }
        });
    }

    // Scroll to top button functionality
    var scrollToTopBtn = document.getElementById("scrollToTop");

    // Show/hide the button based on scroll position
    window.addEventListener("scroll", function() {
        if (window.pageYOffset > 300) {
            scrollToTopBtn.classList.add("visible");
        } else {
            scrollToTopBtn.classList.remove("visible");
        }
    });

    // Scroll to top when button is clicked
    scrollToTopBtn.addEventListener("click", function() {
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    });

    // Apply custom Plotly theme if Plotly is loaded
    if (typeof Plotly !== 'undefined') {
        // Set default template
        Plotly.setPlotConfig({
            modeBarButtonsToRemove: ['sendDataToCloud', 'autoScale2d', 'resetScale2d'],
            displaylogo: false
        });

        // Apply theme to all charts
        const charts = document.querySelectorAll('[id$="-chart"]');
        charts.forEach(chart => {
            if (chart._fullData) {
                Plotly.relayout(chart.id, plotlyTheme);
            }
        });
    }
});
