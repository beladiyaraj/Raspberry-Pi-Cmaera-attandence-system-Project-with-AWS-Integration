const express = require("express");
const session = require("express-session");
const cookieParser = require("cookie-parser");
const path = require("path");
const db = require("./conn/connection");
const app = express();

app.use(cookieParser());
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(
  session({
    secret: "gatex",
    resave: false,
    saveUninitialized: true,
    cookie: {
      httpOnly: true,
      expires: false,
    },
  })
);

app.use((req, res, next) => {
  if (req.originalUrl === "/") {
    res.set(
      "Cache-Control",
      "no-store, no-cache, must-revalidate, private, max-age=0"
    );
  }
  next();
});

app.use(express.static(path.join(__dirname, "/assets")));
app.set("view engine", "hbs");

app.get("/", (req, res) => {
  if (req.session && req.session.user) {
    return res.redirect("/admin");
  }
  res.render("login");
});

app.post("/login", async (req, res) => {
  try {
    const user = await getUserFromDB(req.body.email);

    if (!user) {
      return res.send(alertRedirect("No user found with this email", "/"));
    }

    if (user.customer_password !== req.body.password) {
      return res.send(alertRedirect("Invalid Password", "/"));
    }

    req.session.user = user.customer_login;
    res.redirect("/admin");
  } catch (error) {
    console.error("Error:", error);
    res.status(500).send("Internal Server Error");
  }
});

app.get("/admin", ensureAuthenticated, async (req, res) => {
  try {
    if (!req.session.user) {
      return res.redirect("/");
    }

    const data = await getAdminData(req.session.user);
    if (!data.userdata) {
      return res.send(alertRedirect("No userData found with the email", "/"));
    }
    res.render("admin", data);
  } catch (error) {
    console.error("Error:", error);
    res.status(500).send("Internal Server Error");
  }
});

app.get("/logout", (req, res) => {
  req.session.destroy((err) => {
    if (err) {
      return res.redirect("/admin");
    }
    res.clearCookie("connect.sid");
    res.redirect("/");
  });
});

app.get("/dashboard", ensureAuthenticated, async (req, res) => {
  try {
    if (!req.session.user) {
      return res.redirect("/");
    }

    const user = req.session.user;
    const userDataResults = await getAdminData(user);

    if (!userDataResults.userdata) {
      return res.send(alertRedirect("No userData found with the email", "/"));
    }

    res.render("dashboard", userDataResults);
  } catch (error) {
    console.error("Error:", error);
    res.status(500).send("Internal Server Error");
  }
});

app.get("/forgotpassword", async (req, res) => {
  try {
    res.render("forgotpassword");
  } catch (error) {
    res.send("Page not found");
    console.error("Error:", error);
  }
});

app.get("/checkemail", async (req, res) => {
  const email = req.query.email; // Get the email from the query parameters
  try {
    const user = await getUserFromDB(email);
    if (!user) {
      return res.send(
        alertRedirect("No user found with this email", "/forgotpassword")
      );
    }
    res.json(true);
  } catch (error) {
    console.error("An error occurred:", error);
    res.status(500).json({ error: "Internal Server Error" });
  }
});

app.post("/resetpassword", async (req, res) => {
  try {
    const { email, currentPassword, newPassword } = req.body;
    // Verify the current password (you can customize this logic)
    const isPasswordValid = await verifyCurrentPassword(email, currentPassword);
    if (!isPasswordValid) {
      return res.status(400).json({ error: "Invalid current password" });
    }

    // Update the password in your database (you can customize this logic)
    const passwordChanged = await changePassword(email, newPassword);

    if (passwordChanged) {
      return res.json({ message: "Password changed successfully" });
    } else {
      return res.status(500).json({ error: "Failed to change password" });
    }
  } catch (error) {
    console.error("An error occurred:", error);
    res.status(500).json({ error: "Internal Server Error" });
  }
});

const server = app.listen(2000, "0.0.0.0", () => {
  console.log("listening to server on http://localhost:2000");
});

server.on("error", (error) => {
  console.error("Error occurred:", error);
});

function alertRedirect(message, url) {
  return `
    <script>
        alert('${message}');
        window.location.href = '${url}';
    </script>
  `;
}

