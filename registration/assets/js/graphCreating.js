document.addEventListener("DOMContentLoaded", function () {
  fetchUserData();
  try {
    const submitButton = document.getElementById("applyFiltersButton"); // Replace 'submitButton' with the actual ID of your submit button
    submitButton.addEventListener("click", handleSubmit);
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
        resolve(data);
      } catch (error) {
        reject(error);
      }
    });
  }
  return userDataPromise;
}

async function handleSubmit(event) {
  event.preventDefault(); // Prevent the default form submission behavior

  try {
    // Get form data using FormData
    const formData = new FormData(document.getElementById("filterForm")); // Replace 'yourFormId' with the actual ID of your form element
    let filterData = Object.fromEntries(formData);
    dataProcessing(filterData);
  } catch (error) {
    console.error("Error submitting form:", error);
  }
}

async function dataProcessing(filterData) {
  try {
    const userData = await fetchUserData(); // Fetch user data once
    // Create an array to store the names of empty fields
    const emptyFields = [];

    // Iterate through the properties of filterData
    for (const key in filterData) {
      if (filterData.hasOwnProperty(key)) {
        const value = filterData[key];
        if (!value) {
          emptyFields.push(key);
        }
      }
    }

    if (Object.values(filterData).every((value) => !value)) {
      alert("Please enter any values for filtering");
    } else {
      if (emptyFields.length > 0) {
        if (
          emptyFields.includes("location_id") ||
          emptyFields.includes("device_id")
        ) {
          const defaultLocationId = userData.locationIDsParsed[0];
          const defaultDeviceId = userData.deviceIDsParsed[0];
          // Check if "location_id" is not empty and validate it
          if (!emptyFields.includes("location_id")) {
            const locationId = filterData.location_id;
            if (!userData.locationIDsParsed.includes(locationId)) {
              alert("Invalid location_id. Please select a valid location.");
              return; // Exit the function to prevent further processing
            }
          }

          // Check if "device_id" is not empty and validate it
          if (!emptyFields.includes("device_id")) {
            const deviceId = filterData.device_id;
            if (!userData.deviceIDsParsed.includes(deviceId)) {
              alert("Invalid device_id. Please select a valid device.");
              return; // Exit the function to prevent further processing
            }
          }
          filterData.location_id = defaultLocationId;
          filterData.device_id = defaultDeviceId;
        } else {
          if (!emptyFields.includes("location_id")) {
            const locationId = filterData.location_id;
            if (!userData.locationIDsParsed.includes(locationId)) {
              alert("Invalid location_id. Please select a valid location.");
              return; // Exit the function to prevent further processing
            }
          }

          // Check if "device_id" is not empty and validate it
          if (!emptyFields.includes("device_id")) {
            const deviceId = filterData.device_id;
            if (!userData.deviceIDsParsed.includes(deviceId)) {
              alert("Invalid device_id. Please select a valid device.");
              return; // Exit the function to prevent further processing
            }
          }
        }
      } else {
        if (!emptyFields.includes("location_id")) {
          const locationId = filterData.location_id;
          if (!userData.locationIDsParsed.includes(locationId)) {
            alert("Invalid location_id. Please select a valid location.");
            return; // Exit the function to prevent further processing
          }
        }

        // Check if "device_id" is not empty and validate it
        if (!emptyFields.includes("device_id")) {
          const deviceId = filterData.device_id;
          if (!userData.deviceIDsParsed.includes(deviceId)) {
            alert("Invalid device_id. Please select a valid device.");
            return; // Exit the function to prevent further processing
          }
        }
      }
    }
    countRecordsByYear(userData, filterData);
  } catch (error) {
    console.error("Error in dataProcessing:", error);
  }
}

