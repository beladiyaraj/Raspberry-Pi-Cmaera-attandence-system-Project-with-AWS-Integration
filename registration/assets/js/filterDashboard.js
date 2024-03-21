document.addEventListener("DOMContentLoaded", function () {
["device_id"].forEach((id) => {
  let seen = {};
  $(`select#${id} option`).each(function () {
    let val = $(this).val();
    if (seen[val]) {
      $(this).remove();
    } else {
      seen[val] = true;
    }
  });
});
});