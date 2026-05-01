from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect as sa_inspect, text
from routers import auth_router, users_router, vendors_router
from product_management import models as product_models
from product_management.router import router as products_router
from database import engine
import models as main_models

product_models.Base.metadata.create_all(bind=engine)
main_models.Base.metadata.create_all(bind=engine)

# Migrate products table: normalise to single unit VARCHAR(50)
with engine.begin() as _conn:
    try:
        _inspector = sa_inspect(engine)
        if "products" in _inspector.get_table_names():
            _cols = {c["name"] for c in _inspector.get_columns("products")}
            if "type" in _cols:
                _conn.execute(text("ALTER TABLE products DROP COLUMN type"))
            # Revert units JSON → unit VARCHAR(50)
            if "units" in _cols and "unit" not in _cols:
                _conn.execute(text("ALTER TABLE products ADD COLUMN unit VARCHAR(50) NOT NULL DEFAULT ''"))
                _conn.execute(text(
                    "UPDATE products SET unit = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(units, '$[0]')), '')"
                ))
                _conn.execute(text("ALTER TABLE products DROP COLUMN units"))
    except Exception as _e:
        print(f"[migration] products: {_e}")

# Migrate vendor_profiles table: add pincode column
with engine.begin() as _conn:
    try:
        _inspector = sa_inspect(engine)
        if "vendor_profiles" in _inspector.get_table_names():
            _cols = {c["name"] for c in _inspector.get_columns("vendor_profiles")}
            if "pincode" not in _cols:
                _conn.execute(text("ALTER TABLE vendor_profiles ADD COLUMN pincode VARCHAR(10)"))
    except Exception as _e:
        print(f"[migration] vendor_profiles: {_e}")

