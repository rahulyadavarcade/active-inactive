import re
from main import SessionLocal, User

def seed():
    data = """
    HARSH JAISWAL <harshjaiswal.linuxbean@gmail.com>, Aayush Tamrakar <aayushtamrakar.stevesai@gmail.com>, Aditya Patel <adityapatel.stevesai@gmail.com>, Ammar Ahmed Ansari <ammarahmed.stevesai@gmail.com>, Anirudh Raykhere <anirudh.stevesai@gmail.com>, Anshul khandelwal <anshulkhandelwal.stevesai@gmail.com>, Ashutosh <ashutosh.stevesai@gmail.com>, Chetanya Gupta <chetanya.linuxbean@gmail.com>, Gourav Panchal <gourav.stevesai@gmail.com>, Harish Barod <harishbarod.stevesai@gmail.com>, "Harsh Jr." <harshjaiswal.stevesai@gmail.com>, himanshu <himanshuvishwakarma.stevesai@gmail.com>, Irfan Khan <irfan.linuxbean@gmail.com>, "kunal.stevesai" <kunal.stevesai@gmail.com>, Milind <milind.stevesai@gmail.com>, Nachiket Borse <nachiket.stevesailab@gmail.com>, Nikhil Tiwari <nikhil.stevesai@gmail.com>, Nilesh Nagar <nileshnagar.stevesai@gmail.com>, Rahul Parihar <rahulparihar.stevesai@gmail.com>, Rahul Singh <rahulsingh.stevesai@gmail.com>, Rahul Yadav <rahulyadavstevesai@gmail.com>, raj singh tomar <rajsingh.stevesai@gmail.com>, Rohit Mukati <rohit.stevesai@gmail.com>, sachin sisodiya <sachin.stevesai@gmail.com>, Yashwant Devda <yashwantdevda.stevesai@gmail.com>
    """
    
    # Simple regex to extract name and email
    pattern = r'(?:"?([^<"]+)"?\s+)?<([^>]+)>'
    matches = re.findall(pattern, data)
    
    db = SessionLocal()
    for name, email in matches:
        name = name.strip()
        email = email.strip()
        
        # Check if user already exists
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Adding user: {name} ({email})")
            user = User(
                email=email,
                username=name,
                status="inactive"
            )
            db.add(user)
        else:
            print(f"User {email} already exists.")
            
    try:
        db.commit()
    except Exception as e:
        print(f"Error during commit: {e}")
        db.rollback()
    finally:
        db.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed()
