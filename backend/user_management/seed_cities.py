"""
Creates the `city` table in the vendornest database and seeds it
with Indian cities and their corresponding states/UTs.
Run once: python seed_cities.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pymysql
from common.database import DATABASE_URL

# Parse host/port/user/password/db from DATABASE_URL
# mysql+pymysql://user:password@host:port/db
import re
m = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/(\w+)', DATABASE_URL)
USER, PASSWORD, HOST, PORT, DB = m.group(1), m.group(2), m.group(3), int(m.group(4)), m.group(5)

CITIES = [
    # Andhra Pradesh
    ("Visakhapatnam", "Andhra Pradesh"), ("Vijayawada", "Andhra Pradesh"),
    ("Guntur", "Andhra Pradesh"), ("Nellore", "Andhra Pradesh"),
    ("Kurnool", "Andhra Pradesh"), ("Rajahmundry", "Andhra Pradesh"),
    ("Kakinada", "Andhra Pradesh"), ("Tirupati", "Andhra Pradesh"),
    ("Kadapa", "Andhra Pradesh"), ("Anantapur", "Andhra Pradesh"),
    ("Amaravati", "Andhra Pradesh"),

    # Arunachal Pradesh
    ("Itanagar", "Arunachal Pradesh"), ("Naharlagun", "Arunachal Pradesh"),

    # Assam
    ("Guwahati", "Assam"), ("Silchar", "Assam"), ("Dibrugarh", "Assam"),
    ("Jorhat", "Assam"), ("Nagaon", "Assam"), ("Tinsukia", "Assam"),
    ("Tezpur", "Assam"), ("Dispur", "Assam"),

    # Bihar
    ("Patna", "Bihar"), ("Gaya", "Bihar"), ("Bhagalpur", "Bihar"),
    ("Muzaffarpur", "Bihar"), ("Purnia", "Bihar"), ("Darbhanga", "Bihar"),
    ("Arrah", "Bihar"), ("Begusarai", "Bihar"), ("Katihar", "Bihar"),
    ("Munger", "Bihar"), ("Chhapra", "Bihar"), ("Saharsa", "Bihar"),

    # Chhattisgarh
    ("Raipur", "Chhattisgarh"), ("Bhilai", "Chhattisgarh"),
    ("Durg", "Chhattisgarh"), ("Korba", "Chhattisgarh"),
    ("Bilaspur", "Chhattisgarh"), ("Rajnandgaon", "Chhattisgarh"),
    ("Jagdalpur", "Chhattisgarh"),

    # Goa
    ("Panaji", "Goa"), ("Margao", "Goa"),
    ("Vasco da Gama", "Goa"), ("Mapusa", "Goa"),

    # Gujarat
    ("Ahmedabad", "Gujarat"), ("Surat", "Gujarat"), ("Vadodara", "Gujarat"),
    ("Rajkot", "Gujarat"), ("Bhavnagar", "Gujarat"), ("Jamnagar", "Gujarat"),
    ("Gandhinagar", "Gujarat"), ("Junagadh", "Gujarat"), ("Anand", "Gujarat"),
    ("Nadiad", "Gujarat"), ("Morbi", "Gujarat"), ("Mehsana", "Gujarat"),
    ("Surendranagar", "Gujarat"), ("Bharuch", "Gujarat"), ("Navsari", "Gujarat"),
    ("Porbandar", "Gujarat"), ("Gandhidham", "Gujarat"),

    # Haryana
    ("Faridabad", "Haryana"), ("Gurugram", "Haryana"), ("Rohtak", "Haryana"),
    ("Hisar", "Haryana"), ("Panipat", "Haryana"), ("Karnal", "Haryana"),
    ("Yamunanagar", "Haryana"), ("Sonipat", "Haryana"), ("Ambala", "Haryana"),
    ("Bhiwani", "Haryana"), ("Sirsa", "Haryana"), ("Panchkula", "Haryana"),

    # Himachal Pradesh
    ("Shimla", "Himachal Pradesh"), ("Solan", "Himachal Pradesh"),
    ("Dharamsala", "Himachal Pradesh"), ("Mandi", "Himachal Pradesh"),
    ("Kullu", "Himachal Pradesh"), ("Baddi", "Himachal Pradesh"),
    ("Palampur", "Himachal Pradesh"),

    # Jharkhand
    ("Ranchi", "Jharkhand"), ("Jamshedpur", "Jharkhand"),
    ("Dhanbad", "Jharkhand"), ("Bokaro", "Jharkhand"),
    ("Deoghar", "Jharkhand"), ("Hazaribagh", "Jharkhand"),
    ("Giridih", "Jharkhand"), ("Ramgarh", "Jharkhand"),

    # Karnataka
    ("Bengaluru", "Karnataka"), ("Mysuru", "Karnataka"),
    ("Mangaluru", "Karnataka"), ("Hubballi", "Karnataka"),
    ("Dharwad", "Karnataka"), ("Belagavi", "Karnataka"),
    ("Davangere", "Karnataka"), ("Ballari", "Karnataka"),
    ("Vijayapura", "Karnataka"), ("Shivamogga", "Karnataka"),
    ("Tumakuru", "Karnataka"), ("Raichur", "Karnataka"),
    ("Kalaburagi", "Karnataka"), ("Hassan", "Karnataka"),
    ("Udupi", "Karnataka"),

    # Kerala
    ("Thiruvananthapuram", "Kerala"), ("Kochi", "Kerala"),
    ("Kozhikode", "Kerala"), ("Thrissur", "Kerala"),
    ("Kollam", "Kerala"), ("Kannur", "Kerala"),
    ("Alappuzha", "Kerala"), ("Palakkad", "Kerala"),
    ("Malappuram", "Kerala"), ("Kasaragod", "Kerala"),
    ("Kottayam", "Kerala"), ("Ernakulam", "Kerala"),

    # Madhya Pradesh
    ("Bhopal", "Madhya Pradesh"), ("Indore", "Madhya Pradesh"),
    ("Gwalior", "Madhya Pradesh"), ("Jabalpur", "Madhya Pradesh"),
    ("Ujjain", "Madhya Pradesh"), ("Sagar", "Madhya Pradesh"),
    ("Dewas", "Madhya Pradesh"), ("Satna", "Madhya Pradesh"),
    ("Ratlam", "Madhya Pradesh"), ("Rewa", "Madhya Pradesh"),
    ("Singrauli", "Madhya Pradesh"), ("Burhanpur", "Madhya Pradesh"),
    ("Khandwa", "Madhya Pradesh"), ("Bhind", "Madhya Pradesh"),
    ("Chhindwara", "Madhya Pradesh"), ("Morena", "Madhya Pradesh"),

    # Maharashtra
    ("Mumbai", "Maharashtra"), ("Pune", "Maharashtra"),
    ("Nagpur", "Maharashtra"), ("Thane", "Maharashtra"),
    ("Nashik", "Maharashtra"), ("Aurangabad", "Maharashtra"),
    ("Solapur", "Maharashtra"), ("Amravati", "Maharashtra"),
    ("Kolhapur", "Maharashtra"), ("Navi Mumbai", "Maharashtra"),
    ("Pimpri-Chinchwad", "Maharashtra"), ("Vasai-Virar", "Maharashtra"),
    ("Malegaon", "Maharashtra"), ("Jalgaon", "Maharashtra"),
    ("Ahmednagar", "Maharashtra"), ("Latur", "Maharashtra"),
    ("Dhule", "Maharashtra"), ("Sangli", "Maharashtra"),
    ("Akola", "Maharashtra"), ("Nanded", "Maharashtra"),

    # Manipur
    ("Imphal", "Manipur"), ("Thoubal", "Manipur"),

    # Meghalaya
    ("Shillong", "Meghalaya"), ("Tura", "Meghalaya"),

    # Mizoram
    ("Aizawl", "Mizoram"), ("Lunglei", "Mizoram"),

    # Nagaland
    ("Kohima", "Nagaland"), ("Dimapur", "Nagaland"),

    # Odisha
    ("Bhubaneswar", "Odisha"), ("Cuttack", "Odisha"),
    ("Rourkela", "Odisha"), ("Brahmapur", "Odisha"),
    ("Sambalpur", "Odisha"), ("Puri", "Odisha"),
    ("Balasore", "Odisha"), ("Baripada", "Odisha"),
    ("Bhadrak", "Odisha"),

    # Punjab
    ("Ludhiana", "Punjab"), ("Amritsar", "Punjab"),
    ("Jalandhar", "Punjab"), ("Patiala", "Punjab"),
    ("Bathinda", "Punjab"), ("Mohali", "Punjab"),
    ("Pathankot", "Punjab"), ("Hoshiarpur", "Punjab"),
    ("Batala", "Punjab"), ("Moga", "Punjab"),
    ("Firozpur", "Punjab"), ("Sangrur", "Punjab"),

    # Rajasthan
    ("Jaipur", "Rajasthan"), ("Jodhpur", "Rajasthan"),
    ("Kota", "Rajasthan"), ("Bikaner", "Rajasthan"),
    ("Ajmer", "Rajasthan"), ("Udaipur", "Rajasthan"),
    ("Bhilwara", "Rajasthan"), ("Bharatpur", "Rajasthan"),
    ("Alwar", "Rajasthan"), ("Barmer", "Rajasthan"),
    ("Sikar", "Rajasthan"), ("Pali", "Rajasthan"),
    ("Sri Ganganagar", "Rajasthan"), ("Tonk", "Rajasthan"),
    ("Chittorgarh", "Rajasthan"), ("Beawar", "Rajasthan"),

    # Sikkim
    ("Gangtok", "Sikkim"), ("Namchi", "Sikkim"),

    # Tamil Nadu
    ("Chennai", "Tamil Nadu"), ("Coimbatore", "Tamil Nadu"),
    ("Madurai", "Tamil Nadu"), ("Tiruchirappalli", "Tamil Nadu"),
    ("Salem", "Tamil Nadu"), ("Erode", "Tamil Nadu"),
    ("Tirunelveli", "Tamil Nadu"), ("Vellore", "Tamil Nadu"),
    ("Tirupur", "Tamil Nadu"), ("Thoothukudi", "Tamil Nadu"),
    ("Dindigul", "Tamil Nadu"), ("Thanjavur", "Tamil Nadu"),
    ("Ranipet", "Tamil Nadu"), ("Kanchipuram", "Tamil Nadu"),
    ("Nagercoil", "Tamil Nadu"), ("Cuddalore", "Tamil Nadu"),
    ("Karur", "Tamil Nadu"), ("Hosur", "Tamil Nadu"),

    # Telangana
    ("Hyderabad", "Telangana"), ("Warangal", "Telangana"),
    ("Nizamabad", "Telangana"), ("Karimnagar", "Telangana"),
    ("Khammam", "Telangana"), ("Ramagundam", "Telangana"),
    ("Mahbubnagar", "Telangana"), ("Nalgonda", "Telangana"),
    ("Adilabad", "Telangana"), ("Suryapet", "Telangana"),

    # Tripura
    ("Agartala", "Tripura"), ("Udaipur", "Tripura"),

    # Uttar Pradesh
    ("Lucknow", "Uttar Pradesh"), ("Kanpur", "Uttar Pradesh"),
    ("Agra", "Uttar Pradesh"), ("Varanasi", "Uttar Pradesh"),
    ("Prayagraj", "Uttar Pradesh"), ("Ghaziabad", "Uttar Pradesh"),
    ("Meerut", "Uttar Pradesh"), ("Bareilly", "Uttar Pradesh"),
    ("Aligarh", "Uttar Pradesh"), ("Moradabad", "Uttar Pradesh"),
    ("Gorakhpur", "Uttar Pradesh"), ("Saharanpur", "Uttar Pradesh"),
    ("Noida", "Uttar Pradesh"), ("Firozabad", "Uttar Pradesh"),
    ("Muzaffarnagar", "Uttar Pradesh"), ("Mathura", "Uttar Pradesh"),
    ("Jhansi", "Uttar Pradesh"), ("Ayodhya", "Uttar Pradesh"),
    ("Raebareli", "Uttar Pradesh"), ("Hapur", "Uttar Pradesh"),
    ("Rampur", "Uttar Pradesh"), ("Bulandshahr", "Uttar Pradesh"),
    ("Shahjahanpur", "Uttar Pradesh"), ("Lakhimpur", "Uttar Pradesh"),

    # Uttarakhand
    ("Dehradun", "Uttarakhand"), ("Haridwar", "Uttarakhand"),
    ("Roorkee", "Uttarakhand"), ("Rishikesh", "Uttarakhand"),
    ("Haldwani", "Uttarakhand"), ("Rudrapur", "Uttarakhand"),
    ("Kashipur", "Uttarakhand"), ("Nainital", "Uttarakhand"),

    # West Bengal
    ("Kolkata", "West Bengal"), ("Howrah", "West Bengal"),
    ("Durgapur", "West Bengal"), ("Asansol", "West Bengal"),
    ("Siliguri", "West Bengal"), ("Bardhaman", "West Bengal"),
    ("Malda", "West Bengal"), ("Baharampur", "West Bengal"),
    ("Kharagpur", "West Bengal"), ("Haldia", "West Bengal"),
    ("Jalpaiguri", "West Bengal"), ("Bankura", "West Bengal"),
    ("Darjeeling", "West Bengal"),

    # Union Territories
    ("New Delhi", "Delhi"), ("Delhi", "Delhi"),
    ("Dwarka", "Delhi"), ("Rohini", "Delhi"),

    ("Chandigarh", "Chandigarh"),

    ("Puducherry", "Puducherry"), ("Karaikal", "Puducherry"),

    ("Srinagar", "Jammu & Kashmir"), ("Jammu", "Jammu & Kashmir"),
    ("Anantnag", "Jammu & Kashmir"), ("Sopore", "Jammu & Kashmir"),
    ("Baramulla", "Jammu & Kashmir"),

    ("Leh", "Ladakh"), ("Kargil", "Ladakh"),

    ("Port Blair", "Andaman and Nicobar Islands"),

    ("Kavaratti", "Lakshadweep"),

    ("Daman", "Dadra and Nagar Haveli and Daman and Diu"),
    ("Diu", "Dadra and Nagar Haveli and Daman and Diu"),
    ("Silvassa", "Dadra and Nagar Haveli and Daman and Diu"),
]


def main():
    conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, db=DB)
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS city (
            id    INT AUTO_INCREMENT PRIMARY KEY,
            city  VARCHAR(100) NOT NULL,
            state VARCHAR(100) NOT NULL,
            INDEX idx_city  (city),
            INDEX idx_state (state)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("SELECT COUNT(*) FROM city")
    if cur.fetchone()[0] > 0:
        print("[INFO] city table already has data — skipping seed.")
        conn.close()
        return

    cur.executemany("INSERT INTO city (city, state) VALUES (%s, %s)", CITIES)
    conn.commit()
    print(f"[OK] city table created and seeded with {len(CITIES)} cities.")
    conn.close()


if __name__ == "__main__":
    main()
