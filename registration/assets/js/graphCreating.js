document.addEventListener("DOMContentLoaded", function () {
  const dropdownIds = ["project_name", "building_name"];
  const textInputIds = ["year", "month"];

  // Dropdowns
  dropdownIds.forEach((id) => {
    let selectElement = document.getElementById(id);
    let seen = {};

    if (selectElement) {
      selectElement.style.color = "rgb(173, 173, 173)";
      selectElement.style.cssText = null; // Remove any inline styles

      selectElement.addEventListener("change", function () {
        this.style.color = this.value ? "black" : "rgb(173, 173, 173)";
      });

      // Remove duplicate options
      Array.from(selectElement.options).forEach((option) => {
        if (seen[option.value]) {
          selectElement.removeChild(option);
        } else {
          seen[option.value] = true;
        }
      });

      // Trigger change event on load
      selectElement.dispatchEvent(new Event("change"));
    }
  });

  // Text inputs
  textInputIds.forEach((id) => {
    let inputElement = document.getElementById(id);

    if (inputElement) {
      inputElement.style.color = "rgb(173, 173, 173)";

      inputElement.addEventListener("input", function () {
        this.style.color = this.value ? "black" : "rgb(173, 173, 173)";
      });

      // Trigger input event on load
      inputElement.dispatchEvent(new Event("input"));
    }
  });

  ["project_name", "building_name"].forEach((id) => {
    var element = document.getElementById(id);
    element.style.cssText = null; // This will remove the 'style' attribute
  });

  fetchUserData();

  try {
    const submitButton = document.getElementById("applyFiltersButton");
    if (submitButton) {
      submitButton.addEventListener("click", handleSubmit);
    } else {
      console.log("Submit button not found");
    }
  } catch (error) {
    console.error("Error in main:", error);
  }
});

let userDataPromise = null;

async function fetchUserData() {
  if (!userDataPromise) {
    userDataPromise = new Promise(async (resolve, reject) => {
      try {
        const response = await fetch("/api/getUserData");
        if (!response.ok) {
          throw new Error("Fetch failed with status " + response.status);
        }
        const data = await response.json();
        populateDropdowns(data.transData);
        resolve(data);
      } catch (error) {
        reject(error);
      }
    });
  }
  return userDataPromise;
}

function populateDropdowns(transData) {
  const projectSelect = document.getElementById("project_name");
  const buildingSelect = document.getElementById("building_name");

  const currentSelections = {
    project_name: projectSelect.value,
    building_name: buildingSelect.value,
  };

  const projectNames = new Set(["Project Name"]);
  const buildingNames = new Set(["Building Name"]);

  transData.forEach((item) => {
    projectNames.add(item.project_name);
    buildingNames.add(item.building_name);
  });

  updateDropdown(projectSelect, projectNames);
  updateDropdown(buildingSelect, buildingNames);

  projectSelect.value = currentSelections.project_name;
  buildingSelect.value = currentSelections.building_name;
}

function updateDropdown(selectElement, optionsSet) {
  // Clear existing options
  selectElement.innerHTML = "";

  // Add default option
  const defaultOption = document.createElement("option");
  defaultOption.value = "select";
  defaultOption.textContent =
    selectElement.id === "project_name" ? "Project Name" : "Building Name";
  defaultOption.selected = true; // Set default option as selected
  selectElement.appendChild(defaultOption);

  // Add new options from optionsSet, excluding the default options
  optionsSet.forEach((optionValue) => {
    if (optionValue !== "Project Name" && optionValue !== "Building Name") {
      const optionElement = document.createElement("option");
      optionElement.value = optionValue;
      optionElement.textContent = optionValue;
      selectElement.appendChild(optionElement);
    }
  });
}

async function handleSubmit(event) {
  event.preventDefault();
  try {
    const formData = new FormData(document.getElementById("filterForm"));
    let filterData = Object.fromEntries(formData);
    userDataPromise = null; // Reset userDataPromise
    dataProcessing(filterData);
  } catch (error) {
    console.error("Error submitting form:", error);
  }
}

let myChart = null; // Single instance of the chart

