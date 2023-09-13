document.addEventListener("DOMContentLoaded", function () {
  // Initially hide the transactionsSection when the DOM is fully loaded
  const transactionsSection = document.getElementById("transactionsSection");
  transactionsSection.style.display = "none";

  document
    .getElementById("filterForm")
    .addEventListener("submit", function (e) {
      e.preventDefault();

      let filterData = {};
      const formData = new FormData(e.target);
      formData.forEach((value, key) => {
        filterData[key] = value.trim().toLowerCase(); // Trim and convert all filter data to lowercase
      });

      let tableRows = document.querySelectorAll("#transactionsTable tbody tr");
      let matchingRowCount = 0; // Initialize the counter

      tableRows.forEach(function (row) {
        let showRow = true;
        let cells = row.querySelectorAll("td");

        Object.keys(filterData).forEach(function (key, index) {
          if (filterData[key]) {
            // Check if filter text is a substring of the cell's text content
            if (
              !cells[index].innerText
                .trim()
                .toLowerCase()
                .includes(filterData[key])
            ) {
              // Trim and convert cell content to lowercase before comparison
              showRow = false;
            }
          }
        });

        if (showRow) {
          row.style.display = "";
          matchingRowCount++; // Increase the counter if this row matches
        } else {
          row.style.display = "none";
        }
      });

      // If no rows matched the filter criteria, hide the entire transactions section
      if (matchingRowCount === 0) {
            // Add the fade-out slide-out animation
            transactionsSection.classList.add('hide-transaction');
            transactionsSection.classList.remove('show-transaction');
            
            // Wait for the animation to complete and then set display to 'none'
            setTimeout(() => {
                transactionsSection.style.display = "none";
                transactionsSection.classList.remove('hide-transaction');
            }, 850); // corresponds to the animation duration
        } else {
            // Ensure the section has 'display: block' before the animation
            transactionsSection.style.display = "block";
            // Give the browser a moment to catch up by using a timeout
            setTimeout(() => {
                transactionsSection.classList.add('show-transaction');
                transactionsSection.classList.remove('hide-transaction');
            }, 10);
        }
    });
});
