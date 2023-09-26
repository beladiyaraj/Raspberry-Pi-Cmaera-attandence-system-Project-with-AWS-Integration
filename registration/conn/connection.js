const mysql = require("mysql");

const db = mysql.createConnection({
  host: "gatex.cubboxnpfgtq.ap-south-1.rds.amazonaws.com",
  user: "admin",
  password: "kaizen112",
  database: "gatex_trans",
});

db.connect((err) => {
  if (err) throw err;
  console.log("Connection successful To RDS server");
});

module.exports = db;