async function getUserFromDB(email) {
  return new Promise((resolve, reject) => {
    const sql = "SELECT * FROM customer_master WHERE customer_login = ?";
    db.query(sql, [email], (err, results) => {
      if (err) return reject(err);
      resolve(results[0]);
    });
  });
}

async function getAdminData(useremail) {
  return new Promise((resolve, reject) => {
    try {
      const sql = "SELECT * FROM customer_master WHERE customer_login = ?";
      db.query(sql, [useremail], async (err, results) => {
        if (err) {
          console.error("Error fetching user data:", err);
          return reject(err);
        }
        const userData = results[0];

        // Get location data based on the customer_id
        const locationResults = await getLocationData(userData.customer_id);

        if (!locationResults) {
          console.error("Location data not found.");
          return reject("No location data found for this customer ID");
        }

        const deviceIdArray = userData.device_id
          ? JSON.parse(userData.device_id)
          : [];
        const transResults = await getTransData(deviceIdArray);

        const locationIdArray = locationResults.location_ID
          ? JSON.parse(locationResults.location_ID)
          : [];
        if (deviceIdArray.length === 0) {
          resolve({
            useremail,
            deviceIDsParsed: [],
            locationIDsParsed: [],
            transData: [],
            userdata: userData,
            location: locationResults,
          });
        }

        resolve({
          useremail,
          deviceIDsParsed: deviceIdArray,
          locationIDsParsed: locationIdArray,
          transData: transResults,
          userdata: userData,
          location: locationResults,
        });
      });
    } catch (error) {
      console.error("Error in getAdminData:", error);
      reject(error); // Reject with the error
    }
  });
}

async function getLocationData(customerId) {
  return new Promise((resolve, reject) => {
    const sqlLocation = "SELECT * FROM location_master WHERE customer_id = ?";
    db.query(sqlLocation, [customerId], (err, results) => {
      if (err) return reject(err);

      const locationData = results[0]; // assuming each customer_id has only one associated location data

      resolve(locationData);
    });
  });
}

async function getTransData(deviceIdArray) {
  return new Promise((resolve, reject) => {
    const placeholders = deviceIdArray.map(() => "?").join(",");
    const sqlTrans = `SELECT * FROM trans WHERE device_id IN (${placeholders})`;

    db.query(sqlTrans, deviceIdArray, (err, transResults) => {
      if (err) return reject(err);
      transResults.forEach((trans) => {
        if (trans.visitor_image_thumbnail) {
          let base64Image = Buffer.from(trans.visitor_image_thumbnail).toString(
            "base64"
          );
          trans.visitor_image_thumbnail_data_url =
            "data:image/jpeg;base64," + base64Image;
        }
      });

      resolve(transResults);
    });
  });
}

function ensureAuthenticated(req, res, next) {
  if (req.session && req.session.user) {
    return next();
  } else {
    res.set("Cache-Control", "no-store, no-cache, must-revalidate, private");
    return res.redirect("/");
  }
}

async function verifyCurrentPassword(email, currentPassword) {
  const user = await getUserFromDB(email);
  if (user.customer_password == currentPassword) {
    return true;
  } else {
    return false;
  }
}

async function changePassword(email, newPassword) {
  return new Promise((resolve, reject) => {
    const sql =
      "UPDATE customer_master SET customer_password = ? WHERE customer_login = ?";
    db.query(sql, [newPassword, email], (err, results) => {
      if (err) {
        console.error("An error occurred in changePassword:", err);
        return reject(err);
      }

      // Check if a row was affected (password updated successfully)
      if (results.affectedRows === 1) {
        resolve(true); // Password changed successfully
      } else {
        resolve(false); // Email not found or password not changed
      }
    });
  });
}

// API
app.get("/api/getUserData", ensureAuthenticated, async (req, res) => {
  try {
    if (!req.session.user) {
      return res.redirect("/");
    }

    const data = await getAdminData(req.session.user);
    if (!data.userdata) {
      return res.send(alertRedirect("No userData found with the email", "/"));
    }
    res.json(data);
  } catch (error) {
    console.error("Error:", error);
    res.status(500).send("Internal Server Error");
  }
});
