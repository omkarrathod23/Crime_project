/**
 * MongoDB Seed Script: Maharashtra Police Departments
 * 
 * This script populates the 'departments' collection with major commissionerates, 
 * district headquarters, and key police stations across Maharashtra, India.
 * 
 * Usage: 
 * 1. Open MongoDB Compass or a terminal with mongosh.
 * 2. Select your database: use crime_management_db (or your database name).
 * 3. Copy and paste this script to run.
 */

const departments = [
  // --- Commissionerates (Major Cities) ---
  { name: "Mumbai Police Commissionerate", city: "Mumbai", district: "Mumbai City", type: "Commissionerate", status: "Active", load: 0 },
  { name: "Pune City Police Commissionerate", city: "Pune", district: "Pune", type: "Commissionerate", status: "Active", load: 0 },
  { name: "Nagpur City Police Commissionerate", city: "Nagpur", district: "Nagpur", type: "Commissionerate", status: "Active", load: 0 },
  { name: "Thane City Police Commissionerate", city: "Thane", district: "Thane", type: "Commissionerate", status: "Active", load: 0 },
  { name: "Navi Mumbai Police Commissionerate", city: "Navi Mumbai", district: "Thane", type: "Commissionerate", status: "Active", load: 0 },
  { name: "Nashik City Police Commissionerate", city: "Nashik", district: "Nashik", type: "Commissionerate", status: "Active", load: 0 },
  { name: "Aurangabad City Police Commissionerate", city: "Aurangabad", district: "Aurangabad", type: "Commissionerate", status: "Active", load: 0 },
  { name: "Solapur City Police Commissionerate", city: "Solapur", district: "Solapur", type: "Commissionerate", status: "Active", load: 0 },
  { name: "Amravati City Police Commissionerate", city: "Amravati", district: "Amravati", type: "Commissionerate", status: "Active", load: 0 },
  { name: "Mira-Bhayandar Vasai-Virar Commissionerate", city: "Mira Road", district: "Thane/Palghar", type: "Commissionerate", status: "Active", load: 0 },
  { name: "Pimpri-Chinchwad Police Commissionerate", city: "Pimpri", district: "Pune", type: "Commissionerate", status: "Active", load: 0 },

  // --- District Police Departments ---
  { name: "Raigad District Police", city: "Alibaug", district: "Raigad", type: "District", status: "Active", load: 0 },
  { name: "Kolhapur District Police", city: "Kolhapur", district: "Kolhapur", type: "District", status: "Active", load: 0 },
  { name: "Satara District Police", city: "Satara", district: "Satara", type: "District", status: "Active", load: 0 },
  { name: "Ahmednagar District Police", city: "Ahmednagar", district: "Ahmednagar", type: "District", status: "Active", load: 0 },
  { name: "Sangli District Police", city: "Sangli", district: "Sangli", type: "District", status: "Active", load: 0 },
  { name: "Ratnagiri District Police", city: "Ratnagiri", district: "Ratnagiri", type: "District", status: "Active", load: 0 },
  { name: "Sindhudurg District Police", city: "Oros", district: "Sindhudurg", type: "District", status: "Active", load: 0 },
  { name: "Jalgaon District Police", city: "Jalgaon", district: "Jalgaon", type: "District", status: "Active", load: 0 },
  { name: "Dhule District Police", city: "Dhule", district: "Dhule", type: "District", status: "Active", load: 0 },
  { name: "Nandurbar District Police", city: "Nandurbar", district: "Nandurbar", type: "District", status: "Active", load: 0 },
  { name: "Wardha District Police", city: "Wardha", district: "Wardha", type: "District", status: "Active", load: 0 },
  { name: "Bhandara District Police", city: "Bhandara", district: "Bhandara", type: "District", status: "Active", load: 0 },
  { name: "Gondia District Police", city: "Gondia", district: "Gondia", type: "District", status: "Active", load: 0 },
  { name: "Chandrapur District Police", city: "Chandrapur", district: "Chandrapur", type: "District", status: "Active", load: 0 },
  { name: "Gadchiroli District Police", city: "Gadchiroli", district: "Gadchiroli", type: "District", status: "Active", load: 0 },
  { name: "Buldhana District Police", city: "Buldhana", district: "Buldhana", type: "District", status: "Active", load: 0 },
  { name: "Akola District Police", city: "Akola", district: "Akola", type: "District", status: "Active", load: 0 },
  { name: "Washim District Police", city: "Washim", district: "Washim", type: "District", status: "Active", load: 0 },
  { name: "Yavatmal District Police", city: "Yavatmal", district: "Yavatmal", type: "District", status: "Active", load: 0 },
  { name: "Nanded District Police", city: "Nanded", district: "Nanded", type: "District", status: "Active", load: 0 },
  { name: "Parbhani District Police", city: "Parbhani", district: "Parbhani", type: "District", status: "Active", load: 0 },

  // --- Important Police Stations ---
  { name: "Dadar Police Station", city: "Mumbai", district: "Mumbai City", type: "Station", status: "Active", load: 0 },
  { name: "Andheri Police Station", city: "Mumbai", district: "Mumbai Suburban", type: "Station", status: "Active", load: 0 },
  { name: "Colaba Police Station", city: "Mumbai", district: "Mumbai City", type: "Station", status: "Active", load: 0 },
  { name: "Borivali Police Station", city: "Mumbai", district: "Mumbai Suburban", type: "Station", status: "Active", load: 0 },
  { name: "Hinjawadi Police Station", city: "Pune", district: "Pune", type: "Station", status: "Active", load: 0 },
  { name: "Kothrud Police Station", city: "Pune", district: "Pune", type: "Station", status: "Active", load: 0 },
  { name: "Hadapsar Police Station", city: "Pune", district: "Pune", type: "Station", status: "Active", load: 0 },
  { name: "Panvel City Police Station", city: "Panvel", district: "Raigad", type: "Station", status: "Active", load: 0 },
  { name: "Vashi Police Station", city: "Navi Mumbai", district: "Thane", type: "Station", status: "Active", load: 0 },
  { name: "Belapur Police Station", city: "Navi Mumbai", district: "Thane", type: "Station", status: "Active", load: 0 },
  { name: "Naupada Police Station", city: "Thane", district: "Thane", type: "Station", status: "Active", load: 0 },
  { name: "Kalwa Police Station", city: "Thane", district: "Thane", type: "Station", status: "Active", load: 0 },
  { name: "Sarkarwada Police Station", city: "Nashik", district: "Nashik", type: "Station", status: "Active", load: 0 },
  { name: "Pachpaoli Police Station", city: "Nagpur", district: "Nagpur", type: "Station", status: "Active", load: 0 },
  { name: "Laxmipuri Police Station", city: "Kolhapur", district: "Kolhapur", type: "Station", status: "Active", load: 0 },
  { name: "Shahupuri Police Station", city: "Kolhapur", district: "Kolhapur", type: "Station", status: "Active", load: 0 },
  { name: "Latur City Police Station", city: "Latur", district: "Latur", type: "Station", status: "Active", load: 0 },
  { name: "Beed City Police Station", city: "Beed", district: "Beed", type: "Station", status: "Active", load: 0 },
  { name: "Jalna City Police Station", city: "Jalna", district: "Jalna", type: "Station", status: "Active", load: 0 },
  { name: "Osmanabad City Police Station", city: "Osmanabad", district: "Osmanabad", type: "Station", status: "Active", load: 0 }
];

// Clean operation: db.departments.deleteMany({}); // Uncomment if you want to reset the collection first

db.departments.insertMany(departments);

print("Successfully seeded " + departments.length + " Maharashtra Police Departments.");
