document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("verifyEmail")
    .addEventListener("click", async (event) => {
      event.preventDefault();
      const email = document.getElementById("email").value;
      try {
        const response = await fetch(
          `/checkemail?email=${encodeURIComponent(email)}`,
          {
            method: "GET", // This is a GET request, so no body is needed
            headers: {
              "Content-Type": "application/json",
            },
          }
        );

        // Function to gradually fade in an element
        function fadeIn(element, duration) {
          let start = null;
          const interval = 1000 / 60; // 60 frames per second

          function step(timestamp) {
            if (!start) start = timestamp;

            const elapsed = timestamp - start;

            if (elapsed < duration) {
              const opacity = (elapsed / duration).toFixed(2);
              element.style.opacity = opacity;
              requestAnimationFrame(step);
            } else {
              element.style.opacity = "1";
            }
          }

          requestAnimationFrame(step);
        }

        // After a successful email verification
        if (response.ok) {
          const result = await response.json();

          const passwordForm = document.getElementById("passwordForm");
          passwordForm.style.display = "block";
          const verifyEmailButton = document.getElementById("verifyEmail");
          verifyEmailButton.style.display = "none";
          fadeIn(passwordForm, 300); // 300 milliseconds duration (adjust as needed)
          fadeIn(verifyEmailButton, 300);
        } else {
          const errorMessage = await response.text();
          console.error(errorMessage);
        }
      } catch (error) {
        console.error("An error occurred:", error);
      }
    });

  document
    .getElementById("resetPasswordButton")
    .addEventListener("click", async (event) => {
      event.preventDefault();
      const email = document.getElementById("email").value;
      const currentPassword = document.getElementById("currentPassword").value;
      const newPassword = document.getElementById("newPassword").value;
      const confirmPassword = document.getElementById("confirmPassword").value;
      try {
        if (newPassword == confirmPassword) {
          const response = await fetch("/resetpassword", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ email, currentPassword, newPassword }),
          });

          if (response.ok) {
            const result = await response.json();
            alert("Password Changed Successfully");
            window.location.href = "/";
          } else if (response.status === 400) {
            const errorMessage = await response.text();
            alert("Invalid current password: ");
          } else {
            const errorMessage = await response.text();
            alert("An error occurred: ");
          }
        } else alert("Confirm Password Is Different");
      } catch (error) {
        console.error("An error occurred:", error);
      }
    });
});