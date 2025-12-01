CREATE TABLE doctors1 (
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

INSERT INTO doctors (name, specialization, hospital_name, city, area, consultation_fee, latitude, longitude, email, password) VALUES
('Dr. Rahul Khanna','Oncologist','Smile Dental Studio Ahmedabad','Ahmedabad','Paldi',200,23.0225,72.5714,'rahul.khanna@smile.ahmedabad.com','rahulkhanna123'),
('Dr. Akshit Mehta','Neurologist','Bansal Hospital Ahmedabad','Ahmedabad','Navrangpura',500,23.0266,72.5763,'akshit.mehta@bansal.ahmedabad.com','akshitmehta123'),
('Dr. Aarav Sidhu','ENT Specialist','Aneja Children & Maternity Hospital Ahmedabad','Ahmedabad','Bodakdev',1000,23.0288,72.5336,'aarav.sidhu@aneja.ahmedabad.com','aaravsidhu123'),
('Dr. Harjinder Verma','Nephrologist','Smile Dental Studio Ahmedabad','Ahmedabad','Bodakdev',200,23.0281,72.5318,'harjinder.verma@smile.ahmedabad.com','harjinderverma123'),
('Dr. Harjinder Shah','Gynecologist','Smile Dental Studio Ahmedabad','Ahmedabad','Paldi',900,23.0220,72.5272,'harjinder.shah@smile.ahmedabad.com','harjindershah123'),
('Dr. Megha Chadha','Oncologist','Kapoor Multi‑Specialty Dental Care Ahmedabad','Ahmedabad','Navrangpura',900,23.0245,72.5715,'megha.chadha@kapoor.ahmedabad.com','meghachadha123'),
('Dr. Anil Shah','Dermatologist','Smile Dental Studio Ahmedabad','Ahmedabad','Satellite',500,23.0375,72.5302,'anil.shah@smile.ahmedabad.com','anilshah123'),
('Dr. Heeya Verma','Orthopedic','J.P. Nursing Home Ahmedabad','Ahmedabad','Navrangpura',200,23.0262,72.5731,'heeya.verma@jp.ahmedabad.com','heeyaverma123'),
('Dr. Rohan Chadha','Dentist','Jiwan Nursing Home Ahmedabad','Ahmedabad','Bodakdev',600,23.0347,72.5338,'rohan.chadha@jiwan.ahmedabad.com','rohanchadha123'),
('Dr. Akshit Singla','Dermatologist','Sidhu Clinic Ahmedabad','Ahmedabad','Bodakdev',400,23.0331,72.5356,'akshit.singla@sidhu.ahmedabad.com','akshitsingla123'),
('Dr. Manpreet Garg','Pulmonologist','Prime Physiotherapy Centre Ahmedabad','Ahmedabad','Vastrapur',900,23.0305,72.5201,'manpreet.garg@prime.ahmedabad.com','manpreetgarg123'),
('Dr. Munish Verma','Gynecologist','Gupta Children & General Hospital Ahmedabad','Ahmedabad','Bodakdev',900,23.0326,72.5360,'munish.verma@gupta.ahmedabad.com','munishverma123'),
('Dr. Harjinder Sidhu','Rheumatologist','Bansal Hospital Ahmedabad','Ahmedabad','Navrangpura',700,23.0281,72.5701,'harjinder.sidhu@bansal.ahmedabad.com','harjindersidhu123'),
('Dr. Heeya Verma','Pulmonologist','Maan Homoeopathic Clinic Ahmedabad','Ahmedabad','Paldi',700,23.0256,72.5732,'heeya.verma@maan.ahmedabad.com','heeyaverma123'),
('Dr. Heeya Gupta','Pulmonologist','Prime Physiotherapy Centre Ahmedabad','Ahmedabad','Bodakdev',500,23.0329,72.5385,'heeya.gupta@prime.ahmedabad.com','heeyagupta123'),
('Dr. Anil Garg','Nephrologist','Smile Dental Studio Ahmedabad','Ahmedabad','Maninagar',400,23.0279,72.5456,'anil.garg@smile.ahmedabad.com','anilgarg123'),
('Dr. Jaya Khanna','Cardiologist','Maan Homoeopathic Clinic Ahmedabad','Ahmedabad','Paldi',900,23.0272,72.5710,'jaya.khanna@maan.ahmedabad.com','jayakhanna123'),
('Dr. Sneha Desai','Cardiologist','Lotus Gyne & IVF Ahmedabad','Ahmedabad','Navrangpura',200,23.0258,72.5781,'sneha.desai@lotus.ahmedabad.com','snehadesai123'),
('Dr. Rahul Shah','Cardiologist','Prime Physiotherapy Centre Ahmedabad','Ahmedabad','Vastrapur',300,23.0300,72.5213,'rahul.shah@prime.ahmedabad.com','rahulshah123');