async function dataProcessing(filterData) {
  try {
    const userData = await fetchUserData();
    let transData = [...userData.transData];

    // Initialize sets to collect unique years and months in the dataset.
    let uniqueYears = new Set();
    let uniqueMonths = new Set();

    // Populate the uniqueYears and uniqueMonths sets.
    for (let item of transData) {
      if (item.year) {
        uniqueYears.add(item.year.toString()); // Convert to string to ensure consistency
      }
      if (filterData.year) {
        if (item.year == filterData.year && item.month) {
          uniqueMonths.add(item.month.toString()); // Convert to string to ensure consistency
        }
      }
    }

    if (filterData.year && !uniqueYears.has(filterData.year)) {
      document.getElementById("message").innerText =
        "No data available for the selected year.";
      if (myChart) {
        myChart.destroy();
        myChart = null;
      }
      return;
    }

    // If a month is selected, check if it exists within the selected year in the dataset.
    if (filterData.month && !uniqueMonths.has(filterData.month)) {
      document.getElementById("message").innerText =
        "No data available for the selected month.";
      if (myChart) {
        myChart.destroy();
        myChart = null;
      }
      return;
    }

    // Filtering logic
    let filteredData = transData.filter(
      (item) =>
        (!filterData.project_name ||
          item.project_name == filterData.project_name) &&
        (!filterData.building_name ||
          item.building_name == filterData.building_name) &&
        (!filterData.year || item.year == filterData.year) &&
        (!filterData.month || item.month == filterData.month)
    );

    if (filteredData.length === 0) {
      document.getElementById("message").innerText =
        "No data available for the selected month.";
      if (myChart) {
        myChart.destroy();
        myChart = null;
      }
    }
    document.getElementById("message").innerText = "";

    let labels = [];
    let dataCounts = {};

    if (!filterData.year) {
      // Handling years if none is selected
      const years = filteredData.map((item) => item.year);
      const minYear = Math.min(...years);
      const maxYear = Math.max(...years);
      labels = Array.from(
        { length: maxYear - minYear + 5 }, // Adjust length to add 2 years on each side
        (_, i) => i + minYear - 2 // Start from 2 years before minYear
      );
      dataCounts = labels.reduce((acc, year) => {
        acc[year] = 0;
        return acc;
      }, {});
      filteredData.forEach((item) => {
        if (dataCounts.hasOwnProperty(item.year)) {
          dataCounts[item.year] += 1;
        }
      });
    } else if (filterData.year && !filterData.month) {
      // Handle months
      labels = Array.from({ length: 12 }, (_, i) => i + 1);
      dataCounts = labels.reduce((acc, month) => {
        acc[month] = 0;
        return acc;
      }, {});
      filteredData.forEach((item) => {
        if (dataCounts.hasOwnProperty(item.month)) {
          dataCounts[item.month] += 1;
        }
      });
    } else {
      // Handle dates
      const daysInMonth = (year, month) => new Date(year, month, 0).getDate();
      let year = parseInt(filterData.year, 10);
      let month = parseInt(filterData.month, 10);
      labels = Array.from(
        { length: daysInMonth(year, month) },
        (_, i) => i + 1
      );
      dataCounts = labels.reduce((acc, date) => {
        acc[date] = 0;
        return acc;
      }, {});
      filteredData.forEach((item) => {
        if (dataCounts.hasOwnProperty(item.date)) {
          dataCounts[item.date] += 1;
        }
      });
    }

    // Create the chart
    createChart(labels, dataCounts);
  } catch (error) {
    console.error("Error in dataProcessing:", error);
  }
}

// Count records based on given field
function countRecords(labels, filteredData, field) {
  let dataCounts = {};
  labels.forEach((label) => {
    let count = filteredData.filter((item) => item[field] === label).length;
    dataCounts[label] = count;
  });
  return dataCounts;
}

// Create chart using Chart.js
function createChart(labels, dataCounts) {
  const ctx = document.getElementById("myChart").getContext("2d");

  // Destroy previous chart instance if exists
  if (myChart) {
    myChart.destroy();
  }

  // Find the maximum intersection value in your dataCounts
  const maxIntersection = Math.max(...Object.values(dataCounts));

  // Calculate the maximum Y-axis value and the step size (gap)
  let maxYValue, stepSize;
  if (maxIntersection <= 10) {
    maxYValue = 10;
    stepSize = 1;
  } else {
    maxYValue = Math.ceil(maxIntersection / 10) * 10;
    stepSize = maxYValue / 10;
  }

  myChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Number of Records",
          data: Object.values(dataCounts),
          backgroundColor: "rgba(75, 192, 192, 0.5)",
          borderColor: "rgba(75, 192, 192, 1)",
          borderWidth: 2,
          tension: 0.3,
          fill: false,
        },
      ],
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
          max: maxYValue,
          stepSize: stepSize,
        },
      },
    },
  });
}
