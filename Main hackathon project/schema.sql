-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100),
    role ENUM('patient', 'doctor')
);

CREATE TABLE doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    specialization VARCHAR(100),
    hospital_name VARCHAR(150),
    city VARCHAR(100),
    area VARCHAR(100),
    consultation_fee INT,
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    email VARCHAR(150),
    password VARCHAR(100)
);
    

-- Appointments table
CREATE TABLE appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    doctor_id INT,
    date DATE,
    time TIME,
    status ENUM('booked','completed','cancelled'),
    FOREIGN KEY (patient_id) REFERENCES users(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

-- Remedies table (for Ayurveda chatbot)
CREATE TABLE remedies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symptom VARCHAR(255) NOT NULL,
    remedy TEXT NOT NULL
);


-- Chat History Table
CREATE TABLE chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

