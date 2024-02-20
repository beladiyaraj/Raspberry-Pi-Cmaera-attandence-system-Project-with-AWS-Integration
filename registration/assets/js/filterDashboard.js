document.addEventListener("DOMContentLoaded", function () {
["Device_ID"].forEach((id) => {
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