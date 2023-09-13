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
    const sql = "SELECT * FROM customer_master WHERE customer_login = ?";
    db.query(sql, [useremail], async (err, results) => {
      if (err) return reject(err);

      const userData = results[0];
      console.log("Admin Data:", userData);

      // Get location data based on the customer_id
      const locationData = await getLocationData(userData.customer_id);
      if (!locationData) {
        return reject("No location data found for this customer ID");
      }

      const deviceIdArray = userData.device_id
        ? JSON.parse(userData.device_id)
        : [];

      if (deviceIdArray.length === 0) {
        return resolve({
          useremail,
          plainObject: [],
          transData: [],
          userdata: userData,
          location: locationData,
        });
      }

      const transResults = await getTransData(deviceIdArray);
      resolve({
        useremail,
        plainObject: deviceIdArray,
        transData: transResults,
        userdata: userData,
        location: locationData,
      });
    });
  });
}

async function getLocationData(customerId) {
  return new Promise((resolve, reject) => {
    const sqlLocation = "SELECT * FROM location_master WHERE customer_id = ?";
    db.query(sqlLocation, [customerId], (err, results) => {
      if (err) return reject(err);

      const locationData = results[0]; // assuming each customer_id has only one associated location data
      console.log("Location Data:", locationData); // Log the location data

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
