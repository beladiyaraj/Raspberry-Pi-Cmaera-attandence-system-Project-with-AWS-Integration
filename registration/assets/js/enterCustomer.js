document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("verifyEmail")
    .addEventListener("click", async (event) => {
      event.preventDefault();
      const email = document.getElementById("email").value;
      const password = document.getElementById("adminPassword").value;

      try {
        const response = await fetch(
          `/checkadminemail?email=${encodeURIComponent(
            email
          )}&password=${encodeURIComponent(password)}`,
          {
            method: "GET",
            headers: {
              "Content-Type": "application/json",
            },
          }
        );

        const result = await response.json();
        const emailForm = document.getElementById("emailForm");
        const customerForm = document.getElementById("customerForm");

        if (result) {
          customerForm.classList.add("fade-in");
          setTimeout(() => {
            emailForm.style.display = "none";
            customerForm.style.display = "block";
          }, 500);
        } else {
          if (response.status === 400) {
            alert("Wrong Admin Email");
          } else if (response.status === 500) {
            alert("Wrong Password");
          }
        }
      } catch (error) {
        console.error("An error occurred:", error);
      }
    });

  async function handleClick(event) {
    event.preventDefault();
    const form = document.getElementById("customerForm");
    const formData = new FormData(form);

    let customerId,
      customerLogin,
      customerPassword,
      deviceId,
      customerName,
      customerType,
      customerAddress,
      contactPersonName,
      contactPersonEmailID,
      contactPersonPhone;

    if (!validateForm(form)) {
      alert("Please fill all required fields.");
      return;
    }

    for (let [key, value] of formData) {
      if (key === "customer_id") customerId = value;
      if (key === "customer_login") customerLogin = value;
      if (key === "customer_password") customerPassword = value;
      if (key === "device_id") deviceId = value;
      if (key === "customer_name") customerName = value;
      if (key === "customer_type") customerType = value;
      if (key === "customer_address") customerAddress = value;
      if (key === "contact_person_name") contactPersonName = value;
      if (key === "contact_person_emailID") contactPersonEmailID = value;
      if (key === "contact_person_phone") contactPersonPhone = value;
    }

    if (!validateDeviceId(deviceId)) {
      alert(
        'Invalid device_id. It should be in the format ["something", "something", ...]'
      );
      return;
    }

    try {
      const customerResponse = await fetch("/addCustomer", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          customerId,
          customerLogin,
          customerPassword,
          deviceId,
          customerName,
          customerType,
          customerAddress,
          contactPersonName,
          contactPersonEmailID,
          contactPersonPhone,
        }),
      });

      const customerResult = await customerResponse.json();

      if (customerResult.status === "success") {
        alert("Customer added successfully!");
      } else if (customerResult.status === "customeralreadyexist") {
        alert("Customer With This ID Already Exists");
      } else {
        alert("Failed to add customer.");
      }
    } catch (error) {
      console.error("Failed to add customer:", error);
    }
  }

  const submitBtn = document.getElementById("enterCustomerButton");
  submitBtn.addEventListener("click", handleClick);

  function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll("input[required]");
    inputs.forEach((input) => {
      if (!input.validity.valid) {
        isValid = false;
        input.classList.add("error");
      } else {
        input.classList.remove("error");
      }
    });
    return isValid;
  }

  function validateDeviceId(deviceId) {
    const regex = /^\s*\[("[^"]*",\s*)*"[^"]*"\]\s*$/;
    if (!regex.test(deviceId)) {
      return false;
    }
    try {
      const parsedArray = JSON.parse(deviceId);
      if (!Array.isArray(parsedArray)) {
        return false;
      }
      return true;
    } catch (e) {
      return false;
    }
  }
});