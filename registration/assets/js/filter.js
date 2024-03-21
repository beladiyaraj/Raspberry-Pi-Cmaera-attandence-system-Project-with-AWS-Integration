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
    const batch_id = document.getElementById("batch_id").value.toLowerCase();
    const date = document.getElementById("date").value.toLowerCase();
    const day = document.getElementById("day").value.toLowerCase();
    const entry_time = document
      .getElementById("entry_time")
      .value.toLowerCase();
    const exit_time = document.getElementById("exit_time").value.toLowerCase();
    const visitor_details = document
      .getElementById("visitor_details")
      .value.toLowerCase();
    // const vehicleNo = document.getElementById("Vehicle_No").value.toLowerCase();
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
        (batch_id === "" || cells[5].innerText.toLowerCase() === batch_id) &&
        (date === "" || cells[8].innerText.toLowerCase() === date) &&
        (day === "" || cells[9].innerText.toLowerCase() === day) &&
        (entry_time === "" ||
          cells[10].innerText.toLowerCase() === entry_time) &&
        (exit_time === "" || cells[10].innerText.toLowerCase() === exit_time) &&
        (visitor_details === "" ||
          cells[13].innerText.toLowerCase().includes(visitor_details))
        // (vehicleNo === "" || cells[14].innerText.toLowerCase() === vehicleNo)
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
  ["project_name", "building_name", "gate_name", "gate_no"].forEach((id) => {
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