var flag = "null";
async function countRecordsByYear(userData, filterData) {
  if (!filterData.year && !filterData.month) {
    flag = "year";
    const yearCounts = {};

    // Iterate through the transData array
    for (const record of userData.transData) {
      // Check if the record has both device_id and year
      if (record.Device_ID == filterData.device_id) {
        const year = record.year.toString(); // Convert year to string for consistency

        // Initialize or increment the count for the year
        if (!yearCounts[year]) {
          yearCounts[year] = 1;
        } else {
          yearCounts[year]++;
        }
      }
    }
    updateChart(yearCounts);
  } else if (filterData.year && !filterData.month) {
    flag = "month";
    const monthCounts = {};

    // Iterate through the trAansData array
    for (const record of userData.transData) {
      // Check if the record has both device_id and year matching filterData
      if (
        record.Device_ID == filterData.device_id &&
        record.year == parseInt(filterData.year)
      ) {
        const month = record.month.toString(); // Convert month to string for consistency

        // Initialize or increment the count for the month
        if (!monthCounts[month]) {
          monthCounts[month] = 1;
        } else {
          monthCounts[month]++;
        }
      }
    }
    updateChart(monthCounts);
  } else if (filterData.year && filterData.month) {
    flag = "date";
    const dateCounts = {};
    // Iterate through the transData array
    for (const record of userData.transData) {
      // Check if the record matches all filterData criteria and if record.date is a valid number
      if (
        record.Device_ID == filterData.device_id &&
        record.year == parseInt(filterData.year) &&
        record.month == parseInt(filterData.month) &&
        isNumber(record.date)
      ) {
        // Convert the date to a string for consistency
        const date = record.date.toString();

        // Initialize or increment the count for the date
        if (!dateCounts[date]) {
          dateCounts[date] = 1;
        } else {
          dateCounts[date]++;
        }
      }
    }
    updateChart(dateCounts, filterData);
  }
  return null; // Return the result (it can be an object or null)
}

function updateChart(counts, filterData) {
  const keys = Object.keys(counts); // Get the keys
  var data = Object.values(counts);
  var labels = [];
  var xAxisLable;
  if (flag == "year") {
    const maxYear = Math.max(...keys);
    const minYear = Math.min(...keys);
    xAxisLable = "Years";
    // Add the previous and next years to the array
    labels = Array.from(
      { length: maxYear - minYear + 3 },
      (_, index) => minYear - 1 + index
    );
    data = labels.map((year) => (counts[year] ? counts[year] : 0));
  } else if (flag == "month") {
    xAxisLable = "Months";
    const monthLabels = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];

    // Create an array with counts for each month
    const monthCounts = Array.from({ length: 12 }, (_, index) =>
      counts[index + 1] ? counts[index + 1] : 0
    );

    // Assign the month labels and counts to labels and data
    labels = monthLabels;
    data = monthCounts;
  } else if (flag == "date") {
    xAxisLable = "Date";
    const selectedMonth = parseInt(filterData.month);
    // Determine the number of days in the selected month
    const daysInMonth = new Date(
      parseInt(filterData.year),
      selectedMonth,
      0
    ).getDate();

    // Create labels ranging from 1 to the number of days in the month
    labels = Array.from({ length: daysInMonth }, (_, index) => index + 1);
    data = labels.map((year) => (counts[year] ? counts[year] : 0));
  }
  createChart(labels, data, xAxisLable);
}

let myChart = null;
function createChart(labels, data, xAxisLable) {
  // Destroy the existing chart if it exists
  if (myChart) {
    myChart.destroy();
  }

  const ctx = document.getElementById("myChart").getContext("2d");

  const chartData = {
    labels: labels,
    datasets: [
      {
        label: "Fliter",
        data: data,
        fill: false,
        borderColor: "rgb(75, 192, 192)",
        tension: 0.3,
      },
    ],
  };

  const chartOptions = {
    scales: {
      y: {
        beginAtZero: true,
        max: 10, // Set the Y-axis max value to 10
        ticks: {
          font: {
            size: 16, // Set the font size to 20px for the Y-axis ticks
            weight: "bold", // Make the font bold
          },
        },
        title: {
          display: true,
          text: "Visitors", // Set the Y-axis label to 'Visitors'
          font: {
            size: 16, // Set the font size for the label
            weight: "bold", // Make the label bold
          },
        },
      },
      x: {
        ticks: {
          font: {
            size: 16, // Set the font size to 20px for the X-axis ticks
            weight: "bold", // Make the font bold
          },
        },
        title: {
          display: true,
          text: xAxisLable, // Set the X-axis label to 'Anything'
          font: {
            size: 16, // Set the font size for the label
            weight: "bold", // Make the label bold
          },
        },
      },
    },
    plugins: {
      legend: {
        labels: {
          font: {
            size: 16, // Set the font size to 20px for the legend labels
            weight: "bold", // Make the font bold
          },
        },
      },
    },
  };

  // Create the new chart
  myChart = new Chart(ctx, {
    type: "line",
    data: chartData,
    options: chartOptions,
  });

  ctx.canvas.style.border = "1px solid #324960";

  const chartSection = document.getElementById("chartSection");
  if (chartSection) {
    chartSection.scrollIntoView({ behavior: "smooth" }); // Smooth scrolling
  }
}

//Helper Function
function isNumber(value) {
  return !isNaN(parseFloat(value)) && isFinite(value);
}