# Seed city table
_CITIES = [
    ("Visakhapatnam", "Andhra Pradesh"), ("Vijayawada", "Andhra Pradesh"),
    ("Guntur", "Andhra Pradesh"), ("Nellore", "Andhra Pradesh"),
    ("Kurnool", "Andhra Pradesh"), ("Rajahmundry", "Andhra Pradesh"),
    ("Kakinada", "Andhra Pradesh"), ("Tirupati", "Andhra Pradesh"),
    ("Kadapa", "Andhra Pradesh"), ("Anantapur", "Andhra Pradesh"),
    ("Amaravati", "Andhra Pradesh"),
    ("Itanagar", "Arunachal Pradesh"), ("Naharlagun", "Arunachal Pradesh"),
    ("Guwahati", "Assam"), ("Silchar", "Assam"), ("Dibrugarh", "Assam"),
    ("Jorhat", "Assam"), ("Nagaon", "Assam"), ("Tinsukia", "Assam"),
    ("Tezpur", "Assam"), ("Dispur", "Assam"),
    ("Patna", "Bihar"), ("Gaya", "Bihar"), ("Bhagalpur", "Bihar"),
    ("Muzaffarpur", "Bihar"), ("Purnia", "Bihar"), ("Darbhanga", "Bihar"),
    ("Arrah", "Bihar"), ("Begusarai", "Bihar"), ("Katihar", "Bihar"),
    ("Munger", "Bihar"), ("Chhapra", "Bihar"), ("Saharsa", "Bihar"),
    ("Raipur", "Chhattisgarh"), ("Bhilai", "Chhattisgarh"),
    ("Durg", "Chhattisgarh"), ("Korba", "Chhattisgarh"),
    ("Bilaspur", "Chhattisgarh"), ("Rajnandgaon", "Chhattisgarh"),
    ("Jagdalpur", "Chhattisgarh"),
    ("Panaji", "Goa"), ("Margao", "Goa"), ("Vasco da Gama", "Goa"), ("Mapusa", "Goa"),
    ("Ahmedabad", "Gujarat"), ("Surat", "Gujarat"), ("Vadodara", "Gujarat"),
    ("Rajkot", "Gujarat"), ("Bhavnagar", "Gujarat"), ("Jamnagar", "Gujarat"),
    ("Gandhinagar", "Gujarat"), ("Junagadh", "Gujarat"), ("Anand", "Gujarat"),
    ("Nadiad", "Gujarat"), ("Morbi", "Gujarat"), ("Mehsana", "Gujarat"),
    ("Surendranagar", "Gujarat"), ("Bharuch", "Gujarat"), ("Navsari", "Gujarat"),
    ("Porbandar", "Gujarat"), ("Gandhidham", "Gujarat"),
    ("Faridabad", "Haryana"), ("Gurugram", "Haryana"), ("Rohtak", "Haryana"),
    ("Hisar", "Haryana"), ("Panipat", "Haryana"), ("Karnal", "Haryana"),
    ("Yamunanagar", "Haryana"), ("Sonipat", "Haryana"), ("Ambala", "Haryana"),
    ("Bhiwani", "Haryana"), ("Sirsa", "Haryana"), ("Panchkula", "Haryana"),
    ("Shimla", "Himachal Pradesh"), ("Solan", "Himachal Pradesh"),
    ("Dharamsala", "Himachal Pradesh"), ("Mandi", "Himachal Pradesh"),
    ("Kullu", "Himachal Pradesh"), ("Baddi", "Himachal Pradesh"),
    ("Palampur", "Himachal Pradesh"),
    ("Ranchi", "Jharkhand"), ("Jamshedpur", "Jharkhand"),
    ("Dhanbad", "Jharkhand"), ("Bokaro", "Jharkhand"),
    ("Deoghar", "Jharkhand"), ("Hazaribagh", "Jharkhand"),
    ("Giridih", "Jharkhand"), ("Ramgarh", "Jharkhand"),
    ("Bengaluru", "Karnataka"), ("Mysuru", "Karnataka"),
    ("Mangaluru", "Karnataka"), ("Hubballi", "Karnataka"),
    ("Dharwad", "Karnataka"), ("Belagavi", "Karnataka"),
    ("Davangere", "Karnataka"), ("Ballari", "Karnataka"),
    ("Vijayapura", "Karnataka"), ("Shivamogga", "Karnataka"),
    ("Tumakuru", "Karnataka"), ("Raichur", "Karnataka"),
    ("Kalaburagi", "Karnataka"), ("Hassan", "Karnataka"), ("Udupi", "Karnataka"),
    ("Thiruvananthapuram", "Kerala"), ("Kochi", "Kerala"),
    ("Kozhikode", "Kerala"), ("Thrissur", "Kerala"),
    ("Kollam", "Kerala"), ("Kannur", "Kerala"),
    ("Alappuzha", "Kerala"), ("Palakkad", "Kerala"),
    ("Malappuram", "Kerala"), ("Kasaragod", "Kerala"),
    ("Kottayam", "Kerala"), ("Ernakulam", "Kerala"),
    ("Bhopal", "Madhya Pradesh"), ("Indore", "Madhya Pradesh"),
    ("Gwalior", "Madhya Pradesh"), ("Jabalpur", "Madhya Pradesh"),
    ("Ujjain", "Madhya Pradesh"), ("Sagar", "Madhya Pradesh"),
    ("Dewas", "Madhya Pradesh"), ("Satna", "Madhya Pradesh"),
    ("Ratlam", "Madhya Pradesh"), ("Rewa", "Madhya Pradesh"),
    ("Singrauli", "Madhya Pradesh"), ("Burhanpur", "Madhya Pradesh"),
    ("Khandwa", "Madhya Pradesh"), ("Bhind", "Madhya Pradesh"),
    ("Chhindwara", "Madhya Pradesh"), ("Morena", "Madhya Pradesh"),
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
    ("Imphal", "Manipur"), ("Thoubal", "Manipur"),
    ("Shillong", "Meghalaya"), ("Tura", "Meghalaya"),
    ("Aizawl", "Mizoram"), ("Lunglei", "Mizoram"),
    ("Kohima", "Nagaland"), ("Dimapur", "Nagaland"),
    ("Bhubaneswar", "Odisha"), ("Cuttack", "Odisha"),
    ("Rourkela", "Odisha"), ("Brahmapur", "Odisha"),
    ("Sambalpur", "Odisha"), ("Puri", "Odisha"),
    ("Balasore", "Odisha"), ("Baripada", "Odisha"), ("Bhadrak", "Odisha"),
    ("Ludhiana", "Punjab"), ("Amritsar", "Punjab"),
    ("Jalandhar", "Punjab"), ("Patiala", "Punjab"),
    ("Bathinda", "Punjab"), ("Mohali", "Punjab"),
    ("Pathankot", "Punjab"), ("Hoshiarpur", "Punjab"),
    ("Batala", "Punjab"), ("Moga", "Punjab"),
    ("Firozpur", "Punjab"), ("Sangrur", "Punjab"),
    ("Jaipur", "Rajasthan"), ("Jodhpur", "Rajasthan"),
    ("Kota", "Rajasthan"), ("Bikaner", "Rajasthan"),
    ("Ajmer", "Rajasthan"), ("Udaipur", "Rajasthan"),
    ("Bhilwara", "Rajasthan"), ("Bharatpur", "Rajasthan"),
    ("Alwar", "Rajasthan"), ("Barmer", "Rajasthan"),
    ("Sikar", "Rajasthan"), ("Pali", "Rajasthan"),
    ("Sri Ganganagar", "Rajasthan"), ("Tonk", "Rajasthan"),
    ("Chittorgarh", "Rajasthan"), ("Beawar", "Rajasthan"),
    ("Gangtok", "Sikkim"), ("Namchi", "Sikkim"),
    ("Chennai", "Tamil Nadu"), ("Coimbatore", "Tamil Nadu"),
    ("Madurai", "Tamil Nadu"), ("Tiruchirappalli", "Tamil Nadu"),
    ("Salem", "Tamil Nadu"), ("Erode", "Tamil Nadu"),
    ("Tirunelveli", "Tamil Nadu"), ("Vellore", "Tamil Nadu"),
    ("Tirupur", "Tamil Nadu"), ("Thoothukudi", "Tamil Nadu"),
    ("Dindigul", "Tamil Nadu"), ("Thanjavur", "Tamil Nadu"),
    ("Ranipet", "Tamil Nadu"), ("Kanchipuram", "Tamil Nadu"),
    ("Nagercoil", "Tamil Nadu"), ("Cuddalore", "Tamil Nadu"),
    ("Karur", "Tamil Nadu"), ("Hosur", "Tamil Nadu"),
    ("Hyderabad", "Telangana"), ("Warangal", "Telangana"),
    ("Nizamabad", "Telangana"), ("Karimnagar", "Telangana"),
    ("Khammam", "Telangana"), ("Ramagundam", "Telangana"),
    ("Mahbubnagar", "Telangana"), ("Nalgonda", "Telangana"),
    ("Adilabad", "Telangana"), ("Suryapet", "Telangana"),
    ("Agartala", "Tripura"), ("Udaipur", "Tripura"),
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
    ("Dehradun", "Uttarakhand"), ("Haridwar", "Uttarakhand"),
    ("Roorkee", "Uttarakhand"), ("Rishikesh", "Uttarakhand"),
    ("Haldwani", "Uttarakhand"), ("Rudrapur", "Uttarakhand"),
    ("Kashipur", "Uttarakhand"), ("Nainital", "Uttarakhand"),
    ("Kolkata", "West Bengal"), ("Howrah", "West Bengal"),
    ("Durgapur", "West Bengal"), ("Asansol", "West Bengal"),
    ("Siliguri", "West Bengal"), ("Bardhaman", "West Bengal"),
    ("Malda", "West Bengal"), ("Baharampur", "West Bengal"),
    ("Kharagpur", "West Bengal"), ("Haldia", "West Bengal"),
    ("Jalpaiguri", "West Bengal"), ("Bankura", "West Bengal"),
    ("Darjeeling", "West Bengal"),
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

with engine.begin() as _conn:
    try:
        _count = _conn.execute(text("SELECT COUNT(*) FROM city")).scalar()
        if _count == 0:
            _conn.execute(
                text("INSERT INTO city (city, state) VALUES (:city, :state)"),
                [{"city": c, "state": s} for c, s in _CITIES],
            )
            print(f"[seed] city table seeded with {len(_CITIES)} cities.")
    except Exception as _e:
        print(f"[seed] city: {_e}")

app = FastAPI(
    title       = "VendorNest API",
    version     = "1.0.0",
    description = "Vendor Management Platform — HLD v1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(vendors_router.router)
app.include_router(products_router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": "VendorNest API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
