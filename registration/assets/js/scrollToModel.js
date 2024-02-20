$(document).ready(function () {
  // Listen for when any modal is shown
  console.log("Document content has been loaded.");
  $(".modal").on("shown.bs.modal", function () {
    // Find the table
    var table = $(".table-wrapper");

    // Ensure that the table element is found
    if (table.length === 0) {
      console.log("Table not found.");
      return;
    }

    // Calculate the table's center position relative to the viewport
    var tableTop = table.offset().top;
    var tableHeight = table.outerHeight();
    var windowHeight = $(window).height();
    var tableCenter = tableTop + tableHeight / 2;
    var viewportCenter = windowHeight / 2;

    console.log("Table top:", tableTop);
    console.log("Table height:", tableHeight);
    console.log("Window height:", windowHeight);
    console.log("Table center:", tableCenter);
    console.log("Viewport center:", viewportCenter);

    var desiredScrollPosition;
    desiredScrollPosition = tableCenter - tableTop;

    console.log("Desired scroll position:", desiredScrollPosition);

    // Scroll the viewport to the desired position
    $("html, body").animate(
      {
        scrollTop: desiredScrollPosition,
      },
      "slow"
    );
  });
  // Listen for when any modal is hidden
  $(".modal").on("hidden.bs.modal", function () {
    // Smooth scroll back to the top of the page
    $("html, body").animate(
      {
        scrollTop: 0,
      },
      "slow"
    );
  });
});
