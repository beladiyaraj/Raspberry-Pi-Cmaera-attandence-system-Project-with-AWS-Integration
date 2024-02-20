document.addEventListener("DOMContentLoaded", function () {
  const transactionsSection = document.getElementById("transactionsSection");
  transactionsSection.style.display = "none";

  const form = document.getElementById("filterForm");
  const tableRows = document.querySelectorAll("#transactionsTable tbody tr");
  let matchingRowCount = 0;
  form.addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent the default form submission

    // Collect filter criteria from form
    const projectName = document
      .getElementById("project_name")
      .value.toLowerCase();
    const buildingName = document
      .getElementById("building_name")
      .value.toLowerCase();
    const gateNo = document.getElementById("gate_no").value.toLowerCase();
    const gateName = document.getElementById("gate_name").value.toLowerCase();
    const batchID = document.getElementById("Batch_ID").value.toLowerCase();
    const year = document.getElementById("Year").value.toLowerCase();
    const month = document.getElementById("Month").value.toLowerCase();
    const date = document.getElementById("Date").value.toLowerCase();
    const day = document.getElementById("Day").value.toLowerCase();
    const hours = document.getElementById("Hours").value.toLowerCase();
    const minutes = document.getElementById("Minutes").value.toLowerCase();
    const seconds = document.getElementById("Seconds").value.toLowerCase();
    const visitorDetails = document
      .getElementById("Visitor_Details")
      .value.toLowerCase();
    const vehicleNo = document.getElementById("Vehicle_No").value.toLowerCase();
    // Apply filters to table rows
    tableRows.forEach((row) => {
      const cells = row.cells;
      if (
        (projectName === "" ||
          cells[0].innerText.toLowerCase() === projectName) &&
        (buildingName === "" ||
          cells[1].innerText.toLowerCase() === buildingName) &&
        (gateNo === "" || cells[2].innerText.toLowerCase() === gateNo) &&
        (gateName === "" || cells[3].innerText.toLowerCase() === gateName) &&
        (batchID === "" || cells[5].innerText.toLowerCase() === batchID) &&
        (year === "" || cells[6].innerText.toLowerCase() === year) &&
        (month === "" || cells[7].innerText.toLowerCase() === month) &&
        (date === "" || cells[8].innerText.toLowerCase() === date) &&
        (day === "" || cells[9].innerText.toLowerCase() === day) &&
        (hours === "" || cells[10].innerText.toLowerCase() === hours) &&
        (minutes === "" || cells[11].innerText.toLowerCase() === minutes) &&
        (seconds === "" || cells[12].innerText.toLowerCase() === seconds) &&
        (visitorDetails === "" ||
          cells[13].innerText.toLowerCase().includes(visitorDetails)) &&
        (vehicleNo === "" || cells[14].innerText.toLowerCase() === vehicleNo)
      ) {
        console.log(cells);
        row.style.display = "";
        matchingRowCount++;
      } else {
        row.style.display = "none";
      }
    });
    if (matchingRowCount == 0) {
      transactionsSection.classList.add("hide-transaction");
      transactionsSection.classList.remove("show-transaction");
      setTimeout(() => {
        transactionsSection.style.display = "none";
        transactionsSection.classList.remove("hide-transaction");
      }, 850);
    } else {
      transactionsSection.style.display = "block";
      setTimeout(() => {
        transactionsSection.classList.add("show-transaction");
        transactionsSection.classList.remove("hide-transaction");
      }, 10);
    }
    matchingRowCount = 0;
  });
  [
    "project_name",
    "building_name",
    "gate_name",
    "gate_no",
  ].forEach((id) => {
    let seen = {};

    $(`select#${id}`).css("color", "rgb(173, 173, 173)");

    // Register a change event listener
    $(`select#${id}`).on("change", function () {
      if (this.value) {
        $(this).css("color", "black");
      } else {
        $(this).css("color", "rgb(173, 173, 173)");
      }
    });
    
    $(`select#${id} option`).each(function () {
      let val = $(this).val();
      if (seen[val]) {
        $(this).remove();
      } else {
        seen[val] = true;
      }
    });
  });

  document.getElementById("clearAll").addEventListener("click", function () {
    transactionsSection.classList.add("hide-transaction");
    transactionsSection.classList.remove("show-transaction");
    setTimeout(() => {
      transactionsSection.style.display = "none";
      transactionsSection.classList.remove("hide-transaction");
    }, 850);
    const form = document.getElementById("filterForm");
    for (const element of form.elements) {
      if (element.type !== "button" && element.type !== "submit") {
        element.value = "";
      }
    }
  });
});
